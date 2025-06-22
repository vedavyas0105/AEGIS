import config
from .rewriter import run_rewriting

def get_valid_batch_size() -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input("Enter the LLM batch size for Stage 3 (e.g., 10): ")
            batch_size = int(batch_size_str)
            if batch_size > 0:
                return batch_size
            else:
                print("Error: Batch size must be a positive number.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

if __name__ == "__main__":
    INPUT_FILE = config.STAGE2_OUTPUT_CSV
    OUTPUT_FILE = config.STAGE3_OUTPUT_CSV

    # --- Get User Input for Direct Execution ---
    batch_size_to_run = get_valid_batch_size()
    
    try:
        print("Running Stage 3 (Query Rewriting) for standalone testing...")
        run_rewriting(input_path=INPUT_FILE, output_path=OUTPUT_FILE, batch_size=batch_size_to_run)
    except Exception as e:
        print(f"An error occurred: {e}")