import pandas as pd
import os
import time
import config
import google.generativeai as genai

class ComplaintRewriter:
    """Uses an LLM to rewrite a patient complaint into a standard medical phrase."""
    def __init__(self, model):
        self.model = model
        self.prompt_template = """
        You are a clinical terminology expert. Your task is to rewrite the following "Patient Complaint" into a concise, standard medical phrase suitable for searching a clinical knowledge base like UMLS.

        Translate colloquial terms into formal medical terms. Do not add any explanation, just return the rewritten phrase.

        **Examples:**

        1. Patient Complaint: "belly ache and feeling gassy"
        Rewritten Complaint: "abdominal pain and flatulence"

        2. Patient Complaint: "feeling down and sad for weeks"
        Rewritten Complaint: "depressed mood"

        3. Patient Complaint: "pt c/o sob on exertion"
        Rewritten Complaint: "dyspnea on exertion"

        4. Patient Complaint: "hurts to pee"
        Rewritten Complaint: "dysuria"

        5. Patient Complaint: "pain in the lower back"
        Rewritten Complaint: "low back pain"

        6. Patient Complaint: "throwing up after eating"
        Rewritten Complaint: "postprandial vomiting"

        7. Patient Complaint: "trouble sleeping at night"
        Rewritten Complaint: "insomnia"

        8. Patient Complaint: "pain in the chest when breathing"
        Rewritten Complaint: "pleuritic chest pain"

        9. Patient Complaint: "hx of heart attack"
        Rewritten Complaint: "history of myocardial infarction"

        10. Patient Complaint: "high blood sugar"
        Rewritten Complaint: "hyperglycemia"

        ---
        Patient Complaint: "{normalized_complaint}"
        Rewritten Complaint:
        """

    def rewrite_complaint(self, normalized_complaint: str) -> str:
        """Rewrites a single complaint text."""
        prompt = self.prompt_template.format(normalized_complaint=normalized_complaint)
        try:
            response = self.model.generate_content(prompt)
            # Return the rewritten text, falling back to original if LLM fails
            return response.text.strip() or normalized_complaint
        except Exception as e:
            print(f"   ⚠️ LLM Error during rewriting: {e}. Using original text.")
            return normalized_complaint

# def run_rewriting(input_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
def run_rewriting(input_path: str, output_path: str, batch_size: int, delay_between_batches: int = 10):
    """
    Executes the query rewriting process for the entire input file in batches.
    
    Args:
        input_path (str): Path to the CSV file with normalized complaints.
        output_path (str): Path to save the final CSV with rewritten complaints.
        batch_size (int): The number of complaints to process in each batch.
        delay_between_batches (int): The number of seconds to wait between batches.
    """
    print("--- Starting Stage 3: Query Rewriting ---")
    try:
        genai.configure(api_key=config.STAGE_3_GEMINI_API_KEY) # type: ignore
        llm_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME, generation_config={"temperature": 0}) # type: ignore
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}"); return

    try:
        df_input = pd.read_csv(input_path)
        rewriter = ComplaintRewriter(llm_model)
        
        complaints_to_process = df_input['final_normalized_complaint'].tolist()
        rewritten_complaints = []
        
        print(f"Rewriting {len(complaints_to_process)} complaints in batches of {batch_size}...")

        # Process complaints in batches
        for i in range(0, len(complaints_to_process), batch_size):
            batch = complaints_to_process[i : i + batch_size]
            print(f"   Processing batch {i//batch_size + 1} (complaints {i+1} to {i+len(batch)})...")
            
            # Rewrite each complaint within the current batch
            for complaint in batch:
                rewritten = rewriter.rewrite_complaint(str(complaint))
                rewritten_complaints.append(rewritten)
                # This small per-request delay can help prevent hitting rapid-fire limits
                time.sleep(1)

            # If this is not the last batch, wait for the specified delay period
            if (i + batch_size) < len(complaints_to_process):
                print(f"   Waiting {delay_between_batches} seconds to respect API rate limit...")
                time.sleep(delay_between_batches)

        df_input['rewritten_complaint'] = rewritten_complaints
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_input.to_csv(output_path, index=False)
        
        print(f"\n🎉 Rewriting complete! Rewritten complaints saved to '{output_path}'.")

    except Exception as e:
        print(f"❌ An unexpected error occurred in Stage 3: {e}")