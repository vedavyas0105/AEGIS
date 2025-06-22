# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyAGcLSC7CrmPCN8cfPnBM6doX0jbvcZrII"
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Processing Settings
DEFAULT_BATCH_SIZE = 5
DEFAULT_DELAY = 5  # seconds between LLM batches

# File Paths
INPUT_FILE_PATH = "input_files/text.csv"
RAW_OUTPUT_PATH = "output_files/extracted_complaints.csv"
DEDUP_OUTPUT_PATH = "output_files/extracted_complaints_dedup.csv"
ERROR_LOG_DIR = "llm_error_logs"