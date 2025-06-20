import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class UMLSConceptCandidateGenerator:
    """
    A candidate generator for UMLS concept mapping.
    This class loads a pre-built FAISS index and a corresponding concepts CSV
    to perform efficient semantic searches for candidate UMLS concepts.
    """
    def __init__(self, umls_csv_path: str, faiss_index_path: str, embedding_model_name='all-MiniLM-L6-v2'):
        """
        Initializes the candidate generator.

        Args:
            umls_csv_path (str): Path to the CSV file containing UMLS concepts
                                 (e.g., 'icd_code_with_descriptions.csv'). Must have 'CUI' and 'Description' columns.
            faiss_index_path (str): Path to the pre-built FAISS index file
                                    (e.g., 'umls_faiss.index').
            embedding_model_name (str): The name of the SentenceTransformer model to use.
                                        MUST be the same model used to create the index.
        """
        # --- 1. Load Required Assets ---
        print("--- Initializing Candidate Generator ---")
        try:
            # Load the mapping file to get CUI/Description from an index position.
            print(f"Loading concepts data from '{umls_csv_path}'...")
            self.umls_df = pd.read_csv(umls_csv_path)
            
            # Load the pre-computed FAISS index from disk.
            print(f"Loading FAISS index from '{faiss_index_path}'...")
            self.index = faiss.read_index(faiss_index_path)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"A required file was not found. Please check your paths. Details: {e}")
        
        # Load the sentence embedding model.
        print(f"Loading embedding model '{embedding_model_name}'...")
        self.model = SentenceTransformer(embedding_model_name)
        print("✅ Candidate Generator initialized successfully.")

    def generate_candidates(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        Generates the top-k candidate UMLS concepts for a given query text.

        Args:
            query_text (str): The normalized complaint text to search for.
            top_k (int): The number of candidate concepts to retrieve.

        Returns:
            A list of dictionaries, where each dictionary represents a candidate
            concept and contains its CUI, Description, and similarity score.
        """
        if not query_text.strip():
            return []

        # 1. Convert the query text into a vector using the same model.
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)
        
        # 2. Normalize the vector (must match the process used for building the index).
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)

        # 3. Search the FAISS index for the top_k most similar vectors.
        # This returns the similarity scores and the row indices of the matches in the original CSV.
        scores, indices = self.index.search(query_embedding, top_k)

        # 4. Retrieve the details of the matched concepts using the indices.
        candidates = []
        for i, score in zip(indices[0], scores[0]):
            # The 'i' here is the row number from the original icd_code_with_descriptions.csv
            # that corresponds to the matched vector.
            candidate_info = {
                'CUI': self.umls_df.iloc[i]['CUI'],
                'Description': self.umls_df.iloc[i]['Description'],
                'score': float(score)
            }
            candidates.append(candidate_info)
        
        return candidates

# ==============================================================================
# Example Usage: How to Use This Class in Your Main Pipeline
# ==============================================================================
if __name__ == "__main__":
    # --- Configuration ---
    icd_code_with_descriptions_CSV = r"output_files\icd_code_with_descriptions.csv"
    FAISS_INDEX_FILE = r"output_files\umls_faiss.index"

    # Check if the required files exist before trying to run.
    if not os.path.exists(icd_code_with_descriptions_CSV) or not os.path.exists(FAISS_INDEX_FILE):
        print("❌ ERROR: Required files not found.")
        print(f"Please ensure '{icd_code_with_descriptions_CSV}' and '{FAISS_INDEX_FILE}' are in the same directory.")
    else:
        # 1. Initialize the candidate generator (this loads the DB and model).
        try:
            generator = UMLSConceptCandidateGenerator(
                umls_csv_path=icd_code_with_descriptions_CSV,
                faiss_index_path=FAISS_INDEX_FILE
            )

            # 2. Use the generator to find candidates for a normalized complaint.
            normalized_complaint = "shortness of breath"
            print(f"\n--- Generating candidates for: '{normalized_complaint}' ---")
            
            candidates = generator.generate_candidates(normalized_complaint, top_k=5)

            # 3. Print the results.
            if candidates:
                print("\nTop 5 Candidates Found:")
                for cand in candidates:
                    print(f"  - CUI: {cand['CUI']}, Description: '{cand['Description']}', Score: {cand['score']:.4f}")
            else:
                print("No candidates found.")
        except Exception as e:
            print(f"An error occurred during initialization or search: {e}")