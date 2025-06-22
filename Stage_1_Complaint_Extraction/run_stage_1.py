import os
import pandas as pd

from extractor import run_extracting, deduplicate_extracted_complaints
from config import INPUT_FILE_PATH, RAW_OUTPUT_PATH, DEDUP_OUTPUT_PATH

if __name__ == "__main__":
    INPUT_FILE = INPUT_FILE_PATH
    RAW_OUTPUT_FILE = RAW_OUTPUT_PATH
    DEDUP_OUTPUT_FILE = DEDUP_OUTPUT_PATH
    
    try:
        df_notes_for_count = pd.read_csv(INPUT_FILE)
        
        while True:
            try:
                count_str = input(f"\nEnter the number of medical notes to process (1-{len(df_notes_for_count)}): ")
                count_to_run = int(count_str)
                if 1 <= count_to_run <= len(df_notes_for_count): break
                else: print(f"Please enter a number between 1 and {len(df_notes_for_count)}.")
            except ValueError: print("Invalid input. Please enter a whole number.")
            
        while True:
            try:
                batch_size_str = input("\nEnter the batch size for LLM processing (e.g., 5-10 is recommended): ")
                batch_size_to_run = int(batch_size_str)
                if batch_size_to_run > 0: break
                else: print("Batch size must be a positive number.")
            except ValueError: print("Invalid input. Please enter a whole number.")

        while True:
            dedup_choice = input("\nDo you want to deduplicate extracted complaints? (y/n): ").lower().strip()
            if dedup_choice in ['y', 'yes', 'n', 'no']: break
            else: print("Please enter 'y' for yes or 'n' for no.")

        run_extracting(
            input_path=INPUT_FILE, 
            output_path=RAW_OUTPUT_FILE,
            num_to_process=count_to_run, 
            batch_size=batch_size_to_run
        )

        if dedup_choice in ['y', 'yes']:
            print(f"\n--- Starting Deduplication ---")
            deduplicate_extracted_complaints(
                input_path=RAW_OUTPUT_FILE,
                output_path=DEDUP_OUTPUT_FILE
            )
            print(f"\n🎉 Pipeline Complete!")
            print(f"   ✅ Raw complaints: '{RAW_OUTPUT_FILE}'")
            print(f"   ✅ Deduplicated complaints: '{DEDUP_OUTPUT_FILE}'")
        else:
            print(f"\n🎉 Extraction Complete! Results saved to '{RAW_OUTPUT_FILE}'")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{INPUT_FILE}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")