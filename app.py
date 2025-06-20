# import streamlit as st
# import pandas as pd
# import os
# import time
# import uuid
# import requests
# import json
# import zipfile
# import io

# # --- Import the main logic function from each stage ---
# from Stage_1_Complaint_Extraction.extractor import run_extracting
# from Stage_2_Normalization.normalizer import run_normalization
# from Stage_3_Complaint_Rewriting.rewriter import run_rewriting
# from Stage_4_Concept_Mapping.mapper import run_concept_mapping
# from Stage_5_Consolidation.Consolidator import run_candidate_enhancement
# from Stage_6_Reranking.reranker import run_reranking
# from Stage_1_Complaint_Extraction.extractor import deduplicate_extracted_complaints

# # --- Page Configuration ---
# st.set_page_config(
#     page_title="AEGIS: Medical Coding Assistant",
#     page_icon="🛡️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # --- Initialize Session State ---
# if 'run_completed' not in st.session_state:
#     st.session_state.run_completed = False
#     st.session_state.total_time = 0
#     st.session_state.stages_run = []
#     st.session_state.is_batch = False

# # --- Centralized Configuration ---
# CONFIG = {
#     'stage1_output': r"Stage_1_Complaint_Extraction/output_files/extracted_complaints.csv",
#     'stage2_abbreviations': r"Stage_2_Normalization/input_files/abbreviations.csv",
#     'stage2_output': r"Stage_2_Normalization/output_files/normalized_complaints.csv",
#     'stage3_output': r"Stage_3_Complaint_Rewriting/output_files/rewritten_complaints.csv",
#     'stage4_kb': r"Stage_4_Concept_Mapping/output_files/icd_code_with_descriptions.csv",
#     'stage4_faiss': r"Stage_4_Concept_Mapping/output_files/umls_faiss.index",
#     'stage4_output': r"Stage_4_Concept_Mapping/output_files/concept_mapped_complaints.csv",
#     'stage5_output': r"Stage_5_Consolidation/output_files/combined_list_for_reranking.csv",
#     'stage6_kb': r"Stage_4_Concept_Mapping/output_files/icd_code_with_descriptions.csv",
#     'stage6_raw_output': r"Stage_6_Reranking/output_files/raw_icd_predictions.csv",
#     'stage6_output': r"Stage_6_Reranking/output_files/final_icd_predictions.csv",
# }

# # --- Helper Functions ---
# def create_zip_of_outputs(files_to_zip):
#     zip_buffer = io.BytesIO()
#     with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
#         for file_path in files_to_zip:
#             if os.path.exists(file_path):
#                 zip_file.write(file_path, os.path.basename(file_path))
#     return zip_buffer.getvalue()

# def clear_existing_output_files():
#     for key, path in CONFIG.items():
#         if 'output' in key and os.path.exists(path):
#             os.remove(path)
#     print("Cleaned up existing output files.")

# def display_stage_descriptions():
#     with st.expander('ℹ️ How the AEGIS Pipeline Works (Click to learn more)'):
#         st.markdown("""
#         The AEGIS framework processes medical notes in a multi-step pipeline. Let's trace an example complaint through the stages:

#         > **Example Complaint:** *"Pt is a 45 y/o F with hx of asthma & T2DM comes in c/o fatigue x1wk."*
        
#         ---
#         ### Stage 1: Complaint Extraction
#         *   **Purpose:** To read the raw medical note and identify the core clinical complaints.
#         *   **From our example:** It intelligently pulls **"fatigue"** from the note as the primary issue.
#         ### Stage 2: Text Normalization
#         *   **Purpose:** To clean and standardize the extracted text by expanding abbreviations and correcting typos.
#         *   **From our example:** It would expand "hx" to "history" and "T2DM" to "Type 2 Diabetes Mellitus".
#         ### Stage 3: Query Rewriting
#         *   **Purpose:** To use an LLM to rephrase the complaint into multiple, clinically diverse queries.
#         *   **From our example:** "Fatigue" might be rewritten as "tiredness," "lethargy," or "lack of energy".
#         ### Stage 4: Concept Mapping
#         *   **Purpose:** To take the rewritten queries and search a medical knowledge base to find all possible matching ICD-10 codes.
#         ### Stage 5: Candidate Enhancement
#         *   **Purpose:** To consolidate the list of candidate codes, preparing it for the final decision-making step.
#         ### Stage 6: Final Selection (Reranking)
#         *   **Purpose:** To use an expert-prompted LLM to analyze the final candidates and select the single most accurate ICD-10 code along with the confidence category and their reasons.
#         ### Post-Processing: Deduplication
#         *   **Purpose:** To remove duplicate complaint-code pairs, ensuring each unique clinical scenario is represented only once.
#         """)

