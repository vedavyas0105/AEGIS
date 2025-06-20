import pandas as pd

# --- FIX: The import now correctly points to 'stage3_mapper' ---
from mapper import run_concept_mapping

def get_valid_batch_size(limit: int) -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input(f"Enter the LLM batch size for Stage 4 (1 to {limit}): ")
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
    INPUT_NORMALIZED_COMPLAINTS = r"..\Stage_3_Complaint_Rewriting\output_files\rewritten_complaints.csv"
    icd_code_with_descriptions_CSV = r"output_files\icd_code_with_descriptions.csv"
    FAISS_INDEX_FILE = r"output_files\umls_faiss.index"
    OUTPUT_CONCEPT_MAPPED_CSV = r"output_files\concept_mapped_complaints.csv"

    FREE_TIER_LIMIT = 15
    batch_size_to_run = get_valid_batch_size(limit=FREE_TIER_LIMIT)

    try:
        # --- This script no longer needs user input. It processes the whole file by default. ---
        print("Running Stage 3 on the entire input file for standalone testing...")

        # --- Call the main logic function ---
        run_concept_mapping(
            input_path=INPUT_NORMALIZED_COMPLAINTS,
            kb_csv_path=icd_code_with_descriptions_CSV,
            faiss_index_path=FAISS_INDEX_FILE,
            output_path=OUTPUT_CONCEPT_MAPPED_CSV,
            batch_size=batch_size_to_run
        )
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")