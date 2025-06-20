import os
import re
import json
import time # Imported the time module
import pandas as pd
import google.generativeai as genai

class ComplaintExtractor:
    """A class to extract clinical complaints from medical notes in batches using an LLM."""
    def __init__(self, model, batch_size=50, delay_between_batches=5):
    # def __init__(self, model, batch_size=50, delay_between_batches=10):
        self.model = model
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches # Store the delay
        # self.base_prompt = """
        # You are an expert clinical NLP assistant. Your task is to perform a comprehensive review of a medical note and extract ALL distinct clinical items, including acute problems, chronic conditions, and relevant behavioral factors.

        # To ensure accuracy, follow this two-step process:
        # 1.  **Internal Checklist:** First, read the entire note and create a mental checklist of every single codable issue (e.g., "Acute Chest Pain," "History of HTN," "Medication Non-compliance," "Smoking History").
        # 2.  **JSON Formatting:** Second, for each item on your internal checklist, create a separate JSON object with the required details.

        # **Crucial Rule:** Do not let a single, severe complaint cause you to overlook the patient's chronic history or other secondary issues. Every distinct item must be extracted.

        # For each complaint, provide these details in a JSON array format:
        # 1.  `note_id`: The original document ID.
        # 2.  `patient_sex`: The gender of the patient.
        # 3.  `chief_complaint`: A concise summary phrase for the isolated clinical issue.
        # 4.  `supporting_evidence`: The specific phrase from the note that supports this single issue.
        # 5.  `icd_codes`: A list of the best relevant ICD-10 codes.

        # Do not add explanations outside of the JSON structure.

        # ---
        # Here are the medical notes to process:
        # """

        ### Currently Working Prompt ################################################
        self.base_prompt = """
        You are an expert clinical NLP assistant. Your task is to perform a comprehensive review of a medical note and extract All clinical items, including acute problems, chronic conditions, and relevant behavioral factors.

        To ensure accuracy, follow this two-step process:
        1.  **Internal Checklist:** First, read the entire note and create a mental checklist of every single codable issue (e.g., "Acute Chest Pain," "History of HTN," "Medication Non-compliance," "Smoking History").
        2.  **JSON Formatting:** Second, for each item on your internal checklist, create a separate JSON object with the required details.

        **Crucial Rule:** Do not let a single, severe complaint cause you to overlook the patient's chronic history or other secondary issues. Every distinct item must be extracted.

        **Important:** Do not miss any of the given complaints

        For each complaint, provide these details in a JSON array format:
        1.  `note_id`: The original document ID.
        2.  `patient_sex`: The gender of the patient.
        3.  `chief_complaint`: A concise summary phrase for the isolated clinical issue.
        4.  `supporting_evidence`: The specific phrase from the note that supports this single issue.

        Do not add explanations outside of the JSON structure.
        
        **Now process these medical notes:**
        """

    def extract(self, df_notes: pd.DataFrame) -> pd.DataFrame:
        final_dfs = []
        error_log_dir = "llm_error_logs"
        os.makedirs(error_log_dir, exist_ok=True)

        for start in range(0, len(df_notes), self.batch_size):
            end = min(start + self.batch_size, len(df_notes))
            df_batch = df_notes.iloc[start:end]

            # Build the prompt for the current batch correctly.
            notes_for_prompt = ""
            for _, row in df_batch.iterrows():
                notes_for_prompt += f"\n---\nNote ID: {row['Document ID']}\nNote Text: \"\"\"{row['medical_record_text']}\"\"\"\n"
            
            prompt = self.base_prompt + notes_for_prompt
            
            json_text = ""
            try:
                print(f"✅ Processing batch {start//self.batch_size + 1} (notes {start+1}-{end})...")
                response = self.model.generate_content(prompt)
                json_text = response.text.strip()
                
                # Regex to find JSON within markdown ```json ... ```
                match = re.search(r"``````", json_text, re.DOTALL)
                
                if match:
                    cleaned_json_str = match.group(1)
                else: # Fallback for when markdown block is missing
                    start_index = json_text.find('[')
                    end_index = json_text.rfind(']')
                    if start_index != -1 and end_index != -1:
                        cleaned_json_str = json_text[start_index : end_index + 1]
                    else:
                        cleaned_json_str = ""

                if not cleaned_json_str:
                    raise json.JSONDecodeError("No valid JSON array found in the model's response.", json_text, 0)

                data = json.loads(cleaned_json_str)
                df = pd.DataFrame(data)
                final_dfs.append(df)

            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error in batch {start//self.batch_size + 1}: {e}")
                error_file_path = os.path.join(error_log_dir, f"error_batch_{start+1}-{end}_malformed.txt")
                with open(error_file_path, "w", encoding="utf-8") as f: f.write(json_text)
                print(f"   Faulty LLM output saved to '{error_file_path}' for review.")
                continue
            
            except Exception as e:
                print(f"❌ An unexpected error occurred in batch {start//self.batch_size + 1}: {e}")
                continue
            
            # --- TIME DELAY ADDED HERE ---
            # If this is not the last batch, pause before processing the next one.
            if end < len(df_notes):
                print(f"   Waiting {self.delay_between_batches} seconds to respect API rate limit...")
                time.sleep(self.delay_between_batches)
        
        if final_dfs:
            return pd.concat(final_dfs, ignore_index=True)
        else:
            return pd.DataFrame()

def run_extracting(input_path: str, output_path: str, num_to_process: int, batch_size: int, delay_between_batches: int = 5):
    """The main logic function for Stage 1, callable by other scripts."""
    try:
        genai.configure(api_key="AIzaSyAGcLSC7CrmPCN8cfPnBM6doX0jbvcZrII") # type: ignore
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    try:
        df_notes = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"❌ Error: Input file not found at '{input_path}'")
        return

    print(f"Loaded {len(df_notes)} notes. Processing the first {num_to_process}...")
    df_to_process = df_notes.head(num_to_process)
    
    print(f"\nExtracting using LLM with a batch size of {batch_size}...\n")
    extractor = ComplaintExtractor(model=model, batch_size=batch_size, delay_between_batches=delay_between_batches)
    extracted_df = extractor.extract(df_to_process)
    
    if extracted_df is not None and not extracted_df.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        extracted_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n🎉 Success! Final dataset saved to '{output_path}' with shape: {extracted_df.shape}")
        print("\n--- Sample of Extracted Data ---")
        print(extracted_df.head())
    else:
        print("\n❌ No data was extracted from any of the notes.")