# # --- Main Application Logic ---
# def run_aegis_pipeline(input_file_path, stages_to_run, placeholders, progress_bar, num_to_process=None, batch_size=10):
#     total_stages_to_run = len(stages_to_run)
#     all_stages = {
#         "Stage 1: Complaint Extraction": lambda: run_extracting(input_file_path, CONFIG['stage1_output'], num_to_process, batch_size), # type: ignore
#         "Stage 2: Text Normalization": lambda: run_normalization(CONFIG['stage1_output'], CONFIG['stage2_abbreviations'], CONFIG['stage2_output'], batch_size),
#         "Stage 3: Query Rewriting": lambda: run_rewriting(CONFIG['stage2_output'], CONFIG['stage3_output'], batch_size),
#         "Stage 4: Concept Mapping": lambda: run_concept_mapping(CONFIG['stage3_output'], CONFIG['stage4_kb'], CONFIG['stage4_faiss'], CONFIG['stage4_output'], batch_size),
#         "Stage 5: Candidate Enhancement": lambda: run_candidate_enhancement(CONFIG['stage1_output'], CONFIG['stage4_output'], CONFIG['stage5_output'], batch_size),
#         "Stage 6: Final Selection": lambda: run_reranking(CONFIG['stage5_output'], CONFIG['stage6_kb'], CONFIG['stage6_raw_output'], batch_size),
#         "Post-Processing: Deduplication": lambda: run_deduplication(CONFIG['stage6_raw_output'], CONFIG['stage6_output'])
#     }
#     running_stage_name = None
#     stage_index_in_selection = 0

#     try:
#         for stage_name in stages_to_run:
#             stage_func = all_stages[stage_name]
#             running_stage_name = stage_name
#             placeholder = placeholders[stage_index_in_selection]
#             placeholder.markdown(f"⏳ {stage_name}...")
#             start = time.time()

#             # Simulate dynamic progress within each stage
#             # This is a placeholder: in real code, you should update progress based on actual work done inside stage_func
#             # For now, we simulate progress with a loop
#             for i in range(1, 101):
#                 time.sleep(0.01)  # Simulate work; replace with actual progress updates if possible
#                 progress = (stage_index_in_selection + i/100) / total_stages_to_run
#                 progress_bar.progress(progress, text=f"Overall Progress: Stage {stage_index_in_selection+1}/{total_stages_to_run} ({int(progress*100)}%)")

#             # Run the actual stage function
#             stage_func()

#             elapsed = time.time() - start
#             placeholder.markdown(f"✅ {stage_name} – {elapsed:.2f}s")
#             stage_index_in_selection += 1
#             progress_text = f"Overall Progress: Stage {stage_index_in_selection}/{total_stages_to_run} complete"
#             progress_bar.progress(stage_index_in_selection / total_stages_to_run, text=progress_text)
#     except Exception as e:
#         st.error(f"An error occurred during '{running_stage_name}': {e}")
#         if running_stage_name:
#             placeholder_to_update = placeholders[stages_to_run.index(running_stage_name)]
#             placeholder_to_update.markdown(f"❌ {running_stage_name} (Failed)")
#         progress_bar.progress(stage_index_in_selection / total_stages_to_run, text="Pipeline failed.")
#         return False
#     progress_bar.progress(1.0, text="Pipeline completed successfully!")
#     return True

# def display_results(total_time, stages_run, is_batch=False):
#     minutes = int(total_time // 60)
#     seconds = int(total_time % 60)
#     st.metric(label="Total Processing Time", value=f"{minutes}m {seconds}s")
    
#     st.subheader("Detailed Stage Outputs & Downloads")
    
