# # # stage4_enhancer.py
# # import pandas as pd
# # import ast
# # import os
# # import json
# # import re
# # import time
# # import google.generativeai as genai

# # # --- Substage 4.1: The LLM Generator Class ---
# # class Stage5_LLMGenerator:
# #     """Uses an LLM to generate candidate codes based on normalized text and evidence."""
# #     def __init__(self, model):
# #         self.model = model
# #         self.prompt_template = """
# #         You are a clinical investigator. Your task is to analyze the provided clinical text and
# #         generate a list of 2-3 relevant ICD-10 codes.

# #         **Crucial Instruction:** Do not just code for the mentioned symptom. Analyze the full context
# #         for clues (like medications or patient history) that point to a more specific **underlying diagnosis**.
# #         If such a diagnosis is likely, include its code.

# #         **Example:**
# #         - **Context:** "wheezing + tight chest, used inhaler 2x"
# #         - **Rewritten Complaint:** "Wheezing and chest tightness"
# #         - **Your Inferred Codes:** You should return codes for Asthma (e.g., "J45.909") in addition
# #         to the symptom code for Wheezing (e.g., "R06.2"), as "inhaler" strongly implies asthma.

# #         Return your response as a single, raw JSON array of strings.
# #         ---
# #         **Supporting Evidence:**
# #         "{context}"

# #         **Rewritten Complaint Text:**
# #         "{rewritten_complaint}"
# #         ---

# #         JSON Array Response:
# #         """

# #     def generate_codes(self, rewritten_complaint: str, context: str) -> list[str]:
# #         # This function's logic is fine, but it needs the right input.
# #         prompt = self.prompt_template.format(
# #             context=context,
# #             rewritten_complaint=rewritten_complaint # Use the rewritten complaint
# #         )
# #         # ... (rest of the try/except block)
# #         try:
# #             response = self.model.generate_content(prompt)
# #             json_str = response.text.strip()
# #             match = re.search(r'\[.*\]', json_str, re.DOTALL)
# #             if not match: return []
# #             parsed_json = json.loads(match.group(0))
# #             return [str(code) for code in parsed_json] if isinstance(parsed_json, list) else []
# #         except Exception as e:
# #             print(f"   ⚠️ LLM Error during Stage 5 generation: {e}")
# #             return []

# # # --- Main Logic Function Updated for 6-Stage Pipeline ---
# # def run_candidate_enhancement(stage1_path: str, stage4_path: str, output_path: str, batch_size: int):
# #     print("\n--- Starting Stage 5: Candidate Enhancement & Consolidation ---\n")
# #     try:
# #         genai.configure(api_key="AIzaSyAEI45NC4nP8cKLMdl8O8h3A8DH7Wnsrmc") # type: ignore
# #         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
# #     except Exception as e:
# #         print(f"❌ Error configuring Gemini API: {e}"); return

# #     try:
# #         print("Loading data from Stage 1 and Stage 4...")
# #         df_stage1 = pd.read_csv(stage1_path)
# #         # --- FIX: Load from the correct stage output ---
# #         df_stage4 = pd.read_csv(stage4_path)
        
# #         # --- FIX: Merge the correct DataFrames ---
# #         # We need columns from both, so a merge is appropriate.
# #         # df_merged = pd.merge(df_stage1, df_stage4, on='chief_complaint', how='left')
# #         df_merged = pd.merge(df_stage1, df_stage4, left_index=True, right_index=True, how='left')
# #         print("✅ Data merged successfully.")

# #         print("\n--- Running Substage 5.1: LLM Candidate Generation ---")
# #         llm_generator = Stage5_LLMGenerator(llm_model)
# #         new_llm_codes = []
# #         for index, row in df_merged.iterrows():
# #             print(f"   Processing row {index + 1}/{len(df_merged)}...") # type: ignore
            
# #             # --- FIX: Use the 'rewritten_complaint' column for the prompt ---
# #             codes = llm_generator.generate_codes(
# #                 rewritten_complaint=row['rewritten_complaint'],
# #                 context=row['supporting_evidence_x'] # Use evidence from the S1 merge
# #             )
# #             new_llm_codes.append(codes)
# #             if (index + 1) % batch_size == 0 and (index + 1) < len(df_merged): # type: ignore
# #                 time.sleep(5)

