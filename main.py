# ==============================================================================
# Important - Guideline for Running the Main.py Script
# ==============================================================================
# To run the entire pipeline from start to finish: python main.py
# To run only Stage 3 for testing: python main.py --start-stage 3 --end-stage 3
# To re-run the final two stages after a change: python main.py --start-stage 4
# ==============================================================================

import os
import argparse
import pandas as pd
from typing import Optional
import shutil

# --- Import the main logic function from each of your refactored stage scripts ---
# These imports are based on your provided file structure.
from Stage_1_Complaint_Extraction.extractor import run_extracting
from Stage_2_Normalization.normalizer import run_normalization
from Stage_3_Complaint_Rewriting.rewriter import run_rewriting
from Stage_4_Concept_Mapping.mapper import run_concept_mapping
from Stage_5_Consolidation.Consolidator import run_candidate_enhancement
from Stage_6_Reranking.reranker import run_reranking
from Stage_1_Complaint_Extraction.extractor import deduplicate_extracted_complaints

# ==============================================================================
# Centralized Configuration for all File Paths
# ==============================================================================
CONFIG = {
    # Stage 1
    'stage1_input': r"Stage_1_Complaint_Extraction\input_files\text.csv",
    'stage1_output': r"Stage_1_Complaint_Extraction\output_files\extracted_complaints.csv",
    'stage1_dedup_output': r"Stage_1_Complaint_Extraction\output_files\extracted_complaints_dedup.csv",

    # Stage 2
    'stage2_input': r"Stage_1_Complaint_Extraction\output_files\extracted_complaints.csv",
    'stage2_abbreviations': r"Stage_2_Normalization\input_files\abbreviations.csv",
    'stage2_output': r"Stage_2_Normalization\output_files\normalized_complaints.csv",

    # Stage 3
    'stage3_input': r"Stage_2_Normalization\output_files\normalized_complaints.csv",
    'stage3_output': r"Stage_3_Complaint_Rewriting\output_files\rewritten_complaints.csv",

    # Stage 4
    'stage4_input': r"Stage_3_Complaint_Rewriting\output_files\rewritten_complaints.csv",
    'stage4_kb': r"Stage_4_Concept_Mapping\output_files\icd_code_with_descriptions.csv",
    'stage4_faiss': r"Stage_4_Concept_Mapping\output_files\umls_faiss.index",
    'stage4_output': r"Stage_4_Concept_Mapping\output_files\concept_mapped_complaints.csv",

    # Stage 5
    'stage5_input_s1': r"Stage_1_Complaint_Extraction\output_files\extracted_complaints.csv",
    'stage5_input_s4': r"Stage_4_Concept_Mapping\output_files\concept_mapped_complaints.csv",
    'stage5_output': r"Stage_5_Consolidation\output_files\combined_list_for_reranking.csv",

    # Stage 6
    'stage6_input': r"Stage_5_Consolidation\output_files\combined_list_for_reranking.csv",
    'stage6_kb': r"Stage_4_Concept_Mapping\output_files\icd_code_with_descriptions.csv",
    'stage6_output': r"Stage_6_Reranking\output_files\final_icd_predictions.csv",
}

