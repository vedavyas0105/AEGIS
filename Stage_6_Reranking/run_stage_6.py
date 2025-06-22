import os
import config

from .reranker import run_reranking

def get_valid_batch_size() -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input("Enter the LLM batch size for Stage 6 (e.g., 10): ")
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
    STAGE5_INPUT_FILE = config.STAGE5_OUTPUT_CSV
    KB_CSV_FILE = config.STAGE4_KB_CSV
    FINAL_OUTPUT_FILE = config.STAGE6_OUTPUT_CSV
    
    batch_size = get_valid_batch_size()

    try:
        print("Running Stage 6 Reranking...")
        run_reranking(
            input_path=STAGE5_INPUT_FILE,
            kb_csv_path=KB_CSV_FILE,
            output_path=FINAL_OUTPUT_FILE,
            batch_size=batch_size
        )
        print(f"\n✅ Final predictions saved to: {FINAL_OUTPUT_FILE}")

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred during reranking: {e}")