# #         df_merged['stage5_llm_codes'] = pd.Series(new_llm_codes, index=df_merged.index)
# #         print("✅ Substage 5.1 complete.")

# #         print("\n--- Running Substage 5.2: Final Consolidation ---")
# #         consolidated_list = []
# #         for index, row in df_merged.iterrows():
# #             candidate_set = set()
# #             # Source 1: Stage 1 codes
# #             try: candidate_set.update(ast.literal_eval(row['icd_codes_x']))
# #             except: pass
# #             # Source 2: Stage 4 semantic match
# #             if pd.notna(row.get('concept_identifier')): candidate_set.add(str(row['concept_identifier']))
# #             # Source 3: Stage 5 new LLM codes
# #             if row.get('stage5_llm_codes'): candidate_set.update(row['stage5_llm_codes'])
# #             consolidated_list.append(list(candidate_set))
        
# #         df_merged['candidate_icd_codes'] = consolidated_list
# #         print("✅ Substage 5.2 complete.")

# #         final_columns = ['chief_complaint', 'supporting_evidence_x', 'patient_sex_x', 'concept_identifier', 'candidate_icd_codes']
# #         output_df = df_merged[final_columns].rename(columns={
# #             'supporting_evidence_x': 'supporting_evidence',
# #             'patient_sex_x': 'patient_sex'
# #         })
        
# #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# #         output_df.to_csv(output_path, index=False, encoding='utf-8')
        
# #         print(f"\n🎉 Consolidation complete! Enhanced candidate list saved to '{output_path}'.")

# #     except Exception as e:
# #         print(f"❌ An unexpected error occurred during Stage 5 processing: {e}")

# import pandas as pd
# import ast
# import os
# import json
# import re
# import time
# import google.generativeai as genai

# # --- Substage 4.1: The LLM Generator Class ---
# class Stage5_LLMGenerator:
#     """Uses an LLM to generate candidate codes based on normalized text and evidence."""
#     def __init__(self, model):
#         self.model = model
#         self.prompt_template = """
#         You are a clinical investigator. Your task is to analyze the provided clinical text and
#         generate a list of 2-3 relevant ICD-10 codes.

#         **Crucial Instruction:** Do not just code for the mentioned symptom. Analyze the full context
#         for clues (like medications or patient history) that point to a more specific **underlying diagnosis**.
#         If such a diagnosis is likely, include its code.

#         **Example:**
#         - **Context:** "wheezing + tight chest, used inhaler 2x"
#         - **Rewritten Complaint:** "Wheezing and chest tightness"
#         - **Your Inferred Codes:** You should return codes for Asthma (e.g., "J45.909") in addition
#         to the symptom code for Wheezing (e.g., "R06.2"), as "inhaler" strongly implies asthma.

#         Return your response as a single, raw JSON array of strings.
#         ---
#         **Supporting Evidence:**
#         "{context}"

#         **Rewritten Complaint Text:**
#         "{rewritten_complaint}"
#         ---

#         JSON Array Response:
#         """

#     def generate_codes(self, rewritten_complaint: str, context: str) -> list[str]:
#         prompt = self.prompt_template.format(
#             context=context,
#             rewritten_complaint=rewritten_complaint
#         )
#         try:
#             response = self.model.generate_content(prompt)
#             json_str = response.text.strip()
#             # Use regex to find the JSON array to handle cases where the LLM adds extra text
#             match = re.search(r'\[.*\]', json_str, re.DOTALL)
#             if not match:
#                 print(f"   ⚠️ Could not find a JSON array in the LLM response: {json_str}")
#                 return []
#             # Parse the found string as JSON
#             parsed_json = json.loads(match.group(0))
#             return [str(code) for code in parsed_json] if isinstance(parsed_json, list) else []
#         except Exception as e:
#             print(f"   ⚠️ LLM Error during Stage 5 generation: {e}")
#             return []

# # --- Main Logic Function Updated with Batching ---
# def run_candidate_enhancement(stage1_path: str, stage4_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
#     """
#     Runs Stage 5 to generate new candidate codes using an LLM and consolidates them.
    