# ==============================================================================
# Main Pipeline Orchestrator
# ==============================================================================
def main(args, num_to_process=None, llm_batch_size=None, dedup_choice=None, single_complaint_mode=False):
    """Main function to orchestrate the new 6-stage pipeline."""
    start_stage = args.start_stage
    end_stage = args.end_stage

    if single_complaint_mode:
        num_to_process = 1
        llm_batch_size = 1

    print(f"\n--- Running pipeline from Stage {start_stage} to Stage {end_stage} ---")

    # --- Stage 1 ---
    if start_stage <= 1 <= end_stage:
        print("\n--- EXECUTING STAGE 1: COMPLAINT EXTRACTION ---")
        run_extracting(CONFIG['stage1_input'], CONFIG['stage1_output'], num_to_process, llm_batch_size) # type: ignore
        print("\n--- ✅ STAGE 1 EXECUTION COMPLETED ---")
    
        if not single_complaint_mode and dedup_choice in ['y', 'yes']:
            print("\n--- EXECUTING DEDUPLICATION AFTER STAGE 1 ---")
            dedup_path = deduplicate_extracted_complaints(
                input_path=CONFIG['stage1_output'],
                output_path=CONFIG['stage1_dedup_output']
            )
            if dedup_path and os.path.exists(dedup_path):
                print("\n--- ✅ DEDUPLICATION COMPLETED ---")
                # Update downstream stages to use the dedup file
                CONFIG['stage2_input'] = dedup_path
                CONFIG['stage5_input_s1'] = dedup_path
            else:
                print("\n⚠️ Deduplication failed or output file not found. Using original output.")
                CONFIG['stage2_input'] = CONFIG['stage1_output']
                CONFIG['stage5_input_s1'] = CONFIG['stage1_output']
        else:
            # Use original output for downstream stages
            CONFIG['stage2_input'] = CONFIG['stage1_output']
            CONFIG['stage5_input_s1'] = CONFIG['stage1_output']

    # --- Stage 2 ---
    if start_stage <= 2 <= end_stage:
        print("\n--- EXECUTING STAGE 2: TEXT NORMALIZATION ---")
        run_normalization(CONFIG['stage2_input'], CONFIG['stage2_abbreviations'], CONFIG['stage2_output'], llm_batch_size) # type: ignore
        print("\n--- ✅ STAGE 2 EXECUTION COMPLETED ---")

    # --- Stage 3 ---
    if start_stage <= 3 <= end_stage:
        print("\n--- EXECUTING STAGE 3: QUERY REWRITING ---")
        run_rewriting(CONFIG['stage3_input'], CONFIG['stage3_output'], llm_batch_size) # type: ignore
        print("\n--- ✅ STAGE 3 EXECUTION COMPLETED ---")

    # --- Stage 4 ---
    if start_stage <= 4 <= end_stage:
        print("\n--- EXECUTING STAGE 4: CONCEPT MAPPING ---")
        run_concept_mapping(CONFIG['stage4_input'], CONFIG['stage4_kb'], CONFIG['stage4_faiss'], CONFIG['stage4_output'], llm_batch_size) # type: ignore
        print("\n--- ✅ STAGE 4 EXECUTION COMPLETED ---")
        
    # --- Stage 5 ---
    if start_stage <= 5 <= end_stage:
        print("\n--- EXECUTING STAGE 5: CANDIDATE ENHANCEMENT ---")
        run_candidate_enhancement(CONFIG['stage5_input_s1'], CONFIG['stage5_input_s4'], CONFIG['stage5_output'], llm_batch_size) # type: ignore
        print("\n--- ✅ STAGE 5 EXECUTION COMPLETED ---")
        
    # --- Stage 6 ---
    if start_stage <= 6 <= end_stage:
        print("\n--- EXECUTING STAGE 6: FINAL SELECTION ---")
        run_reranking(
            input_path=CONFIG['stage6_input'], 
            kb_csv_path=CONFIG['stage6_kb'], 
            output_path=CONFIG['stage6_output'],
            batch_size=llm_batch_size # type: ignore
        )
        print("\n--- ✅ STAGE 6 (RERANKING) EXECUTION COMPLETED ---")
    
    print("\n-------------------- ✅ Pipeline execution complete --------------------")


