import streamlit as st
import pandas as pd
import os
import time
import uuid
import zipfile
import io
import config 

# --- Import the main logic function from each stage ---
# FIX: Ensure all function names match their definitions
from Stage_1_Complaint_Extraction.extractor import run_extracting, deduplicate_extracted_complaints
from Stage_2_Normalization.normalizer import run_normalization
from Stage_3_Complaint_Rewriting.rewriter import run_rewriting
from Stage_4_Concept_Mapping.mapper import run_concept_mapping
from Stage_5_Consolidation.Consolidator import run_candidate_enhancement
from Stage_6_Reranking.reranker import run_reranking

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

# --- Helper Functions ---
def create_zip_of_outputs(files_to_zip):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_path in files_to_zip:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
    return zip_buffer.getvalue()

def clear_existing_output_files():
    # FIX: Use the config module to find and clear output files
    paths_to_clear = [
        config.STAGE1_RAW_OUTPUT_CSV, config.STAGE1_DEDUP_OUTPUT_CSV,
        config.STAGE2_OUTPUT_CSV, config.STAGE3_OUTPUT_CSV,
        config.STAGE4_OUTPUT_CSV, config.STAGE5_OUTPUT_CSV,
        config.STAGE6_OUTPUT_CSV
    ]
    for path in paths_to_clear:
        if os.path.exists(path):
            os.remove(path)
    print("Cleaned up existing output files.")

def display_stage_descriptions():
    with st.expander('ℹ️ How the AEGIS Pipeline Works (Click to learn more)'):
        # This section remains unchanged
        st.markdown("""
        The AEGIS framework processes medical notes in a multi-step pipeline...
        """)

# --- Main Application Logic ---
# FIX: The pipeline logic is refactored to use config.py and local variables for data flow
def run_aegis_pipeline(input_file_path, stages_to_run, placeholders, progress_bar, num_to_process=None, batch_size=10):
    total_stages = len(stages_to_run)
    current_stage_idx = 0
    running_stage_name = ""

    # Determine if deduplication is part of the run
    dedup_is_selected = "Post-Processing: Deduplication" in stages_to_run
    
    # This variable tracks the output of Stage 1
    stage1_final_output = config.STAGE1_DEDUP_OUTPUT_CSV if dedup_is_selected else config.STAGE1_RAW_OUTPUT_CSV

    try:
        for stage_name in stages_to_run:
            running_stage_name = stage_name
            placeholder = placeholders[current_stage_idx]
            placeholder.markdown(f"⏳ {stage_name}...")
            start_time = time.time()

            # --- Execute Stage Logic ---
            if stage_name == "Stage 1: Complaint Extraction":
                run_extracting(input_file_path, config.STAGE1_RAW_OUTPUT_CSV, num_to_process, batch_size) # type: ignore
            
            elif stage_name == "Post-Processing: Deduplication":
                deduplicate_extracted_complaints(config.STAGE1_RAW_OUTPUT_CSV, config.STAGE1_DEDUP_OUTPUT_CSV)

            elif stage_name == "Stage 2: Text Normalization":
                run_normalization(stage1_final_output, config.STAGE2_ABBREVIATIONS_CSV, config.STAGE2_OUTPUT_CSV, batch_size)

            elif stage_name == "Stage 3: Query Rewriting":
                run_rewriting(config.STAGE2_OUTPUT_CSV, config.STAGE3_OUTPUT_CSV, batch_size)

            elif stage_name == "Stage 4: Concept Mapping":
                run_concept_mapping(config.STAGE3_OUTPUT_CSV, config.STAGE4_KB_CSV, config.STAGE4_FAISS_INDEX, config.STAGE4_OUTPUT_CSV, batch_size)

            elif stage_name == "Stage 5: Candidate Enhancement":
                run_candidate_enhancement(stage1_final_output, config.STAGE4_OUTPUT_CSV, config.STAGE5_OUTPUT_CSV, batch_size)

            elif stage_name == "Stage 6: Final Selection":
                run_reranking(config.STAGE5_OUTPUT_CSV, config.STAGE4_KB_CSV, config.STAGE6_OUTPUT_CSV, batch_size)

            elapsed_time = time.time() - start_time
            placeholder.markdown(f"✅ {stage_name} – {elapsed_time:.2f}s")
            current_stage_idx += 1
            progress_bar.progress(current_stage_idx / total_stages, text=f"Overall Progress: Stage {current_stage_idx}/{total_stages} complete")

    except Exception as e:
        st.error(f"An error occurred during '{running_stage_name}': {e}")
        if running_stage_name:
            placeholders[stages_to_run.index(running_stage_name)].markdown(f"❌ {running_stage_name} (Failed)")
        progress_bar.progress(current_stage_idx / total_stages, text="Pipeline failed.")
        return False
    
    progress_bar.progress(1.0, text="Pipeline completed successfully!")
    return True

