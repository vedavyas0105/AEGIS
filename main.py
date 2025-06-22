import os
import argparse
import pandas as pd
import config

# FIX: Use relative imports to ensure they work when main.py is in the root.
# FIX: Ensure function names match their definitions in the respective files.
from Stage_1_Complaint_Extraction.extractor import run_extracting, deduplicate_extracted_complaints
from Stage_2_Normalization.normalizer import run_normalization
from Stage_3_Complaint_Rewriting.rewriter import run_rewriting
from Stage_4_Concept_Mapping.mapper import run_concept_mapping
from Stage_5_Consolidation.Consolidator import run_candidate_enhancement
from Stage_6_Reranking.reranker import run_reranking


def main(filepath: str, start_stage: int, end_stage: int, num_to_process: int, llm_batch_size: int, dedup_choice: str, single_complaint_mode: bool = False):
    """
    Main function to orchestrate the new 6-stage pipeline.
    This version uses the config.py module and local variables for data flow.
    """
    print(f"--- Running pipeline from Stage {start_stage} to Stage {end_stage} ---")

    # This variable will track the output of Stage 1 to be used by later stages.
    stage1_final_output = config.STAGE1_DEDUP_OUTPUT_CSV if dedup_choice in ['y', 'yes'] else config.STAGE1_RAW_OUTPUT_CSV

    if start_stage <= 1 <= end_stage:
        print("\n--- EXECUTING STAGE 1: COMPLAINT EXTRACTION ---")
        run_extracting(
            input_path=filepath, 
            output_path=config.STAGE1_RAW_OUTPUT_CSV, 
            num_to_process=num_to_process, 
            batch_size=llm_batch_size
        )
        print("--- STAGE 1 EXECUTION COMPLETED ---")
        
        if not single_complaint_mode and dedup_choice in ['y', 'yes']:
            print("--- EXECUTING DEDUPLICATION AFTER STAGE 1 ---")
            dedup_path = deduplicate_extracted_complaints(
                input_path=config.STAGE1_RAW_OUTPUT_CSV, 
                output_path=config.STAGE1_DEDUP_OUTPUT_CSV
            )
            if not dedup_path:
                print("Deduplication failed. Using raw output for subsequent stages.")
                stage1_final_output = config.STAGE1_RAW_OUTPUT_CSV

    if start_stage <= 2 <= end_stage:
        print("\n--- EXECUTING STAGE 2: TEXT NORMALIZATION ---")
        run_normalization(
            input_complaints_path=stage1_final_output,
            abbreviation_file_path=config.STAGE2_ABBREVIATIONS_CSV,
            output_path=config.STAGE2_OUTPUT_CSV,
            batch_size=llm_batch_size
        )
        print("--- STAGE 2 EXECUTION COMPLETED ---")

    if start_stage <= 3 <= end_stage:
        print("\n--- EXECUTING STAGE 3: QUERY REWRITING ---")
        run_rewriting(
            input_path=config.STAGE2_OUTPUT_CSV,
            output_path=config.STAGE3_OUTPUT_CSV,
            batch_size=llm_batch_size
        )
        print("--- STAGE 3 EXECUTION COMPLETED ---")

    if start_stage <= 4 <= end_stage:
        print("\n--- EXECUTING STAGE 4: CONCEPT MAPPING ---")
        run_concept_mapping(
            input_path=config.STAGE3_OUTPUT_CSV,
            kb_csv_path=config.STAGE4_KB_CSV,
            faiss_index_path=config.STAGE4_FAISS_INDEX,
            output_path=config.STAGE4_OUTPUT_CSV,
            batch_size=llm_batch_size
        )
        print("--- STAGE 4 EXECUTION COMPLETED ---")

    if start_stage <= 5 <= end_stage:
        print("\n--- EXECUTING STAGE 5: CANDIDATE ENHANCEMENT ---")
        run_candidate_enhancement(
            stage1_path=stage1_final_output,
            stage4_path=config.STAGE4_OUTPUT_CSV,
            output_path=config.STAGE5_OUTPUT_CSV,
            batch_size=llm_batch_size
        )
        print("--- STAGE 5 EXECUTION COMPLETED ---")

    if start_stage <= 6 <= end_stage:
        print("\n--- EXECUTING STAGE 6: FINAL SELECTION ---")
        run_reranking(
            input_path=config.STAGE5_OUTPUT_CSV,
            kb_csv_path=config.STAGE4_KB_CSV,
            output_path=config.STAGE6_OUTPUT_CSV,
            batch_size=llm_batch_size
        )
        print("--- STAGE 6 RERANKING EXECUTION COMPLETED ---")

    print("\n-------------------- Pipeline execution complete --------------------")


