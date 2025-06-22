import os

# --- BASE DIRECTORY ---
# Defines the absolute path of the project's root directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- GLOBAL MODEL CONFIGURATION ---
# Set the correct model name, used across all stages.
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# --- STAGE-SPECIFIC API KEYS ---
# Key for Stage 1
STAGE_1_GEMINI_API_KEY = os.environ.get("STAGE_1_API_KEY")
# kEY for Stage 2
STAGE_2_GEMINI_API_KEY = os.environ.get("STAGE_2_API_KEY")
# Key for Stage 3
STAGE_3_GEMINI_API_KEY = os.environ.get("STAGE_3_API_KEY")
# Key for Stage 4
STAGE_4_GEMINI_API_KEY = os.environ.get("STAGE_4_API_KEY")
# Key for Stage 5
STAGE_5_GEMINI_API_KEY = os.environ.get("STAGE_5_API_KEY")
# Key for Stage 6
STAGE_6_GEMINI_API_KEY = os.environ.get("STAGE_6_API_KEY")

# --- GLOBAL SETTINGS ---
DEFAULT_DELAY_BETWEEN_BATCHES = 10 # Seconds

# --- TEMPORARY FILE PATHS ---
TEMP_DATA_DIR = os.path.join(BASE_DIR, "temp_data")
TEMP_JSON_DICT_PATH = os.path.join(TEMP_DATA_DIR, "temp_abbreviations_for_spacy.json")

# --- FILE PATHS ---
# Stage 1: Complaint Extraction
STAGE1_DIR = os.path.join(BASE_DIR, "Stage_1_Complaint_Extraction")
STAGE1_INPUT_DIR = os.path.join(STAGE1_DIR, "input_files")
STAGE1_OUTPUT_DIR = os.path.join(STAGE1_DIR, "output_files")
STAGE1_INPUT_CSV = os.path.join(STAGE1_INPUT_DIR, "text.csv")
STAGE1_RAW_OUTPUT_CSV = os.path.join(STAGE1_OUTPUT_DIR, "extracted_complaints.csv")
STAGE1_DEDUP_OUTPUT_CSV = os.path.join(STAGE1_OUTPUT_DIR, "extracted_complaints_dedup.csv")

# Stage 2: Normalization
STAGE2_DIR = os.path.join(BASE_DIR, "Stage_2_Normalization")
STAGE2_INPUT_DIR = os.path.join(STAGE2_DIR, "input_files")
STAGE2_OUTPUT_DIR = os.path.join(STAGE2_DIR, "output_files")
STAGE2_ABBREVIATIONS_CSV = os.path.join(STAGE2_INPUT_DIR, "abbreviations.csv")
STAGE2_OUTPUT_CSV = os.path.join(STAGE2_OUTPUT_DIR, "normalized_complaints.csv")

# Stage 3: Complaint Rewriting
STAGE3_DIR = os.path.join(BASE_DIR, "Stage_3_Complaint_Rewriting")
STAGE3_OUTPUT_DIR = os.path.join(STAGE3_DIR, "output_files")
STAGE3_OUTPUT_CSV = os.path.join(STAGE3_OUTPUT_DIR, "rewritten_complaints.csv")

# Stage 4: Concept Mapping
STAGE4_DIR = os.path.join(BASE_DIR, "Stage_4_Concept_Mapping")
STAGE4_INPUT_DIR = os.path.join(STAGE4_DIR, "input_files")
STAGE4_OUTPUT_DIR = os.path.join(STAGE4_DIR, "output_files")
STAGE4_KB_CSV = os.path.join(STAGE4_OUTPUT_DIR, "icd_code_with_descriptions.csv")
STAGE4_FAISS_INDEX = os.path.join(STAGE4_OUTPUT_DIR, "umls_faiss.index")
STAGE4_OUTPUT_CSV = os.path.join(STAGE4_OUTPUT_DIR, "concept_mapped_complaints.csv")

# Stage 5: Consolidation
STAGE5_DIR = os.path.join(BASE_DIR, "Stage_5_Consolidation")
STAGE5_OUTPUT_DIR = os.path.join(STAGE5_DIR, "output_files")
STAGE5_OUTPUT_CSV = os.path.join(STAGE5_OUTPUT_DIR, "combined_list_for_reranking.csv")

# Stage 6: Reranking
STAGE6_DIR = os.path.join(BASE_DIR, "Stage_6_Reranking")
STAGE6_OUTPUT_DIR = os.path.join(STAGE6_DIR, "output_files")
STAGE6_OUTPUT_CSV = os.path.join(STAGE6_OUTPUT_DIR, "final_icd_predictions.csv")