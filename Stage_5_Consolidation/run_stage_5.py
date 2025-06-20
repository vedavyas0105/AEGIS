# from Consolidator import run_candidate_enhancement

# def get_valid_batch_size(limit: int) -> int:
#     """Prompts the user for a batch size and validates it."""
#     while True:
#         try:
#             batch_size_str = input(f"Enter the LLM batch size for Stage 5 (1 to {limit}): ")
#             batch_size = int(batch_size_str)
#             if 1 <= batch_size <= limit:
#                 return batch_size
#             else:
#                 print(f"Error: Batch size must be between 1 and {limit}.")
#         except ValueError:
#             print("Invalid input. Please enter a whole number.")

# # ==============================================================================
# # This block allows the script to be run directly for individual testing.
# # ==============================================================================
# if __name__ == "__main__":
#     # --- Configuration for Direct Execution ---
#     STAGE1_INPUT = r"..\Stage_1_Complaint_Extraction\output_files\extracted_complaints.csv"
#     STAGE3_INPUT = r"..\Stage_4_Concept_Mapping\output_files\concept_mapped_complaints.csv"
#     STAGE4_OUTPUT = r"output_files\combined_list_for_reranking.csv"
#     OUTPUT_PATH = r'output_files\combined_list_for_reranking.csv'

#     FREE_TIER_LIMIT = 15
#     batch_size_to_run = get_valid_batch_size(limit=FREE_TIER_LIMIT)

#     try:
#         # --- Get User Input for Direct Execution ---
#         batch_size_to_run = int(input("Enter the LLM batch size for Stage 4 (e.g., 15): "))
        
#         print("Running Enhanced Stage 4 for standalone testing...")
        
#         # --- Call the main logic function ---
#         run_candidate_enhancement(
#             stage1_path=STAGE1_INPUT,
#             stage4_path=STAGE4_OUTPUT,
#             output_path=OUTPUT_PATH,
#             batch_size=batch_size_to_run
#         )

#     except Exception as e:
#         print(f"\n❌ An unexpected error occurred: {e}")

# run_stage_5.py
import os

# Import only the function that belongs to Stage 5
from Consolidator import run_candidate_enhancement

# ==============================================================================
# This block allows the script to be run directly for individual testing.
# ==============================================================================
if __name__ == "__main__":
    # --- Configuration for Direct Execution ---
    # Define the inputs that Stage 5 actually needs
    STAGE1_INPUT_FOR_CONTEXT = r"..\Stage_1_Complaint_Extraction\output_files\extracted_complaints.csv"
    STAGE4_INPUT_FOR_CANDIDATES = r"..\Stage_4_Concept_Mapping\output_files\concept_mapped_complaints.csv"
    
    # Define the final output path for Stage 5
    FINAL_OUTPUT = r"output_files\combined_list_for_reranking.csv"

    try:
        # --- NEW: A single, clear prompt for the Stage 5 batch size ---
        batch_str = input(f"Enter the LLM batch size for Stage 5 (e.g., 10): ")
        llm_batch_size = int(batch_str)

        print("\n--- Running Stage 5 for standalone testing... ---")
        
        # Call the Stage 5 function with its required inputs
        run_candidate_enhancement(
            stage1_path=STAGE1_INPUT_FOR_CONTEXT,
            stage4_path=STAGE4_INPUT_FOR_CANDIDATES,
            output_path=FINAL_OUTPUT,
            batch_size=llm_batch_size
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ ERROR: An error occurred. Please check your paths and input.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")