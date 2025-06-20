# import os

# # This import still works because the function signature has not changed.
# from reranker import run_reranking
# from post_processing import run_deduplication

# def get_valid_batch_size(limit: int) -> int:
#     """Prompts the user for a batch size and validates it."""
#     while True:
#         try:
#             batch_size_str = input(f"Enter the LLM batch size for Stage 6 (1 to {limit}): ")
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
#     STAGE4_INPUT = r"..\Stage_5_Consolidation\output_files\combined_list_for_reranking.csv"
#     KNOWLEDGE_BASE_CSV = r"..\Stage_4_Concept_Mapping\output_files\icd_code_with_descriptions.csv"
#     RAW_OUTPUT = r"output_files\raw_icd_predictions.csv"
#     FINAL_OUTPUT = r"output_files\final_icd_predictions.csv"
    
#     FREE_TIER_LIMIT = 15
#     batch_size_to_run = get_valid_batch_size(limit=FREE_TIER_LIMIT)

#     try:
#         print("Running Stage 5 on the entire input file for standalone testing...")
        
#         run_reranking(
#             input_path=STAGE4_INPUT,
#             kb_csv_path=KNOWLEDGE_BASE_CSV,
#             output_path=FINAL_OUTPUT,
#             batch_size=batch_size_to_run
#         )

#         run_deduplication(
#             input_path=RAW_OUTPUT,
#             output_path=FINAL_OUTPUT
#         )

#         print("\n✅ Entire Stage 6 and Post-Processing workflow completed successfully!")
#         print(f"   Final unique predictions saved to: {FINAL_OUTPUT}")

#     except FileNotFoundError as e:
#         print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
#         print(f"   Details: {e}")
#     except Exception as e:
#         print(f"❌ An unexpected error occurred during the workflow: {e}")

import os

# Import only the reranking function
from reranker import run_reranking

def get_valid_batch_size(limit: int) -> int:
    """Prompts the user for a batch size and validates it."""
    while True:
        try:
            batch_size_str = input(f"Enter the LLM batch size for Stage 6 (1 to {limit}): ")
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
    STAGE5_OUTPUT = r"..\Stage_5_Consolidation\output_files\combined_list_for_reranking.csv"
    KNOWLEDGE_BASE = r"..\Stage_4_Concept_Mapping\output_files\icd_code_with_descriptions.csv"
    FINAL_OUTPUT = r"output_files\final_icd_predictions.csv"  # Direct final path
    
    batch_size = get_valid_batch_size(limit=15)

    try:
        print("Running Stage 6 Reranking...")
        run_reranking(
            input_path=STAGE5_OUTPUT,
            kb_csv_path=KNOWLEDGE_BASE,
            output_path=FINAL_OUTPUT,  # Writes directly here
            batch_size=batch_size
        )
        print(f"\n✅ Final predictions saved to: {FINAL_OUTPUT}")

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A required file was not found. Please check your paths.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred during reranking: {e}")