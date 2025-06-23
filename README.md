# 🛡️ AEGIS: Automated Extraction & Generative ICD code Selection

AEGIS is a sophisticated 6-stage pipeline designed to automate the process of assigning ICD-10 codes from unstructured clinical notes. It leverages a series of Large Language Models (LLMs) and rule-based systems to mimic the workflow of a human medical coding auditor, moving from raw text to a final, justified code selection with a confidence score.

## ✨ Features

- **Multi-Stage Architecture:** Breaks down the complex task of medical coding into six logical, auditable stages.
- **Hybrid AI Approach:** Combines the contextual power of LLMs with fast, reliable rule-based systems and vector search.
- **Flexible Execution:** Run the entire pipeline, a specific range of stages, or a single stage for isolated testing.
- **Multiple Interfaces:** Interact with the pipeline via a command-line interface (`main.py`) or a user-friendly web application (`app.py`).
- **Detailed Auditing:** The final output includes not just the predicted code, but also the LLM's reasoning and confidence level, providing full transparency.

## 📂 Project Structure

The project is organized into distinct directories for each stage, promoting modularity and maintainability.

```
AEGIS/
├── Stage_1_Complaint_Extraction/
│   ├── input/              # Raw clinical text files or CSVs
│   ├── output/             # Extracted chief complaints
│   ├── __init__.py
│   ├── extractor.py
│   └── run_stage_1.py
├── Stage_2_Normalization/
│   ├── input/              # Output from Stage 1
│   ├── output/             # Normalized complaints
│   ├── __init__.py
│   ├── normalizer.py
│   └── run_stage_2.py
├── Stage_3_Complaint_Rewriting/
│   ├── input/              # Output from Stage 2
│   ├── output/             # Rewritten standardized complaints
│   ├── __init__.py
│   ├── rewriter.py
│   └── run_stage_3.py
├── Stage_4_Concept_Mapping/
│   ├── input/              # Output from Stage 3
│   ├── output/             # ICD concept candidates or CUIs
│   ├── __init__.py
│   ├── mapper.py
│   └── run_stage_4.py
├── Stage_5_Consolidation/
│   ├── input/              # Mapped concepts and context info
│   ├── output/             # Consolidated ICD predictions
│   ├── __init__.py
│   ├── Consolidator.py
│   └── run_stage_5.py
├── Stage_6_Reranking/
│   ├── input/              # Consolidated ICD codes and metadata
│   ├── output/             # Final ranked ICD codes
│   ├── __init__.py
│   ├── reranker.py
│   └── run_stage_6.py
├── app.py                  # Streamlit Web Application
├── main.py                 # Main CLI Orchestrator
├── config.py               # Centralized Configuration
└── requirements.txt        # Project Dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Access to the Google Gemini API.

### 1. Setup

**Clone the repository:**

```
git clone 
cd AEGIS
```

**Install dependencies:**  
Create a virtual environment and install the required packages.

```
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. Configuration

All project configuration, including API keys and file paths, is managed in `config.py`.

**API Keys:**  
The pipeline requires separate Gemini API keys for each stage. It is **highly recommended** to set these as environment variables for security.

```
# Example for Linux/macOS
export STAGE_1_API_KEY="your_api_key_for_stage_1"
export STAGE_2_API_KEY="your_api_key_for_stage_2"
# ... and so on for all 6 stages
```

The `config.py` file will automatically read these environment variables.

## ⚙️ How to Run the Pipeline

You can run the AEGIS pipeline in several ways, depending on your needs.

### 1. Main CLI Orchestrator (`main.py`)

This is the primary method for running the pipeline on datasets.

```
python main.py
```

The script will guide you through the following options:

- **Input Mode:**
  - `1. Batch Mode`: Process a CSV file.
  - `2. Single Complaint Mode`: Process a single piece of text entered in the terminal.
- **Stage Selection (Batch Mode Only):**
  - You can specify a `start stage` and `end stage` to run the entire pipeline or just a specific part of it.
  - To run a **single stage**, enter the same number for both start and end (e.g., Start: 4, End: 4).
  - The script will check for prerequisite files if you start from a stage greater than 1.

### 2. Standalone Stage Runners (`run_stage_*.py`)

Each stage has its own runner script for isolated testing and debugging. This is useful for developing a single stage without running the entire pipeline.

**Example: To test only Stage 2:**

