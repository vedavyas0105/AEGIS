import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

def create_vector_database(concepts_csv_path: str, output_index_path: str):
    """
    Creates a FAISS vector database from the descriptions in a concepts CSV file.

    This function performs a one-time setup:
    1. Loads concept descriptions from the CSV.
    2. Encodes them into numerical vectors using a sentence-transformer model.
    3. Builds a FAISS index for efficient similarity searching.
    4. Saves the index to disk for future use.

    Args:
        concepts_csv_path (str): Path to the input CSV file (e.g., 'icd_code_with_descriptions.csv').
                                 Must contain a 'Description' column.
        output_index_path (str): Path to save the final FAISS index file to.
    """
    print("--- Starting Vector Database Creation ---")

    # --- 1. Load the Concepts Data ---
    try:
        print(f"Loading concepts from '{concepts_csv_path}'...")
        df = pd.read_csv(concepts_csv_path)
        if 'Description' not in df.columns:
            raise ValueError("CSV file must contain a 'Description' column.")
        # Ensure descriptions are strings and handle potential missing values
        descriptions = df['Description'].fillna('').astype(str).tolist()
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at '{concepts_csv_path}'.")
        return

    # --- 2. Load the Embedding Model ---
    model_name = 'all-MiniLM-L6-v2'
    print(f"Loading sentence-transformer model '{model_name}'... (This may download the model on first run)")
    model = SentenceTransformer(model_name)

    # --- 3. Encode Descriptions into Vectors ---
    print(f"Encoding {len(descriptions)} descriptions into vectors... (This may take some time)")
    # The model converts each description string into a numerical vector
    embeddings = model.encode(descriptions, show_progress_bar=True, convert_to_numpy=True)
    
    # Ensure embeddings are in float32 format, as required by FAISS
    embeddings = np.array(embeddings).astype('float32')

    # --- 4. Build and Save the FAISS Index ---
    print("Building the FAISS index...")
    # Get the dimension of the vectors (e.g., 384 for all-MiniLM-L6-v2)
    embedding_dimension = embeddings.shape[1]
    
    # We use IndexFlatIP because it's efficient for cosine similarity with normalized vectors
    index = faiss.IndexFlatIP(embedding_dimension)
    
    # Normalize the vectors (this is crucial for using cosine similarity with IndexFlatIP)
    faiss.normalize_L2(embeddings)

    # Add all the vectors to the index
    index.add(embeddings) # type: ignore
    
    print(f"FAISS index built successfully with {index.ntotal} vectors.")

    # Save the completed index to a file for later use
    faiss.write_index(index, output_index_path)
    print(f"✅ Vector database saved to '{output_index_path}'.")


# ==============================================================================
# Main Execution Block
# ==============================================================================
if __name__ == "__main__":
    INPUT_CONCEPTS_CSV = r"output_files\icd_code_with_descriptions.csv"
    
    # The name of the output file that will be your vector DB
    OUTPUT_FAISS_INDEX = r"output_files\umls_faiss.index"
    
    # --- Run the creation process ---
    create_vector_database(INPUT_CONCEPTS_CSV, OUTPUT_FAISS_INDEX)