#     stage_output_files_map = {
#         "Stage 1: Complaint Extraction": CONFIG['stage1_output'],
#         "Stage 2: Text Normalization": CONFIG['stage2_output'],
#         "Stage 3: Query Rewriting": CONFIG['stage3_output'],
#         "Stage 4: Concept Mapping": CONFIG['stage4_output'],
#         "Stage 5: Candidate Enhancement": CONFIG['stage5_output'],
#         "Stage 6: Final Selection": CONFIG['stage6_raw_output'],
#         "Post-Processing: Deduplication": CONFIG['stage6_output']
#     }
#     generated_files = []

#     def get_color_for_confidence(category):
#         """Maps confidence categories to specific CSS colors for styling."""
#         if category == "Very High":
#             return "background-color: #1B5E20; color: white;"
#         elif category == "High":
#             return "background-color: #2E7D32;"
#         elif category == "Medium":
#             return "background-color: #00796B;"
#         elif category == "Low":
#             return "background-color: #EF6C00;"
#         elif category == "Very Low":
#             return "background-color: #B71C1C; color: white;"
#         else:
#             return ""

#     for stage_name in stages_run:
#     # Only display the deduplicated output as Stage 6
#         if stage_name == "Stage 6: Final Selection":
#             file_path = CONFIG['stage6_output']  # Always use deduplicated output
#             if file_path and os.path.exists(file_path):
#                 generated_files.append(file_path)
#                 with st.expander(f"View Output: Stage 6 (Deduplicated Final Output)", expanded=True):
#                     df_stage = pd.read_csv(file_path)
#                     st.markdown("**Final Audited Results (with Confidence and Reasoning)**")
#                     display_columns = ['chief_complaint', 'final_predicted_icd_code', 'reasoning_icd_code', 'confidence_category', 'reasoning_confidence']
#                     available_cols = [col for col in display_columns if col in df_stage.columns]
#                     display_df = df_stage[available_cols]
#                     styled_df = display_df.style.apply(
#                         lambda x: [get_color_for_confidence(v) for v in x],
#                         subset=['confidence_category'] if 'confidence_category' in display_df.columns else []
#                     )
#                     st.dataframe(styled_df)
#                     st.download_button(
#                         label=f"Download final_icd_predictions.csv",
#                         data=df_stage.to_csv(index=False).encode('utf-8'),
#                         file_name="final_icd_predictions.csv",
#                         mime='text/csv',
#                         key="download_final_icd_predictions"
#                     )
#         elif stage_name != "Stage 6: Final Selection":
#             file_path = stage_output_files_map.get(stage_name)
#             if file_path and os.path.exists(file_path):
#                 generated_files.append(file_path)
#                 with st.expander(f"View Output: {stage_name}", expanded=False):
#                     df_stage = pd.read_csv(file_path)
#                     st.dataframe(df_stage)
#                     st.download_button(
#                         label=f"Download {os.path.basename(file_path)}",
#                         data=df_stage.to_csv(index=False).encode('utf-8'),
#                         file_name=os.path.basename(file_path),
#                         mime='text/csv',
#                         key=f"download_{stage_name.replace(' ', '_')}"
#                     )

#     if generated_files:
#         zip_data = create_zip_of_outputs(generated_files)
#         st.download_button(
#             label="📂 Download All Outputs as ZIP",
#             data=zip_data,
#             file_name="aegis_all_outputs.zip",
#             mime="application/zip",
#             type="primary"
#         )

# # --- Streamlit UI ---
# st.title("🛡️ Automated Extraction & Generative ICD code Selection")
# display_stage_descriptions()

# st.markdown("""
# <style>
#     [data-testid="stSelectbox"], [data-testid="stSidebarNavCollapseButton"] {
#         cursor: pointer;
#     }
# </style>
# """, unsafe_allow_html=True)

# # --- Sidebar Controls ---
# stage_names = [
#     "Stage 1: Complaint Extraction", "Stage 2: Text Normalization",
#     "Stage 3: Query Rewriting", "Stage 4: Concept Mapping",
#     "Stage 5: Candidate Enhancement", "Stage 6: Final Selection",
#     "Post-Processing: Deduplication"
# ]

# with st.sidebar:
#     st.title("⚙️ Controls")
#     app_mode = st.selectbox("Choose Input Mode", ("Single Complaint Analysis", "Batch File Processing"))
    
#     st.header("Pipeline Control")
    
#     # Add controls for batch size and number of records
#     num_to_process = 5
#     batch_size = 10
#     if app_mode == "Batch File Processing":
#         num_to_process = st.number_input("Number of records to process", min_value=0, value=0, step=10)
#         batch_size = st.number_input("Processing Batch Size", min_value=1, value=10, step=5)

