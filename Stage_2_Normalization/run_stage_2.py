# run_stage2.py
import pandas as pd

# --- FIX: The import now correctly points to 'stage2_normalizer' ---
from normalizer import run_normalization

def get_valid_batch_size(limit: int) -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input(f"Enter the LLM batch size for Stage 2 (1 to {limit}): ")
            batch_size = int(batch_size_str)
            if 1 <= batch_size <= limit:
                return batch_size
            else:
                print(f"Error: Batch size must be between 1 and {limit}.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

# ==============================================================================
# This block allows the script to be run directly for individual testing.
# ==============================================================================
if __name__ == "__main__":
    # --- Configuration for Direct Execution ---
    YOUR_ABBREVIATION_FILE = r"input_files\abbreviations.csv"
    INPUT_COMPLAINTS_CSV = r'..\Stage_1_Complaint_Extraction\output_files\extracted_complaints.csv'
    FINAL_NORMALIZED_OUTPUT_CSV = r"output_files\normalized_complaints.csv"
    
    # --- Get User Input for Direct Execution ---
    FREE_TIER_LIMIT = 15
    batch_size_to_run = get_valid_batch_size(limit=FREE_TIER_LIMIT)

    try:
        # --- Call the main logic function ---
        run_normalization(
            input_complaints_path=INPUT_COMPLAINTS_CSV,
            abbreviation_file_path=YOUR_ABBREVIATION_FILE,
            output_path=FINAL_NORMALIZED_OUTPUT_CSV,
            batch_size=batch_size_to_run
        )
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")