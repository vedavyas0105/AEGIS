from rewriter import run_rewriting

def get_valid_batch_size(limit: int) -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input(f"Enter the LLM batch size for Stage 3 (1 to {limit}): ")
            batch_size = int(batch_size_str)
            if 1 <= batch_size <= limit:
                return batch_size
            else:
                print(f"Error: Batch size must be between 1 and {limit}.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

if __name__ == "__main__":
    INPUT_FILE = r"..\Stage_2_Normalization\output_files\normalized_complaints.csv"
    OUTPUT_FILE = r"output_files\rewritten_complaints.csv"

    # --- Get User Input for Direct Execution ---
    FREE_TIER_LIMIT = 15
    batch_size_to_run = get_valid_batch_size(limit=FREE_TIER_LIMIT)
    
    try:
        print("Running Stage 3 (Query Rewriting) for standalone testing...")
        run_rewriting(input_path=INPUT_FILE, output_path=OUTPUT_FILE, batch_size=batch_size_to_run)
    except Exception as e:
        print(f"An error occurred: {e}")