import os
import spacy
import pandas as pd
import json
import google.generativeai as genai
import time

# Import your custom classes from their respective files
from .dictionary_expander import AbbreviationExpander
from .llm_expander import LLMContextualExpander

def run_normalization(input_complaints_path: str, abbreviation_file_path: str, output_path: str, batch_size: int):
    """
    Executes the core logic for Stage 2: Text Normalization.
    This function is designed to be called by an orchestrator script.

    Args:
        input_complaints_path (str): Path to the CSV file from Stage 1.
        abbreviation_file_path (str): Path to the custom abbreviations CSV.
        output_path (str): Path to save the final normalized complaints CSV.
        batch_size (int): The number of complaints to send to the LLM in each batch.
    """
    # --- 1. Configuration & Setup ---
    try:
        genai.configure(api_key="AIzaSyCw3wBHGP530rx6WJDqFMfyvlldSkDsfMs") # type: ignore
        llm_model = genai.GenerativeModel('gemini-2.0-flash') # type: ignore
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return

    TEMP_JSON_DICT_PATH = "temp_abbreviations_for_spacy.json"
    # DELAY_BETWEEN_BATCHES = 10
    DELAY_BETWEEN_BATCHES = 5

    try:
        # --- 2. Prepare Dictionary ---
        df_abbr = pd.read_csv(abbreviation_file_path)
        abbreviations_dict = pd.Series(df_abbr.full_form.values, index=df_abbr.abbreviation.str.lower()).to_dict()
        with open(TEMP_JSON_DICT_PATH, "w") as f:
            json.dump(abbreviations_dict, f)

        # --- 3. Pass 1: Dictionary-Based Expansion ---
        print("\n--- Running Pass 1: Dictionary-Based Expansion ---")
        nlp = spacy.load("en_core_web_sm")
        if "abbreviation_expander" not in nlp.pipe_names:
            nlp.add_pipe("abbreviation_expander", config={"dictionary_path": TEMP_JSON_DICT_PATH}, after="parser")
        
        df_complaints = pd.read_csv(input_complaints_path)
        pass1_texts = []
        for text in df_complaints["chief_complaint"]:
            doc = nlp(str(text))
            reconstructed_tokens = [token._.expansion if token._.is_abbreviation else token.text for token in doc]
            pass1_texts.append(" ".join(reconstructed_tokens))
        df_complaints["pass1_normalized"] = pass1_texts
        print("✅ Pass 1 complete.")

        # --- 4. Pass 2: Contextual LLM Expansion ---
        print(f"\n--- Running Pass 2: Contextual Expansion (LLM) in batches of {batch_size} ---")
        llm_expander = LLMContextualExpander(llm_model)
        
        texts_to_process = df_complaints["pass1_normalized"].tolist()
        final_texts = []
        
        for i in range(0, len(texts_to_process), batch_size):
            batch = texts_to_process[i : i + batch_size]
            print(f"   Processing batch {i//batch_size + 1} (complaints {i+1} to {i+len(batch)})...")
            expanded_batch = llm_expander.expand_batch(batch)
            final_texts.extend(expanded_batch)

            if (i + batch_size) < len(texts_to_process):
                print(f"   Waiting {DELAY_BETWEEN_BATCHES} seconds to respect API rate limit...")
                time.sleep(DELAY_BETWEEN_BATCHES)

        df_complaints["final_normalized_complaint"] = final_texts
        print("✅ Pass 2 complete.")

        # --- 5. Save Final Output ---
        # IMPORTANT: We carry forward all columns from the input to ensure data like
        # 'supporting_evidence' and 'patient_sex' is not lost for later stages.
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_complaints.to_csv(output_path, index=False)
        print(f"\n🎉 Normalization complete. Output saved to '{output_path}'.")

    finally:
        if os.path.exists(TEMP_JSON_DICT_PATH):
            os.remove(TEMP_JSON_DICT_PATH)