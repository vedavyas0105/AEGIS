import os
import pandas as pd
import google.generativeai as genai
import time
import json
import config

# These custom tool classes are assumed to exist in their respective files.
# The code below will work as long as they are importable.
from .candidate_generator import UMLSConceptCandidateGenerator
from .llm_classifier import LLMClassifier

def run_concept_mapping(input_path: str, kb_csv_path: str, faiss_index_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
    """
    Executes the core logic for Stage 4: Concept Mapping in batches.
    This function now uses the 'rewritten_complaint' for searching.
    
    Args:
        input_path (str): Path to the input CSV from the previous stage.
        kb_csv_path (str): Path to the knowledge base CSV.
        faiss_index_path (str): Path to the pre-built FAISS index.
        output_path (str): Path to save the final output CSV.
        batch_size (int): The number of complaints to process in each batch.
        delay_between_batches (int): Seconds to wait between batches.
    """
    # --- 1. Configuration & Initialization (No changes here) ---
    try:
        genai.configure(api_key=config.STAGE_4_GEMINI_API_KEY) # type: ignore
        llm_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME, generation_config={"temperature": 0}) # type: ignore
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}"); return

    try:
        print("\n--- Initializing Tools for Stage 4 ---")
        generator = UMLSConceptCandidateGenerator(kb_csv_path, faiss_index_path)
        disambiguator = LLMClassifier(llm_model)
        print("✅ Tools initialized successfully.")

        # --- 2. Load Data ---
        df_to_process = pd.read_csv(input_path)
        print(f"Processing all {len(df_to_process)} complaints from '{input_path}'.")
        
        df_to_process['candidates'] = None
        df_to_process['concept_identifier'] = ""
        df_to_process['candidates'] = df_to_process['candidates'].astype('object')

        # --- 3. Process Each Complaint in Batches ---
        print(f"\n--- Starting Concept Mapping Process in batches of {batch_size} ---")
        
        for i in range(0, len(df_to_process), batch_size):
            batch_df = df_to_process.iloc[i : i + batch_size]
            print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")
            
            for index, row in batch_df.iterrows():
                # KEY CHANGE: Use the rewritten complaint from Stage 3
                query_text = str(row['rewritten_complaint'])
                context_evidence = str(row.get('supporting_evidence', query_text))
                
                print(f"\nProcessing complaint ({int(index) + 1}/{len(df_to_process)}): '{query_text}'") # type: ignore

                # Substage 4.1: Generate candidates using the rewritten query text
                candidates = generator.generate_candidates(query_text, top_k=5)
                # Note: The original index is used to update the main DataFrame correctly
                df_to_process.at[int(index), 'candidates'] = json.dumps(candidates) if candidates else None # type: ignore
                
                if not candidates:
                    print("   -> No candidates found. Skipping."); continue
                
                print(f"   -> Found {len(candidates)} candidates.")

                # Substage 4.2: Classify using the rewritten query text
                final_identifier = disambiguator.select_best_concept(
                    context=context_evidence,
                    normalized_text=query_text, # Pass the rewritten text to the LLM for context
                    candidates=candidates
                )
                
                if final_identifier:
                    print(f"   -> LLM selected Identifier: {final_identifier}")
                    df_to_process.at[int(index), 'concept_identifier'] = final_identifier # type: ignore
                else:
                    print("   -> LLM did not return a valid identifier.")
                
                # A small delay per-request is good practice to avoid hitting "requests per second" limits
                time.sleep(1)

            # After a batch is processed, wait if it is not the last one
            if (i + batch_size) < len(df_to_process):
                print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
                time.sleep(delay_between_batches)

        # --- 4. Save Final Output ---
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_to_process.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n🎉 Concept Mapping Complete! Concept-mapped data saved to '{output_path}'.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred in Stage 4: {e}")