# --- Results Display ---
# FIX: This function is updated to use the config.py module for file paths
def display_results(total_time, stages_run, is_batch=False):
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    st.metric(label="Total Processing Time", value=f"{minutes}m {seconds}s")
    
    st.subheader("Detailed Stage Outputs & Downloads")
    
    stage_output_files_map = {
        "Stage 1: Complaint Extraction": config.STAGE1_RAW_OUTPUT_CSV,
        "Post-Processing: Deduplication": config.STAGE1_DEDUP_OUTPUT_CSV,
        "Stage 2: Text Normalization": config.STAGE2_OUTPUT_CSV,
        "Stage 3: Query Rewriting": config.STAGE3_OUTPUT_CSV,
        "Stage 4: Concept Mapping": config.STAGE4_OUTPUT_CSV,
        "Stage 5: Candidate Enhancement": config.STAGE5_OUTPUT_CSV,
        "Stage 6: Final Selection": config.STAGE6_OUTPUT_CSV,
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
        file_path = stage_output_files_map.get(stage_name)
        if file_path and os.path.exists(file_path):
            generated_files.append(file_path)
            with st.expander(f"View Output: {stage_name}", expanded=(stage_name == "Stage 6: Final Selection")):
                df_stage = pd.read_csv(file_path)
                
                if stage_name == "Stage 6: Final Selection":
                    st.markdown("**Final Audited Results (with Confidence and Reasoning)**")
                    display_columns = ['chief_complaint', 'final_predicted_icd_code', 'reasoning_icd_code', 'confidence_category', 'reasoning_confidence']
                    available_cols = [col for col in display_columns if col in df_stage.columns]
                    st.dataframe(df_stage[available_cols]) # Simplified styling for clarity
                else:
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
# FIX: Stage names updated for clarity (Deduplication is now separate)
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
    
    num_to_process = None
    batch_size = 10
    if app_mode == "Batch File Processing":
        num_to_process = st.number_input("Number of records to process (0 for all)", min_value=0, value=0, step=10)
        batch_size = st.number_input("Processing Batch Size", min_value=1, value=10, step=5)

    st.write("Select stages to run:")
    user_selections = {stage: st.checkbox(stage, value=True, key=f"cb_{stage}") for stage in stage_names}
    last_selected_index = -1
    for i in range(len(stage_names) - 1, -1, -1):
        if user_selections[stage_names[i]]:
            last_selected_index = i
            break
    
    final_stages_to_run = []
    if last_selected_index != -1:
        final_stages_to_run = [stage for i, stage in enumerate(stage_names) if i <= last_selected_index]
        if not user_selections["Post-Processing: Deduplication"] and "Post-Processing: Deduplication" in final_stages_to_run:
            final_stages_to_run.remove("Post-Processing: Deduplication")

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
            clear_existing_output_files() # Clear old files before a run
            
            temp_dir = "temp_data"; os.makedirs(temp_dir, exist_ok=True)
            temp_filename = os.path.join(temp_dir, f"{uuid.uuid4()}.csv")
            df = pd.DataFrame([{'Document ID': 'single_run', 'medical_record_text': note_text}])
            df.to_csv(temp_filename, index=False)
            
            run_pipeline_logic(temp_filename, is_batch_mode=False, num_records=1, proc_batch_size=1)

# --- Batch File Processing Mode ---
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

if st.session_state.run_completed:
    with main_container:
        display_results(st.session_state.total_time, st.session_state.stages_run, st.session_state.is_batch)