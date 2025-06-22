from .Consolidator import run_candidate_enhancement
import config

if __name__ == "__main__":
    # --- Configuration for Direct Execution (from config.py) ---
    # This stage requires two inputs:
    # 1. The original context from Stage 1 (deduplicated)
    # 2. The mapped candidates from Stage 4
    STAGE1_INPUT_FILE = config.STAGE1_DEDUP_OUTPUT_CSV
    STAGE4_INPUT_FILE = config.STAGE4_OUTPUT_CSV
    FINAL_OUTPUT_FILE = config.STAGE5_OUTPUT_CSV
    
    try:
        # --- Get User Input for Direct Execution ---
        while True:
            try:
                batch_str = input(f"Enter the LLM batch size for Stage 5 (e.g., 10): ")
                llmbatchsize = int(batch_str)
                if llmbatchsize > 0:
                    break
                else:
                    print("Batch size must be a positive number.")
            except ValueError:
                print("Invalid input. Please enter a whole number.")

        print("\n--- Running Stage 5: Candidate Consolidation (Standalone) ---")
        
        # --- Call the main logic function ---
        # FIX: The function call now uses the correct name 'run_candidate_enhancement'
        run_candidate_enhancement(
            stage1_path=STAGE1_INPUT_FILE,
            stage4_path=STAGE4_INPUT_FILE,
            output_path=FINAL_OUTPUT_FILE,
            batch_size=llmbatchsize
        )
        
        print(f"\n🎉 Stage 5 Complete! Results saved to '{FINAL_OUTPUT_FILE}'")

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")