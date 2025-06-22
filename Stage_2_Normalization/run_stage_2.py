import config
import pandas as pd

from .normalizer import run_normalization

def get_valid_batch_size() -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input("Enter the LLM batch size for Stage 2 (e.g., 10): ")
            batch_size = int(batch_size_str)
            if batch_size > 0:
                return batch_size
            else:
                print("Error: Batch size must be a positive number.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

# ==============================================================================
# This block allows the script to be run directly for individual testing.
# ==============================================================================
if __name__ == "__main__":
    # --- Configuration for Direct Execution ---
    YOUR_ABBREVIATION_FILE = config.STAGE2_ABBREVIATIONS_CSV
    INPUT_COMPLAINTS_CSV = config.STAGE1_DEDUP_OUTPUT_CSV
    FINAL_NORMALIZED_OUTPUT_CSV = config.STAGE2_OUTPUT_CSV
    
    # --- Get User Input for Direct Execution ---
    batch_size_to_run = get_valid_batch_size()

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