```
# Run from the root AEGIS/ directory
python -m Stage_2_Normalization.run_stage_2
```

### 3. Streamlit Web Application (`app.py`)

For an interactive, graphical interface, use the Streamlit app.

```
streamlit run app.py
```

This will launch a web app in your browser where you can enter a single complaint or upload a batch file and see the results in real-time.

---

## 🔬 Pipeline Stages Explained

The AEGIS framework processes medical notes through a six-stage pipeline.

### Stage 1: Complaint Extraction

- **Goal:** To identify and extract the primary clinical "chief complaint" from a potentially long and unstructured medical note.
- **Process:** An LLM reads the raw text and is prompted to pull out the single, most important patient complaint (e.g., "headache," "shortness of breath," "fall with injury").
- **Substage (Optional):** Deduplication can be run to remove identical complaints from the batch, reducing redundant processing in later stages.
- **Input:** Raw `medical_record_text` from a CSV.
- **Output:** `extracted_complaints.csv` (and optionally `extracted_complaints_dedup.csv`).

### Stage 2: Text Normalization

- **Goal:** To clean the extracted complaint, expanding common medical abbreviations and correcting typos.
- **Process:** This stage uses a two-pass approach for both speed and accuracy.
  - **Pass 1 (Dictionary Expansion):** A fast, rule-based pass uses a custom `abbreviations.csv` file to expand common, unambiguous shorthand (e.g., "c/o" -> "complains of", "hx" -> "history of").
  - **Pass 2 (Contextual LLM Expansion):** For remaining or ambiguous abbreviations, an LLM analyzes the term in its clinical context to determine the correct expansion.
- **Input:** `extracted_complaints_dedup.csv`.
- **Output:** `complaints_normalized.csv`.

### Stage 3: Query Rewriting

- **Goal:** To transform the normalized clinical phrase into a clean, well-formed query suitable for a semantic search engine.
- **Process:** An LLM rephrases the text to be more explicit. For example, "headache x1wk" becomes "Patient complains of headache for one week." This improves the accuracy of the vector search in the next stage.
- **Input:** `complaints_normalized.csv`.
- **Output:** `complaints_rewritten.csv`.

### Stage 4: Concept Mapping (Candidate Generation)

- **Goal:** To generate a broad list of potential ICD-10 code candidates that are semantically related to the rewritten query.
- **Process:**
  - **Vector Search:** The rewritten query is embedded into a vector and searched against a pre-built FAISS index of ICD-10 code descriptions.
  - **Candidate Retrieval:** The system retrieves the top N most similar ICD-10 codes from the knowledge base (`codewithdescriptions.csv`) to serve as an initial candidate list.
- **Input:** `complaints_rewritten.csv`.
- **Output:** `mappedcomplaints.csv`, which includes the complaint and a list of potential ICD codes.

### Stage 5: Candidate Enhancement & Consolidation

- **Goal:** To refine the candidate list by re-introducing the full context of the original medical note and adding any obvious codes that the vector search may have missed.
- **Process:** This stage looks at the initial candidate list from Stage 4 alongside the original text from Stage 1. It uses an LLM to "double-check" the work, confirming if the candidates make sense in the full context or suggesting new ones if necessary.
- **Input:** `mappedcomplaints.csv` (from Stage 4) and `extracted_complaints_dedup.csv` (from Stage 1).
- **Output:** `list_for_reranking.csv`, containing a final, context-aware list of candidate codes.

### Stage 6: Final Selection (Reranking & Auditing)

- **Goal:** To act as the final "human auditor," selecting the single best ICD-10 code and providing a justification and a confidence score.
- **Process:** This stage uses a powerful two-step logic.
  - **Substage 1 (Rules Engine):** A deterministic rules engine applies hardcoded clinical logic to filter the candidate list. This includes specificity rules (e.g., prefer `I25.110` over `I25.1`) and category rules (e.g., a "rash" complaint should map to an "L" code).
  - **Substage 2 (LLM Reranker):** The final, filtered candidates are passed to a highly specialized LLM prompt. The LLM is instructed to act as a **Lead Coding Auditor**, weighing the candidates against coding guidelines (like diagnosis precedence over symptoms) to select the single best code, write a justification for its choice, and assign a confidence level (from "Very High" to "Very Low").
- **Input:** `list_for_reranking.csv`.
- **Output:** `icd_predictions.csv`, the final, auditable result of the entire pipeline.