#     st.write("Select stages to run:")
#     user_selections = {stage: st.checkbox(stage, value=True, key=f"cb_{stage}") for stage in stage_names}
#     last_selected_index = -1
#     for i in range(len(stage_names) - 1, -1, -1):
#         if user_selections[stage_names[i]]:
#             last_selected_index = i
#             break
#     if last_selected_index != -1:
#         final_stages_to_run = stage_names[:last_selected_index + 1]
#         user_clicked_stages = [stage for stage, selected in user_selections.items() if selected]
#         if set(user_clicked_stages) != set(final_stages_to_run):
#             st.warning("To maintain pipeline integrity, all stages preceding your final selection will be run automatically.")
#     else:
#         final_stages_to_run = []

# # Main application container
# main_container = st.container()

# def run_pipeline_logic(temp_filename, is_batch_mode, num_records, proc_batch_size):
#     progress_container = main_container.container()
#     with progress_container:
#         st.subheader("Pipeline Progress")
#         placeholders = [st.empty() for _ in final_stages_to_run]
#         for i, name in enumerate(final_stages_to_run):
#             placeholders[i].markdown(f"⚪ {name} (Queued)")
#         progress_bar = st.progress(0, text="Starting Pipeline...")
    
#     spinner_text = "Processing batch file..." if is_batch_mode else "AEGIS is thinking..."
#     with st.spinner(spinner_text):
#         total_start_time = time.time()
#         success = run_aegis_pipeline(temp_filename, final_stages_to_run, placeholders, progress_bar, num_to_process=num_records, batch_size=proc_batch_size)
#         total_elapsed_time = time.time() - total_start_time
#         if success:
#             st.toast('Pipeline Execution Successful!', icon='🎉')
#             st.session_state.run_completed = True
#             st.session_state.total_time = total_elapsed_time
#             st.session_state.stages_run = final_stages_to_run
#             st.session_state.is_batch = is_batch_mode
#         else:
#             st.session_state.run_completed = False
    
#     if os.path.exists(temp_filename):
#         os.remove(temp_filename)
#     st.rerun()

# # --- Single Complaint Mode ---
# if app_mode == "Single Complaint Analysis":
#     with main_container:
#         st.header("Single Complaint Analysis")
#         note_text = st.text_area("Enter Medical Note:", value="Pt is a 45 y/o F with hx of asthma & T2DM comes in c/o fatigue x1wk.", height=120)
        
#         if st.button("Run AEGIS Pipeline", type="primary", disabled=not note_text.strip() or not final_stages_to_run):
#             st.session_state.run_completed = False
            
#             temp_dir = "temp_data"; os.makedirs(temp_dir, exist_ok=True)
#             temp_filename = os.path.join(temp_dir, f"{uuid.uuid4()}.csv")
#             df = pd.DataFrame([{'Document ID': 'single_run', 'medical_record_text': note_text}])
#             df.to_csv(temp_filename, index=False)
            
#             run_pipeline_logic(temp_filename, is_batch_mode=False, num_records=None, proc_batch_size=10)

# # --- Batch File Processing Mode (with Validation) ---
# elif app_mode == "Batch File Processing":
#     with main_container:
#         st.header("Batch File Processing")
#         uploaded_file = st.file_uploader("Upload a CSV with a 'medical_record_text' column", type="csv")
        
#         if uploaded_file is not None:
#             try:
#                 df = pd.read_csv(uploaded_file)
#                 if 'medical_record_text' in df.columns:
#                     st.markdown("**File Preview:**")
#                     st.dataframe(df.head())
                    
#                     if st.button("Run AEGIS on Batch File", type="primary", disabled=not final_stages_to_run):
#                         st.session_state.run_completed = False
                        
#                         temp_dir = "temp_data"; os.makedirs(temp_dir, exist_ok=True)
#                         temp_filename = os.path.join(temp_dir, f"{uuid.uuid4()}.csv")
#                         df.to_csv(temp_filename, index=False)
                        
#                         run_pipeline_logic(temp_filename, is_batch_mode=True, num_records=num_to_process, proc_batch_size=batch_size)
#                 else:
#                     st.error("❌ Validation Error: The uploaded CSV file must contain a column named 'medical_record_text'.")
#             except Exception as e:
#                 st.error(f"An error occurred while reading the file: {e}")

