import pandas as pd
import config

from .mapper import run_concept_mapping

def get_valid_batch_size() -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input("Enter the LLM batch size for Stage 4 (e.g., 10): ")
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
    INPUT_FILE = config.STAGE3_OUTPUT_CSV
    KB_CSV_FILE = config.STAGE4_KB_CSV
    FAISS_INDEX_FILE = config.STAGE4_FAISS_INDEX
    OUTPUT_FILE = config.STAGE4_OUTPUT_CSV

    batch_size_to_run = get_valid_batch_size()

    try:
        print("Running Stage 3 on the entire input file for standalone testing...")

        # --- Call the main logic function ---
        run_concept_mapping(
            input_path=INPUT_FILE,
            kb_csv_path=KB_CSV_FILE,
            faiss_index_path=FAISS_INDEX_FILE,
            output_path=OUTPUT_FILE,
            batch_size=batch_size_to_run
        )
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")