#     Args:
#         stage1_path (str): Path to the output CSV from Stage 1 (contains original evidence).
#         stage4_path (str): Path to the output CSV from Stage 4 (contains rewritten complaints).
#         output_path (str): Path to save the final consolidated CSV.
#         batch_size (int): The number of rows to process in each API batch.
#         delay_between_batches (int): Seconds to wait between batches.
#     """
#     print("\n--- Starting Stage 5: Candidate Enhancement & Consolidation ---\n")
#     try:
#         genai.configure(api_key="AIzaSyAEI45NC4nP8cKLMdl8O8h3A8DH7Wnsrmc") # type: ignore
#         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
#     except Exception as e:
#         print(f"❌ Error configuring Gemini API: {e}"); return

#     try:
#         print("Loading data from Stage 1 and Stage 4...")
#         df_stage1 = pd.read_csv(stage1_path)
#         df_stage4 = pd.read_csv(stage4_path)
        
#         # Merge dataframes using index to align rows correctly
#         df_merged = pd.merge(df_stage1, df_stage4, left_index=True, right_index=True, how='left')
#         print("✅ Data merged successfully.")

#         print(f"\n--- Running Substage 5.1: LLM Candidate Generation in batches of {batch_size} ---")
#         llm_generator = Stage5_LLMGenerator(llm_model)
#         all_new_codes = []

#         # Process the DataFrame in batches
#         for i in range(0, len(df_merged), batch_size):
#             batch_df = df_merged.iloc[i : i + batch_size]
#             print(f"   Processing batch {i//batch_size + 1} (rows {i+1} to {i+len(batch_df)})...")
            
#             for index, row in batch_df.iterrows():
#                 codes = llm_generator.generate_codes(
#                     rewritten_complaint=str(row['rewritten_complaint']),
#                     context=str(row['supporting_evidence_x'])
#                 )
#                 all_new_codes.append(codes)
#                 time.sleep(1)  # Small delay between individual API calls to prevent rapid-fire requests

#             # If this is not the last batch, wait before starting the next one
#             if (i + batch_size) < len(df_merged):
#                 print(f"   Waiting {delay_between_batches} seconds to respect API rate limit...")
#                 time.sleep(delay_between_batches)

#         df_merged['stage5_llm_codes'] = pd.Series(all_new_codes, index=df_merged.index)
#         print("✅ Substage 5.1 complete.")

#         print("\n--- Running Substage 5.2: Final Consolidation ---")
#         consolidated_list = []
#         for index, row in df_merged.iterrows():
#             candidate_set = set()
#             if pd.notna(row.get('concept_identifier')): 
#                 candidate_set.add(str(row['concept_identifier']))
#             if isinstance(row.get('stage5_llm_codes'), list): 
#                 candidate_set.update(row['stage5_llm_codes'])
#             consolidated_list.append(sorted(list(candidate_set))) # Sort for consistent output
        
#         df_merged['candidate_icd_codes'] = consolidated_list
#         print("✅ Substage 5.2 complete.")

#         # Prepare and save the final output dataframe
#         final_columns = ['chief_complaint_x', 'supporting_evidence_x', 'patient_sex_x', 'concept_identifier', 'candidate_icd_codes']
#         output_df = df_merged[final_columns].rename(columns={
#             'chief_complaint_x': 'chief_complaint',
#             'supporting_evidence_x': 'supporting_evidence',
#             'patient_sex_x': 'patient_sex'
#         })
        
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
#         output_df.to_csv(output_path, index=False, encoding='utf-8')
        
#         print(f"\n🎉 Consolidation complete! Enhanced candidate list saved to '{output_path}'.")

#     except FileNotFoundError as e:
#         print(f"❌ Error: An input file was not found. Please check the path. Details: {e}")
#     except Exception as e:
#         print(f"❌ An unexpected error occurred during Stage 5 processing: {e}")

import pandas as pd
import ast
import os
import json
import re
import time
import google.generativeai as genai
import random