if __name__ == "__main__":
    print("=" * 45)
    print("Welcome to the AEGIS Medical Coding Pipeline")
    print("=" * 45)

    mode = input("Select input mode:\n  1. Batch Mode (from a CSV file)\n  2. Single Complaint Mode (from terminal input)\nYour choice (1 or 2): ").strip()

    if mode == '1':
        print("\n--- Batch File Mode Selected ---")
        
        while True:
            filepath = input("Please enter the full path to your input CSV file: ").strip()
            if os.path.exists(filepath):
                break
            else:
                print("File not found. Please check the path and try again.")
        
        parser = argparse.ArgumentParser(description="Run the 6-stage AEGIS medical coding pipeline.")
        parser.add_argument("--start-stage", type=int, default=1, help="The stage to start from (1-6).")
        parser.add_argument("--end-stage", type=int, default=6, help="The stage to end at (1-6).")
        args = parser.parse_args()

        if args.start_stage > args.end_stage:
            print("Error: --start-stage cannot be greater than --end-stage.")
        else:
            total_notes = len(pd.read_csv(filepath))
            while True:
                try:
                    num_str = input(f"Notes to process (1-{total_notes}): ")
                    num_to_process = int(num_str)
                    if 1 <= num_to_process <= total_notes: break
                    else: print(f"Please enter a number between 1 and {total_notes}.")
                except ValueError: print("Invalid input. Please enter a whole number.")
            
            while True:
                try:
                    batch_str = input(f"Enter global LLM batch size (e.g., 10): ")
                    llm_batch_size = int(batch_str)
                    if llm_batch_size > 0: break
                    else: print("Batch size must be a positive number.")
                except ValueError: print("Invalid input. Please enter a whole number.")

            dedup_choice = ''
            while True:
                dedup_choice = input("Deduplicate complaints after Stage 1? (y/n): ").lower().strip()
                if dedup_choice in ['y', 'yes', 'n', 'no']: break
                else: print("Please enter 'y' for yes or 'n' for no.")

            # CHANGE: All collected variables are now passed as arguments to main()
            main(filepath, args.start_stage, args.end_stage, num_to_process, llm_batch_size, dedup_choice)

    elif mode == '2':
        print("\n--- Single Complaint Mode Selected ---")
        complaint_text = input("Enter the full medical note or complaint text: ")
        patient_sex = input("Enter patient sex (M/F/Unknown) [default: Unknown]: ").strip().upper() or "Unknown"

        single_note_df = pd.DataFrame([{"Document ID": "single_complaint_run", "patient_sex": patient_sex, "medical_record_text": complaint_text}])
        temp_input_path = os.path.join(config.TEMP_DATA_DIR, "temp_single_complaint_run.csv")
        
        try:
            os.makedirs(config.TEMP_DATA_DIR, exist_ok=True)
            single_note_df.to_csv(temp_input_path, index=False)
            print(f"Temporary input file created at {temp_input_path}")
            
            # For a single run, we always run the full pipeline
            main(filepath=temp_input_path, start_stage=1, end_stage=6, num_to_process=1, llm_batch_size=1, dedup_choice='n', single_complaint_mode=True)
            
            final_output_file = config.STAGE6_OUTPUT_CSV
            if os.path.exists(final_output_file):
                result_df = pd.read_csv(final_output_file)
                print("\n" + "="*20 + "\n--- FINAL PREDICTIONS ---\n" + "="*20)
                print(result_df[['chief_complaint', 'final_predicted_icd_code']].to_string(index=False))
            else:
                print("--- No final output file was generated. ---")
        
        finally:
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
                print(f"\nTemporary file '{os.path.basename(temp_input_path)}' has been deleted.")

    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")