# # --- Display results if they exist in session state ---
# if st.session_state.run_completed:
#     with main_container:
#         display_results(st.session_state.total_time, st.session_state.stages_run, st.session_state.is_batch)

import streamlit as st
import pandas as pd
import os
import time
import uuid
import requests
import json
import zipfile
import io

# --- Import the main logic function from each stage ---
from Stage_1_Complaint_Extraction.extractor import run_extracting
from Stage_2_Normalization.normalizer import run_normalization
from Stage_3_Complaint_Rewriting.rewriter import run_rewriting
from Stage_4_Concept_Mapping.mapper import run_concept_mapping
from Stage_5_Consolidation.Consolidator import run_candidate_enhancement
from Stage_6_Reranking.reranker import run_reranking
from Stage_1_Complaint_Extraction.extractor import deduplicate_extracted_complaints

# --- Page Configuration ---
st.set_page_config(
    page_title="AEGIS: Medical Coding Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
if 'run_completed' not in st.session_state:
    st.session_state.run_completed = False
    st.session_state.total_time = 0
    st.session_state.stages_run = []
    st.session_state.is_batch = False

# --- Centralized Configuration ---
CONFIG = {
    'stage1_output': r"Stage_1_Complaint_Extraction/output_files/extracted_complaints.csv",
    'stage1_dedup_output': r"Stage_1_Complaint_Extraction/output_files/extracted_complaints_dedup.csv",
    'stage2_input': r"Stage_1_Complaint_Extraction/output_files/extracted_complaints.csv",  # Will be updated if dedup is run
    'stage2_abbreviations': r"Stage_2_Normalization/input_files/abbreviations.csv",
    'stage2_output': r"Stage_2_Normalization/output_files/normalized_complaints.csv",
    'stage3_output': r"Stage_3_Complaint_Rewriting/output_files/rewritten_complaints.csv",
    'stage4_kb': r"Stage_4_Concept_Mapping/output_files/icd_code_with_descriptions.csv",
    'stage4_faiss': r"Stage_4_Concept_Mapping/output_files/umls_faiss.index",
    'stage4_output': r"Stage_4_Concept_Mapping/output_files/concept_mapped_complaints.csv",
    'stage5_input_s1': r"Stage_1_Complaint_Extraction/output_files/extracted_complaints.csv",  # Will be updated if dedup is run
    'stage5_input_s4': r"Stage_4_Concept_Mapping/output_files/concept_mapped_complaints.csv",
    'stage5_output': r"Stage_5_Consolidation/output_files/combined_list_for_reranking.csv",
    'stage6_kb': r"Stage_4_Concept_Mapping/output_files/icd_code_with_descriptions.csv",
    'stage6_raw_output': r"Stage_6_Reranking/output_files/raw_icd_predictions.csv",
    'stage6_output': r"Stage_6_Reranking/output_files/final_icd_predictions.csv",
}

# --- Helper Functions ---
def create_zip_of_outputs(files_to_zip):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_path in files_to_zip:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
    return zip_buffer.getvalue()

def clear_existing_output_files():
    for key, path in CONFIG.items():
        if 'output' in key and os.path.exists(path):
            os.remove(path)
    print("Cleaned up existing output files.")

def display_stage_descriptions():
    with st.expander('ℹ️ How the AEGIS Pipeline Works (Click to learn more)'):
        st.markdown("""
        The AEGIS framework processes medical notes in a multi-step pipeline. Let's trace an example complaint through the stages:

        > **Example Complaint:** *"Pt is a 45 y/o F with hx of asthma & T2DM comes in c/o fatigue x1wk."*
        
        ---
        ### Stage 1: Complaint Extraction
        *   **Purpose:** To read the raw medical note and identify the core clinical complaints.
        *   **From our example:** It intelligently pulls **"fatigue"** from the note as the primary issue.
        ### Stage 2: Text Normalization
        *   **Purpose:** To clean and standardize the extracted text by expanding abbreviations and correcting typos.
        *   **From our example:** It would expand "hx" to "history" and "T2DM" to "Type 2 Diabetes Mellitus".
        ### Stage 3: Query Rewriting
        *   **Purpose:** To use an LLM to rephrase the complaint into multiple, clinically diverse queries.
        *   **From our example:** "Fatigue" might be rewritten as "tiredness," "lethargy," or "lack of energy".
        ### Stage 4: Concept Mapping
        *   **Purpose:** To take the rewritten queries and search a medical knowledge base to find all possible matching ICD-10 codes.
        ### Stage 5: Candidate Enhancement
        *   **Purpose:** To consolidate the list of candidate codes, preparing it for the final decision-making step.
        ### Stage 6: Final Selection (Reranking)
        *   **Purpose:** To use an expert-prompted LLM to analyze the final candidates and select the single most accurate ICD-10 code along with the confidence category and their reasons.
        ### Post-Processing: Deduplication
        *   **Purpose:** To remove duplicate complaint-code pairs, ensuring each unique clinical scenario is represented only once.
        """)

# --- Main Application Logic ---
def run_aegis_pipeline(input_file_path, stages_to_run, placeholders, progress_bar, num_to_process=None, batch_size=10):
    dedup_successful = False
    for i, stage_name in enumerate(stages_to_run):
        placeholder = placeholders[i]
        placeholder.markdown(f"⏳ {stage_name}...")
        start = time.time()

        # Simulate dynamic progress within each stage
        for j in range(1, 101):
            time.sleep(0.01)  # Simulate work; replace with actual progress updates if possible
            progress = (i + j/100) / len(stages_to_run)
            progress_bar.progress(progress, text=f"Overall Progress: Stage {i+1}/{len(stages_to_run)} ({int(progress*100)}%)")

        # Run the actual stage function or deduplication
        if stage_name == "Stage 1: Complaint Extraction":
            run_extracting(input_file_path, CONFIG['stage1_output'], num_to_process, batch_size)
        elif stage_name == "Post-Processing: Deduplication":
            dedup_path = deduplicate_extracted_complaints(CONFIG['stage1_output'], CONFIG['stage1_dedup_output'])
            if dedup_path and os.path.exists(dedup_path):
                dedup_successful = True
                CONFIG['stage2_input'] = CONFIG['stage1_dedup_output']
                CONFIG['stage5_input_s1'] = CONFIG['stage1_dedup_output']
        elif stage_name == "Stage 2: Text Normalization":
            run_normalization(CONFIG['stage2_input'], CONFIG['stage2_abbreviations'], CONFIG['stage2_output'], batch_size)
        elif stage_name == "Stage 3: Query Rewriting":
            run_rewriting(CONFIG['stage2_output'], CONFIG['stage3_output'], batch_size)
        elif stage_name == "Stage 4: Concept Mapping":
            run_concept_mapping(CONFIG['stage3_output'], CONFIG['stage4_kb'], CONFIG['stage4_faiss'], CONFIG['stage4_output'], batch_size)
        elif stage_name == "Stage 5: Candidate Enhancement":
            run_candidate_enhancement(CONFIG['stage5_input_s1'], CONFIG['stage5_input_s4'], CONFIG['stage5_output'], batch_size)
        elif stage_name == "Stage 6: Final Selection":
            run_reranking(CONFIG['stage5_output'], CONFIG['stage6_kb'], CONFIG['stage6_output'], batch_size)

        elapsed = time.time() - start
        placeholder.markdown(f"✅ {stage_name} - {elapsed:.2f}s")
        progress_bar.progress((i + 1) / len(stages_to_run), text=f"Overall Progress: Stage {i+1}/{len(stages_to_run)} complete")

    progress_bar.progress(1.0, text="Pipeline completed successfully!")
    return True

def display_results(total_time, stages_run, is_batch=False):
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    st.metric(label="Total Processing Time", value=f"{minutes}m {seconds}s")
    
    st.subheader("Detailed Stage Outputs & Downloads")
    
    stage_output_files_map = {
        "Stage 1: Complaint Extraction": CONFIG['stage1_output'],
        "Stage 2: Text Normalization": CONFIG['stage2_output'],
        "Stage 3: Query Rewriting": CONFIG['stage3_output'],
        "Stage 4: Concept Mapping": CONFIG['stage4_output'],
        "Stage 5: Candidate Enhancement": CONFIG['stage5_output'],
        "Stage 6: Final Selection": CONFIG['stage6_raw_output'],
        "Post-Processing: Deduplication": CONFIG['stage1_dedup_output']
    }
    generated_files = []

    def get_color_for_confidence(category):
        """Maps confidence categories to specific CSS colors for styling."""
        if category == "Very High":
            return "background-color: #1B5E20; color: white;"
        elif category == "High":
            return "background-color: #2E7D32;"
        elif category == "Medium":
            return "background-color: #00796B;"
        elif category == "Low":
            return "background-color: #EF6C00;"
        elif category == "Very Low":
            return "background-color: #B71C1C; color: white;"
        else:
            return ""

    for stage_name in stages_run:
        # Only display the deduplicated output as Stage 1 if deduplication was run
        if stage_name == "Post-Processing: Deduplication":
            file_path = CONFIG['stage1_dedup_output']
            if file_path and os.path.exists(file_path):
                generated_files.append(file_path)
                with st.expander(f"View Output: Deduplicated Complaints", expanded=False):
                    df_stage = pd.read_csv(file_path)
                    st.dataframe(df_stage)
                    st.download_button(
                        label=f"Download extracted_complaints_dedup.csv",
                        data=df_stage.to_csv(index=False).encode('utf-8'),
                        file_name="extracted_complaints_dedup.csv",
                        mime='text/csv',
                        key="download_deduplicated_complaints"
                    )
        elif stage_name == "Stage 6: Final Selection":
            file_path = CONFIG['stage6_output']  # Always use deduplicated output as final
            if file_path and os.path.exists(file_path):
                generated_files.append(file_path)
                with st.expander(f"View Output: Stage 6 (Deduplicated Final Output)", expanded=True):
                    df_stage = pd.read_csv(file_path)
                    st.markdown("**Final Audited Results (with Confidence and Reasoning)**")
                    display_columns = ['chief_complaint', 'final_predicted_icd_code', 'reasoning_icd_code', 'confidence_category', 'reasoning_confidence']
                    available_cols = [col for col in display_columns if col in df_stage.columns]
                    display_df = df_stage[available_cols]
                    styled_df = display_df.style.apply(
                        lambda x: [get_color_for_confidence(v) for v in x],
                        subset=['confidence_category'] if 'confidence_category' in display_df.columns else []
                    )
                    st.dataframe(styled_df)
                    st.download_button(
                        label=f"Download final_icd_predictions.csv",
                        data=df_stage.to_csv(index=False).encode('utf-8'),
                        file_name="final_icd_predictions.csv",
                        mime='text/csv',
                        key="download_final_icd_predictions"
                    )
        elif stage_name != "Stage 6: Final Selection":
            file_path = stage_output_files_map.get(stage_name)
            if file_path and os.path.exists(file_path):
                generated_files.append(file_path)
                with st.expander(f"View Output: {stage_name}", expanded=False):
                    df_stage = pd.read_csv(file_path)
                    st.dataframe(df_stage)
                    st.download_button(
                        label=f"Download {os.path.basename(file_path)}",
                        data=df_stage.to_csv(index=False).encode('utf-8'),
                        file_name=os.path.basename(file_path),
                        mime='text/csv',
                        key=f"download_{stage_name.replace(' ', '_')}"
                    )

    if generated_files:
        zip_data = create_zip_of_outputs(generated_files)
        st.download_button(
            label="📂 Download All Outputs as ZIP",
            data=zip_data,
            file_name="aegis_all_outputs.zip",
            mime="application/zip",
            type="primary"
        )

# --- Streamlit UI ---
st.title("🛡️ Automated Extraction & Generative ICD code Selection")
display_stage_descriptions()

st.markdown("""
<style>
    [data-testid="stSelectbox"], [data-testid="stSidebarNavCollapseButton"] {
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
stage_names = [
    "Stage 1: Complaint Extraction",
    "Post-Processing: Deduplication",
    "Stage 2: Text Normalization",
    "Stage 3: Query Rewriting",
    "Stage 4: Concept Mapping",
    "Stage 5: Candidate Enhancement",
    "Stage 6: Final Selection"
]

with st.sidebar:
    st.title("⚙️ Controls")
    app_mode = st.selectbox("Choose Input Mode", ("Single Complaint Analysis", "Batch File Processing"))
    
    st.header("Pipeline Control")
    
    # Add controls for batch size and number of records
    num_to_process = 5
    batch_size = 10
    if app_mode == "Batch File Processing":
        num_to_process = st.number_input("Number of records to process", min_value=0, value=0, step=10)
        batch_size = st.number_input("Processing Batch Size", min_value=1, value=10, step=5)

    st.write("Select stages to run:")
    user_selections = {stage: st.checkbox(stage, value=True, key=f"cb_{stage}") for stage in stage_names}
    last_selected_index = -1
    for i in range(len(stage_names) - 1, -1, -1):
        if user_selections[stage_names[i]]:
            last_selected_index = i
            break
    if last_selected_index != -1:
        final_stages_to_run = stage_names[:last_selected_index + 1]
        user_clicked_stages = [stage for stage, selected in user_selections.items() if selected]
        if set(user_clicked_stages) != set(final_stages_to_run):
            st.warning("To maintain pipeline integrity, all stages preceding your final selection will be run automatically.")
    else:
        final_stages_to_run = []

# Main application container
main_container = st.container()

def run_pipeline_logic(temp_filename, is_batch_mode, num_records, proc_batch_size):
    progress_container = main_container.container()
    with progress_container:
        st.subheader("Pipeline Progress")
        placeholders = [st.empty() for _ in final_stages_to_run]
        for i, name in enumerate(final_stages_to_run):
            placeholders[i].markdown(f"⚪ {name} (Queued)")
        progress_bar = st.progress(0, text="Starting Pipeline...")
    
    spinner_text = "Processing batch file..." if is_batch_mode else "AEGIS is thinking..."
    with st.spinner(spinner_text):
        total_start_time = time.time()
        success = run_aegis_pipeline(temp_filename, final_stages_to_run, placeholders, progress_bar, num_to_process=num_records, batch_size=proc_batch_size)
        total_elapsed_time = time.time() - total_start_time
        if success:
            st.toast('Pipeline Execution Successful!', icon='🎉')
            st.session_state.run_completed = True
            st.session_state.total_time = total_elapsed_time
            st.session_state.stages_run = final_stages_to_run
            st.session_state.is_batch = is_batch_mode
        else:
            st.session_state.run_completed = False
    
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    st.rerun()

# --- Single Complaint Mode ---
if app_mode == "Single Complaint Analysis":
    with main_container:
        st.header("Single Complaint Analysis")
        note_text = st.text_area("Enter Medical Note:", value="Pt is a 45 y/o F with hx of asthma & T2DM comes in c/o fatigue x1wk.", height=120)
        
        if st.button("Run AEGIS Pipeline", type="primary", disabled=not note_text.strip() or not final_stages_to_run):
            st.session_state.run_completed = False
            
            temp_dir = "temp_data"; os.makedirs(temp_dir, exist_ok=True)
            temp_filename = os.path.join(temp_dir, f"{uuid.uuid4()}.csv")
            df = pd.DataFrame([{'Document ID': 'single_run', 'medical_record_text': note_text}])
            df.to_csv(temp_filename, index=False)
            
            run_pipeline_logic(temp_filename, is_batch_mode=False, num_records=None, proc_batch_size=10)

# --- Batch File Processing Mode (with Validation) ---
elif app_mode == "Batch File Processing":
    with main_container:
        st.header("Batch File Processing")
        uploaded_file = st.file_uploader("Upload a CSV with a 'medical_record_text' column", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                if 'medical_record_text' in df.columns:
                    st.markdown("**File Preview:**")
                    st.dataframe(df.head())
                    
                    if st.button("Run AEGIS on Batch File", type="primary", disabled=not final_stages_to_run):
                        st.session_state.run_completed = False
                        
                        temp_dir = "temp_data"; os.makedirs(temp_dir, exist_ok=True)
                        temp_filename = os.path.join(temp_dir, f"{uuid.uuid4()}.csv")
                        df.to_csv(temp_filename, index=False)
                        
                        run_pipeline_logic(temp_filename, is_batch_mode=True, num_records=num_to_process, proc_batch_size=batch_size)
                else:
                    st.error("❌ Validation Error: The uploaded CSV file must contain a column named 'medical_record_text'.")
            except Exception as e:
                st.error(f"An error occurred while reading the file: {e}")

# --- Display results if they exist in session state ---
if st.session_state.run_completed:
    with main_container:
        display_results(st.session_state.total_time, st.session_state.stages_run, st.session_state.is_batch)