class Stage5_LLMGenerator:
    """Uses an LLM to generate candidate codes based on normalized text and evidence."""
    def __init__(self, model):
        self.model = model
        self.prompt_template = """
        You are a clinical investigator. Your task is to analyze the provided clinical text and
        generate a list of 3-4 relevant ICD-10 codes.

        **Crucial Instruction:** Do not just code for the mentioned symptom. Analyze the full context
        for clues (like medications or patient history) that point to a more specific **underlying diagnosis**.
        If such a diagnosis is likely, include its code.

        Return your response as a single, raw JSON array of strings.
        ---
        **Supporting Evidence:** "{context}"
        **Rewritten Complaint Text:** "{rewritten_complaint}"
        ---
        JSON Array Response:
        """

    def generate_codes(self, rewritten_complaint: str, context: str, max_retries=3) -> list[str]:
        """Generates codes with an exponential backoff retry mechanism."""
        base_delay = 2
        for attempt in range(max_retries):
            try:
                prompt = self.prompt_template.format(context=context, rewritten_complaint=rewritten_complaint)
                response = self.model.generate_content(prompt)
                json_str = response.text.strip()
                match = re.search(r'\[.*\]', json_str, re.DOTALL)
                if not match: return []
                parsed_json = json.loads(match.group(0))
                return [str(code) for code in parsed_json] if isinstance(parsed_json, list) else []
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = "503" in error_str or "timeout" in error_str or "failed to connect" in error_str
                if is_retryable and attempt < max_retries - 1:
                    wait_time = (base_delay ** attempt) + (random.uniform(0, 1))
                    print(f"   ⚠️ API Error (Attempt {attempt + 1}/{max_retries}): Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"   ⚠️ LLM Error during Stage 5 generation: {e}")
                    return []
        return []

def run_candidate_enhancement(stage1_path: str, stage4_path: str, output_path: str, batch_size: int):
    """Runs Stage 5 with the corrected consolidation logic."""
    print("\n--- Starting Stage 5: Candidate Enhancement & Consolidation ---\n")
    try:
        print(f"\n--- Running Substage 5.1: LLM Candidate Generation in batches of {batch_size} ---")
        genai.configure(api_key="AIzaSyAEI45NC4nP8cKLMdl8O8h3A8DH7Wnsrmc")
        llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0})
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}"); return

    try:
        df_stage1 = pd.read_csv(stage1_path)
        df_stage4 = pd.read_csv(stage4_path)
        df_merged = pd.merge(df_stage1, df_stage4, left_index=True, right_index=True, how='left')

        llm_generator = Stage5_LLMGenerator(llm_model)
        new_llm_codes = [
            llm_generator.generate_codes(
                rewritten_complaint=row['rewritten_complaint'],
                context=row['supporting_evidence_x']
            )
            for _, row in df_merged.iterrows()
        ]
        df_merged['stage5_llm_codes'] = pd.Series(new_llm_codes, index=df_merged.index)
        print("✅ Substage 5.1 complete.")

        print("\n--- Running Substage 5.2: Final Consolidation ---")
        consolidated_list = []
        for index, row in df_merged.iterrows():
            candidate_set = set()
            
             # Include other Stage 4 candidates
            if pd.notna(row.get('rag_candidates')):
                try: 
                    rag_candidates = ast.literal_eval(row['rag_candidates'])
                    candidate_set.update(rag_candidates)
                except (ValueError, SyntaxError): 
                    pass
            
            # Source 2: Stage 5 new LLM-generated codes
            if isinstance(row.get('stage5_llm_codes'), list):
                candidate_set.update(row['stage5_llm_codes'])

            # Source 3: Stage 4 Top ICD Code
            if pd.notna(row.get('concept_identifier')):
                candidate_set.add(row['concept_identifier'])

            # Always include Stage 4's top-scored FAISS candidate
            if pd.notna(row.get('candidates')):
                try:
                    candidate_dicts = ast.literal_eval(row['candidates'])
                    # Get top-scored candidate (first in list)
                    if candidate_dicts:
                        top_scored_candidate = candidate_dicts[0]['CUI']
                        candidate_set.add(top_scored_candidate)
                except (ValueError, SyntaxError): 
                    pass
                
            consolidated_list.append(sorted(list(candidate_set)))
        
        df_merged['candidate_icd_codes'] = consolidated_list
        print("✅ Substage 5.2 complete.")

        final_columns = ['chief_complaint_x', 'supporting_evidence_x', 'patient_sex_x', 'concept_identifier', 'candidate_icd_codes']
        output_df = df_merged[final_columns].rename(columns={
            'chief_complaint_x': 'chief_complaint',
            'supporting_evidence_x': 'supporting_evidence',
            'patient_sex_x': 'patient_sex'
        })
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n🎉 Consolidation complete! Enhanced candidate list saved to '{output_path}'.")

    except Exception as e:
        print(f"❌ An unexpected error occurred during Stage 5 processing: {e}")