# def deduplicate_extracted_complaints(input_path: str, output_path: str):
#     """
#     Removes duplicate complaints from the extracted complaints CSV.
#     Keeps only unique rows based on 'chief_complaint' column.
#     """
#     print("\n--- Starting Deduplication of Extracted Complaints ---")
#     try:
#         df = pd.read_csv(input_path)
#         original_row_count = len(df)
#         print(f"Loaded {original_row_count} rows from '{input_path}'.")

#         # Check if 'chief_complaint' column exists
#         if 'chief_complaint' not in df.columns:
#             print("❌ Error: 'chief_complaint' column not found for deduplication.")
#             return

#         # Normalize chief_complaint for deduplication
#         df['chief_complaint'] = df['chief_complaint'].str.strip().str.lower()
#         dedup_df = df.drop_duplicates(subset=['chief_complaint'], keep='first')
#         final_row_count = len(dedup_df)

#         print(f"Removed {original_row_count - final_row_count} duplicate rows.")
#         print(f"Found {final_row_count} unique complaints.")

#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
#         dedup_df.to_csv(output_path, index=False, encoding='utf-8')
#         print(f"\n🎉 Deduplicated complaints saved to '{output_path}'.")
#         return output_path

def deduplicate_extracted_complaints(input_path: str, output_path: str):
    """
    Removes duplicate complaints from the extracted complaints CSV.
    Keeps only unique rows based on 'chief_complaint' column.
    Returns the output path if successful, None otherwise.
    """
    print("\n--- Starting Deduplication of Extracted Complaints ---")
    try:
        df = pd.read_csv(input_path)
        if 'chief_complaint' not in df.columns:
            print("❌ Error: 'chief_complaint' column not found for deduplication.")
            return None

        original_row_count = len(df)
        df['chief_complaint'] = df['chief_complaint'].str.strip().str.lower()
        dedup_df = df.drop_duplicates(subset=['chief_complaint'], keep='first')
        final_row_count = len(dedup_df)

        print(f"Removed {original_row_count - final_row_count} duplicate rows.")
        print(f"Found {final_row_count} unique complaints.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        dedup_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n🎉 Deduplicated complaints saved to '{output_path}'.")
        return output_path

    except FileNotFoundError:
        print(f"❌ Error: Input file not found at '{input_path}'. Please check the path.")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred during deduplication: {e}")
        return None