# ==============================================================================
#                  --- NEW SCRIPT ENTRY POINT ---
# This block now handles the user's choice of input mode.
# ==============================================================================
if __name__ == '__main__':
    print("="*45)
    print("Welcome to the AEGIS Medical Coding Pipeline")
    print("="*45)
    
    mode = input("Select input mode:\n  1. Batch Mode (from a CSV file)\n  2. Single Complaint Mode (from terminal input)\nEnter your choice (1 or 2): ").strip()
    
    # --- BATCH FILE MODE ---
    if mode == '1':
        print("\n--- Batch File Mode Selected ---")
        while True:
            try:
                file_path = input("Please enter the full path to your input CSV file: ").strip()
                if os.path.exists(file_path):
                    CONFIG['stage1_input'] = file_path
                    print(f"Pipeline will run on: {file_path}")
                    break
                else:
                    print("❌ File not found. Please check the path and try again.")
            except Exception as e:
                print(f"An error occurred: {e}")

        parser = argparse.ArgumentParser(description="Run the 6-stage AEGIS medical coding pipeline.")
        parser.add_argument('--start-stage', type=int, default=1)
        parser.add_argument('--end-stage', type=int, default=6)
        args = parser.parse_args()

        if args.start_stage > args.end_stage:
            print("Error: --start-stage cannot be greater than --end-stage.")
        else:
            df_notes = pd.read_csv(CONFIG['stage1_input'])
            total_notes = len(df_notes)
            while True:
                num_str = input(f"\nEnter notes to process (1-{total_notes}): ")
                try:
                    num_to_process = int(num_str)
                    if 1 <= num_to_process <= total_notes: break
                    else: print(f"Please enter a number between 1 and {total_notes}.")
                except ValueError:
                    print("Invalid input. Please enter a whole number.")

            while True:
                batch_str = input(f"Enter global LLM batch size (e.g., 10): ")
                try:
                    llm_batch_size = int(batch_str)
                    if llm_batch_size > 0: break
                    else: print("Batch size must be a positive number.")
                except ValueError:
                    print("Invalid input. Please enter a whole number.")

            while True:
                dedup_choice = input("\nDo you want to deduplicate extracted complaints after Stage 1? (y/n): ").lower().strip()
                if dedup_choice in ['y', 'yes', 'n', 'no']: break
                else: print("Please enter 'y' for yes or 'n' for no.")

            # Now call main(args) with the collected values
            main(args, num_to_process=num_to_process, llm_batch_size=llm_batch_size, dedup_choice=dedup_choice)

    # --- SINGLE COMPLAINT MODE ---
    elif mode == '2':
        print("\n--- Single Complaint Mode Selected ---")
        complaint_text = input("Enter the full medical note or complaint text:\n> ")
        patient_sex = input("Enter patient sex (M/F/Unknown) [default: Unknown]: ").strip().upper() or "Unknown"
        
        single_note_df = pd.DataFrame([{
            'Document ID': 'single_complaint_run',
            'patient_sex': patient_sex,
            'medical_record_text': complaint_text
        }])
        
        # --- NEW: Define a safe, temporary file path ---
        base_input_dir = os.path.dirname(CONFIG['stage1_input'])
        temp_input_path = os.path.join(base_input_dir, '_temp_single_complaint_run.csv')
        
        # --- NEW: Use a try...finally block to ensure cleanup ---
        try:
            # Create the temporary input file
            os.makedirs(base_input_dir, exist_ok=True)
            single_note_df.to_csv(temp_input_path, index=False)
            print(f"\nTemporary input file created at '{temp_input_path}'")
            
            # --- CHANGE: Dynamically update the config to use the temp file ---
            CONFIG['stage1_input'] = temp_input_path
            
            # For a single run, we always run the full pipeline
            args = argparse.Namespace(start_stage=1, end_stage=6)
            
            main(args, single_complaint_mode=True)
            
            final_output_file = CONFIG['stage6_output']
            if os.path.exists(final_output_file):
                result_df = pd.read_csv(final_output_file)
                print("\n" + "="*20)
                print("--- FINAL PREDICTIONS ---")
                print("="*20)
                print(result_df[['chief_complaint', 'final_predicted_icd_code']].to_string(index=False))
            else:
                print("\n--- No final output file was generated. ---")

        finally:
            # --- NEW: Automatic cleanup of the temporary file ---
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
                print(f"\nTemporary file '{os.path.basename(temp_input_path)}' has been deleted.")

    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")