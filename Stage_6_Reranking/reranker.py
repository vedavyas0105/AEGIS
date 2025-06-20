# # # # import pandas as pd
# # # # import google.generativeai as genai
# # # # import time
# # # # import ast
# # # # import os
# # # # import re
# # # # from collections import Counter
# # # # from .clinical_defaults import COMMON_DEFAULTS_MAP

# # # # # --- ARCHITECTURAL UPGRADE 1: A DETERMINISTIC RULES ENGINE ---
# # # # class RulesEngine:
# # # #     """
# # # #     A deterministic engine to apply hard-coded clinical coding rules before
# # # #     escalating to a probabilistic LLM.
# # # #     """
    
# # # #     # --- THE FIX IS HERE: Add the __init__ constructor ---
# # # #     def __init__(self, defaults_map: dict):
# # # #         """Initializes the engine with the map of common default codes."""
# # # #         self.COMMON_DEFAULTS = defaults_map
# # # #         self.icd_map = {}

# # # #     def _filter_by_specificity(self, codes: list) -> list:
# # # #         """Removes less specific parent codes when a more specific child code exists."""
# # # #         if not codes or len(codes) <= 1:
# # # #             return codes
        
# # # #         codes_set = set(codes)
# # # #         to_remove = {c2 for c1 in codes_set for c2 in codes_set if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
# # # #         return [code for code in codes if code not in to_remove]

# # # #     def _filter_by_category(self, complaint: str, codes: list) -> list:
# # # #         """Removes codes from clinically inappropriate categories."""
# # # #         complaint_lower = complaint.lower()
# # # #         if "rash" in complaint_lower or "pruritic" in complaint_lower:
# # # #             return [code for code in codes if code.startswith('L') or code.startswith('R')]
# # # #         if "fall" in complaint_lower or "injury" in complaint_lower:
# # # #             return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
# # # #         return codes

# # # #     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
# # # #         """Checks if a common default code can be applied."""
# # # #         complaint_lower = complaint.lower().strip()
        
# # # #         if complaint_lower in self.COMMON_DEFAULTS:
# # # #             default_code = self.COMMON_DEFAULTS[complaint_lower]
# # # #             if default_code in codes:
# # # #                 return [default_code]
        
# # # #         for key, default_code in self.COMMON_DEFAULTS.items():
# # # #             if key in complaint_lower and default_code in codes:
# # # #                 return [default_code]
        
# # # #         return codes

# # # #     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
# # # #         """
# # # #         Runs the full sequence of rule-based filters in the correct, safer order.
# # # #         """
# # # #         if not candidates: return []
        
# # # #         self.icd_map = icd_map
        
# # # #         # Step 1: Filter by clinical category first to remove nonsensical options.
# # # #         filtered_codes = self._filter_by_category(complaint, candidates)
        
# # # #         # Step 2: Apply the crucial specificity filter.
# # # #         filtered_codes = self._filter_by_specificity(filtered_codes)
        
# # # #         # Step 3: ONLY if ambiguity still exists, check for a common default.
# # # #         # This is now the last rule, preventing it from overriding more specific codes.
# # # #         if len(filtered_codes) > 1:
# # # #             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
# # # #         return filtered_codes

# # # # # --- LLM "AUDITOR" CLASS FOR COMPLEX CASES ---
# # # # class ICDReRanker:
# # # #     """The LLM agent, now focused only on complex clinical tie-breaking."""
# # # #     def __init__(self, model, icd_description_map: dict):
# # # #         self.model = model
# # # #         self.icd_map = icd_description_map
# # # #         self.prompt_template = """
# # # #         You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

# # # #         **Auditor's Checklist:**
# # # #         1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
# # # #         2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
# # # #         3.  **Mandatory Reasoning:** State your reasoning in one sentence based on the checklist.
# # # #         ---
# # # #         **EXAMPLE:**
# # # #         **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
# # # #         **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
# # # #         **Reasoning:** Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
# # # #         **Chosen ICD-10 Code:** I50.9
# # # #         ---
# # # #         **ACTUAL AUDIT TASK**
# # # #         **Clinical Text:** "{context}"
# # # #         **Candidate Codes:** {candidate_list}
# # # #         ---
# # # #         **Reasoning:**
# # # #         [Your one-sentence reasoning]
# # # #         **Chosen ICD-10 Code:**
# # # #         [The single best ICD-10 code]
# # # #         """
    
# # # #     def _format_candidates(self, candidate_codes: list) -> str:
# # # #         formatted_string = ""
# # # #         for i, code in enumerate(candidate_codes):
# # # #             description = self.icd_map.get(code, "No description found.")
# # # #             formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
# # # #         return formatted_string.strip()

# # # #     def select_final_code(self, context: str, candidate_codes: list) -> str:
# # # #         """Selects the best code and returns only the code string."""
# # # #         if not candidate_codes: return ""
# # # #         prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
# # # #         try:
# # # #             response = self.model.generate_content(prompt)
# # # #             response_text = response.text.strip()
# # # #             code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
# # # #             if code_match:
# # # #                 code = code_match.group(1).strip()
# # # #                 if code in candidate_codes:
# # # #                     return code
# # # #             return ""
# # # #         except Exception as e:
# # # #             print(f"   ⚠️ Error during LLM call in select_final_code: {e}")
# # # #             return ""

# # # # # --- MAIN ORCHESTRATOR FUNCTION WITH GENERALIZED LOGIC ---
# # # # def run_reranking(input_path: str, kb_csv_path: str, output_path: str, n_samples=5):
# # # #     """Executes Stage 6 with the generalized, hybrid architecture."""
# # # #     try:
# # # #         # NOTE: Handle your API key securely, e.g., using environment variables
# # # #         genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw") # type: ignore
# # # #         stochastic_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
# # # #     except Exception as e:
# # # #         print(f"❌ Error configuring Gemini API: {e}"); return
    
# # # #     try:
# # # #         df_to_process = pd.read_csv(input_path)
# # # #         df_kb = pd.read_csv(kb_csv_path)
# # # #         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
# # # #         # Correctly initialize the RulesEngine with the imported map
# # # #         rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
# # # #         reranker = ICDReRanker(model=stochastic_model, icd_description_map=icd_description_map)

# # # #         print("--- Starting Final Selection Process (Generalized Hybrid Logic) ---")
# # # #         final_results = []
# # # #         for index, row in df_to_process.iterrows():
# # # #             complaint = str(row['chief_complaint'])
# # # #             context = str(row['supporting_evidence'])
# # # #             candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
            
# # # #             print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'") # type: ignore
# # # #             print(f"   -> Initial Candidates: {candidate_codes}")
            
# # # #             final_code = ""
# # # #             confidence = 0

# # # #             # 1. Apply the deterministic Rules Engine FIRST.
# # # #             rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
            
# # # #             if len(rule_based_candidates) != len(candidate_codes):
# # # #                 print(f"   -> Rules Engine Applied. Refined Candidates: {rule_based_candidates}")

# # # #             if len(rule_based_candidates) == 1:
# # # #                 final_code = rule_based_candidates[0]
# # # #                 confidence = 100
# # # #                 print(f"   -> ✅ Decided by Rules Engine.")
# # # #             elif len(rule_based_candidates) > 1:
# # # #                 # 2. If ambiguity remains, use Self-Consistency with the LLM.
# # # #                 print(f"   -> Escalating to LLM Auditor for Self-Consistency...")
# # # #                 llm_predictions = []
# # # #                 for _ in range(n_samples):
# # # #                     code = reranker.select_final_code(context, rule_based_candidates)
# # # #                     if code:
# # # #                         llm_predictions.append(code)
                
# # # #                 if llm_predictions:
# # # #                     vote_count = Counter(llm_predictions)
# # # #                     most_common = vote_count.most_common(1)[0]
# # # #                     final_code = most_common[0]
# # # #                     confidence = (most_common[1] / len(llm_predictions)) * 100
# # # #                     print(f"   -> ✅ LLM Consensus Chose: '{final_code}' with {confidence:.0f}% confidence.")
            
# # # #             if not final_code:
# # # #                 final_code = row.get('concept_identifier', '')
# # # #                 confidence = 20 # Low confidence for fallbacks
# # # #                 print(f"   -> ⚠️ No definitive code found. Using fallback.")
            
# # # #             final_results.append({
# # # #                 'chief_complaint': complaint,
# # # #                 'final_predicted_icd_code': final_code,
# # # #             })
# # # #             time.sleep(1) # Basic rate limiting

# # # #         output_df = pd.DataFrame(final_results)
# # # #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# # # #         output_df.to_csv(output_path, index=False, encoding='utf-8')
# # # #         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# # # #     except Exception as e:
# # # #         print(f"❌ An unexpected error occurred in Stage 6: {e}")

# # # import pandas as pd
# # # import google.generativeai as genai
# # # import time
# # # import ast
# # # import os
# # # import re
# # # from collections import Counter

# # # # --- ARCHITECTURAL UPGRADE 1: A DETERMINISTIC RULES ENGINE ---
# # # class RulesEngine:
# # #     """
# # #     A deterministic engine to apply hard-coded clinical coding rules before
# # #     escalating to a probabilistic LLM.
# # #     """
    
# # #     # --- THE FIX IS HERE: Add the __init__ constructor ---
# # #     def __init__(self, defaults_map: dict):
# # #         """Initializes the engine with the map of common default codes."""
# # #         self.COMMON_DEFAULTS = {k.lower(): v for k, v in defaults_map.items()}
# # #         self.icd_map = {}

# # #     def _filter_by_specificity(self, codes: list) -> list:
# # #         """Removes less specific parent codes when a more specific child code exists."""
# # #         if not codes or len(codes) <= 1:
# # #             return codes
        
# # #         codes_set = set(codes)
# # #         to_remove = {c2 for c1 in codes_set for c2 in codes_set if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
# # #         return [code for code in codes if code not in to_remove]

# # #     def _filter_by_category(self, complaint: str, codes: list) -> list:
# # #         """Removes codes from clinically inappropriate categories."""
# # #         complaint_lower = complaint.lower()
# # #         if "rash" in complaint_lower or "pruritic" in complaint_lower:
# # #             return [code for code in codes if code.startswith('L') or code.startswith('R')]
# # #         if "fall" in complaint_lower or "injury" in complaint_lower:
# # #             return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
# # #         return codes

# # #     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
# # #         """Checks if a common default code can be applied."""
# # #         complaint_lower = complaint.lower().strip()
        
# # #         if complaint_lower in self.COMMON_DEFAULTS:
# # #             default_code = self.COMMON_DEFAULTS[complaint_lower]
# # #             if default_code in codes:
# # #                 return [default_code]
        
# # #         for key, default_code in self.COMMON_DEFAULTS.items():
# # #             if key in complaint_lower and default_code in codes:
# # #                 return [default_code]
        
# # #         return codes

# # #     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
# # #         """
# # #         Runs the full sequence of rule-based filters in the correct, safer order.
# # #         """
# # #         if not candidates: return []
        
# # #         self.icd_map = icd_map
        
# # #         # Step 1: Filter by clinical category first to remove nonsensical options.
# # #         filtered_codes = self._filter_by_category(complaint, candidates)
        
# # #         # Step 2: Apply the crucial specificity filter.
# # #         filtered_codes = self._filter_by_specificity(filtered_codes)
        
# # #         # Step 3: ONLY if ambiguity still exists, check for a common default.
# # #         # This is now the last rule, preventing it from overriding more specific codes.
# # #         if len(filtered_codes) > 1:
# # #             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
# # #         return filtered_codes

# # # # --- LLM "AUDITOR" CLASS FOR COMPLEX CASES ---
# # # class ICDReRanker:
# # #     """The LLM agent, now focused only on complex clinical tie-breaking."""
# # #     def __init__(self, model, icd_description_map: dict):
# # #         self.model = model
# # #         self.icd_map = icd_description_map
# # #         self.prompt_template = """
# # #         You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

# # #         **Auditor's Checklist:**
# # #         1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
# # #         2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
# # #         3.  **Mandatory Reasoning:** State your reasoning in one sentence based on the checklist.
# # #         ---
# # #         **EXAMPLE:**
# # #         **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
# # #         **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
# # #         **Reasoning:** Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
# # #         **Chosen ICD-10 Code:** I50.9
# # #         ---
# # #         **ACTUAL AUDIT TASK**
# # #         **Clinical Text:** "{context}"
# # #         **Candidate Codes:** {candidate_list}
# # #         ---
# # #         **Reasoning:**
# # #         [Your one-sentence reasoning]
# # #         **Chosen ICD-10 Code:**
# # #         [The single best ICD-10 code]
# # #         """
    
# # #     def _format_candidates(self, candidate_codes: list) -> str:
# # #         formatted_string = ""
# # #         for i, code in enumerate(candidate_codes):
# # #             description = self.icd_map.get(code, "No description found.")
# # #             formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
# # #         return formatted_string.strip()
    
# # #     def select_final_code(self, context: str, candidate_codes: list) -> str:
# # #         """Selects the best code and returns only the code string."""
# # #         if not candidate_codes: return ""
# # #         prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
# # #         try:
# # #             response = self.model.generate_content(prompt)
# # #             response_text = response.text.strip()
# # #             code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
# # #             if code_match:
# # #                 code = code_match.group(1).strip()
# # #                 if code in candidate_codes:
# # #                     return code
# # #             return ""
# # #         except Exception as e:
# # #             print(f"   ⚠️ Error during LLM call in select_final_code: {e}")
# # #             return ""

# # # # --- MAIN ORCHESTRATOR FUNCTION WITH BATCHING ADDED ---
# # # def run_reranking(input_path: str, kb_csv_path: str, output_path: str, batch_size: int, delay_between_batches: int = 20, n_samples=5):
# # #     """Executes Stage 6 with the generalized, hybrid architecture in batches."""
# # #     try:
# # #         # NOTE: Handle your API key securely, e.g., using environment variables
# # #         genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw") # type: ignore
# # #         stochastic_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
# # #     except Exception as e:
# # #         print(f"❌ Error configuring Gemini API: {e}"); return
    
# # #     try:
# # #         df_to_process = pd.read_csv(input_path)
# # #         df_kb = pd.read_csv(kb_csv_path)
# # #         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
# # #         # Self-contained dictionary to avoid dependency on external files
# # #         COMMON_DEFAULTS_MAP = {
# # #             'headache': 'R51','dizziness': 'R42','sore throat': 'J02.9','chest pain': 'R07.9',
# # #             'cough': 'R05','abdominal pain': 'R10.9','nausea': 'R11.0','vomiting': 'R11.10',
# # #             'diarrhea': 'R19.7','back pain': 'M54.9','fatigue': 'R53.83','rash': 'R21',
# # #             'shortness of breath': 'R06.02',
# # #         }
        
# # #         # Correctly initialize the RulesEngine with the defined map
# # #         rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
# # #         reranker = ICDReRanker(model=stochastic_model, icd_description_map=icd_description_map)

# # #         print(f"--- Starting Final Selection Process (Batch Size: {batch_size}) ---")
# # #         final_results = []

# # #         # Process the dataframe in batches
# # #         for i in range(0, len(df_to_process), batch_size):
# # #             batch_df = df_to_process.iloc[i : i + batch_size]
# # #             print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")
            
# # #             for index, row in batch_df.iterrows():
# # #                 complaint = str(row['chief_complaint'])
# # #                 context = str(row['supporting_evidence'])
# # #                 candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
                
# # #                 print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
# # #                 print(f"   -> Initial Candidates: {candidate_codes}")
                
# # #                 final_code = ""
# # #                 confidence = 0

# # #                 # 1. Apply the deterministic Rules Engine FIRST.
# # #                 rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
                
# # #                 if len(rule_based_candidates) != len(candidate_codes):
# # #                     print(f"   -> Rules Engine Applied. Refined Candidates: {rule_based_candidates}")
                
# # #                 if len(rule_based_candidates) == 1:
# # #                     final_code = rule_based_candidates[0]
# # #                     confidence = 100
# # #                     print(f"   -> ✅ Decided by Rules Engine.")
# # #                 elif len(rule_based_candidates) > 1:
# # #                     # 2. If ambiguity remains, use Self-Consistency with the LLM.
# # #                     print(f"   -> Escalating to LLM Auditor for Self-Consistency...")
# # #                     llm_predictions = []
# # #                     for _ in range(n_samples):
# # #                         code = reranker.select_final_code(context, rule_based_candidates)
# # #                         if code:
# # #                             llm_predictions.append(code)
                    
# # #                     if llm_predictions:
# # #                         vote_count = Counter(llm_predictions)
# # #                         most_common = vote_count.most_common(1)[0]
# # #                         final_code = most_common[0]
# # #                         confidence = (most_common[1] / len(llm_predictions)) * 100
# # #                         print(f"   -> ✅ LLM Consensus Chose: '{final_code}' with {confidence:.0f}% confidence.")
                
# # #                 if not final_code:
# # #                     final_code = row.get('concept_identifier', '')
# # #                     confidence = 20 # Low confidence for fallbacks
# # #                     print(f"   -> ⚠️ No definitive code found. Using fallback.")
                
# # #                 final_results.append({
# # #                     'chief_complaint': complaint,
# # #                     'final_predicted_icd_code': final_code,
# # #                 })
# # #                 time.sleep(1) # Basic rate limiting per request

# # #             # After a batch is processed, wait if it is not the last one.
# # #             if (i + batch_size) < len(df_to_process):
# # #                 print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
# # #                 time.sleep(delay_between_batches)

# # #         output_df = pd.DataFrame(final_results)
# # #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# # #         output_df.to_csv(output_path, index=False, encoding='utf-8')
# # #         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# # #     except Exception as e:
# # #         print(f"❌ An unexpected error occurred in Stage 6: {e}")

# # # # Example of how to run the function:
# # # if __name__ == '__main__':
# # #     # Create dummy input files for demonstration if they don't exist
# # #     if not os.path.exists('dummy_candidates.csv'):
# # #         dummy_data = {
# # #             'chief_complaint': ['headache', ' worsening leg edema', 'fall with wrist pain', 'acute wheezing', 'pruritic rash'],
# # #             'supporting_evidence': ['pt c/o headache for 3 days', '72 y/o F with a hx of CHF presents with worsening leg edema', 'pt fell, has pain in right wrist, swelling noted', 'pt c/o wheezing, has hx of asthma, uses albuterol inhaler', 'Patient has an itchy red rash on their arm after touching a plant.'],
# # #             'candidate_icd_codes': [str(['R51', 'G44.1']), str(['R60.0', 'I50.9']), str(['S62.90XA', 'W19.XXXA', 'R52']), str(['R06.2', 'J45.901']), str(['L23.9', 'R21'])],
# # #             'concept_identifier': ['R51', 'I50.9', 'S62.90XA', 'R06.2', 'L23.9']
# # #         }
# # #         pd.DataFrame(dummy_data).to_csv('dummy_candidates.csv', index=False)
    
# # #     if not os.path.exists('dummy_kb.csv'):
# # #         dummy_kb_data = {
# # #             'CUI': ['R51', 'G44.1', 'R60.0', 'I50.9', 'S62.90XA', 'W19.XXXA', 'R52', 'R06.2', 'J45.901', 'L23.9', 'R21'],
# # #             'Description': ['Headache', 'Vascular headache, not elsewhere classified', 'Localized edema', 'Unspecified heart failure', 'Unspecified fracture of unspecified carpal bone(s), initial encounter for closed fracture', 'Unspecified fall, initial encounter', 'Pain, unspecified', 'Wheezing', 'Unspecified asthma with (acute) exacerbation', 'Allergic contact dermatitis, unspecified cause', 'Rash and other nonspecific skin eruption']
# # #         }
# # #         pd.DataFrame(dummy_kb_data).to_csv('dummy_kb.csv', index=False)
        
# # #     run_reranking(
# # #         input_path='dummy_candidates.csv',
# # #         kb_csv_path='dummy_kb.csv',
# # #         output_path='output/final_predictions.csv',
# # #         batch_size=2,          # Process 2 rows per batch
# # #         delay_between_batches=5 # Wait 5 seconds between batches
# # #     )

# import pandas as pd
# import google.generativeai as genai
# import time
# import ast
# import os
# import re
# from collections import Counter
# from .clinical_defaults import COMMON_DEFAULTS_MAP

# # # --- ARCHITECTURAL UPGRADE 1: A DETERMINISTIC RULES ENGINE ---
# # # class RulesEngine:
# # #     """
# # #     A deterministic engine to apply hard-coded clinical coding rules before
# # #     escalating to a probabilistic LLM.
# # #     """
    
# # #     def __init__(self, defaults_map: dict):
# # #         """Initializes the engine with the map of common default codes."""
# # #         self.COMMON_DEFAULTS = {k.lower(): v for k, v in defaults_map.items()}
# # #         self.icd_map = {}

# # #     def _filter_by_specificity(self, codes: list) -> list:
# # #         """Removes less specific parent codes when a more specific child code exists."""
# # #         if not codes or len(codes) <= 1:
# # #             return codes
        
# # #         codes_set = set(codes)
# # #         to_remove = {c2 for c1 in codes_set for c2 in codes_set if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
# # #         return [code for code in codes if code not in to_remove]

# # #     def _filter_by_category(self, complaint: str, codes: list) -> list:
# # #         """Removes codes from clinically inappropriate categories."""
# # #         complaint_lower = complaint.lower()
# # #         if "rash" in complaint_lower or "pruritic" in complaint_lower:
# # #             return [code for code in codes if code.startswith('L') or code.startswith('R')]
# # #         if "fall" in complaint_lower or "injury" in complaint_lower:
# # #             return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
# # #         return codes

# # #     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
# # #         """Checks if a common default code can be applied."""
# # #         complaint_lower = complaint.lower().strip()
        
# # #         if complaint_lower in self.COMMON_DEFAULTS:
# # #             default_code = self.COMMON_DEFAULTS[complaint_lower]
# # #             if default_code in codes:
# # #                 return [default_code]
        
# # #         for key, default_code in self.COMMON_DEFAULTS.items():
# # #             if key in complaint_lower and default_code in codes:
# # #                 return [default_code]
        
# # #         return codes

# # #     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
# # #         """
# # #         Runs the full sequence of rule-based filters in the correct, safer order.
# # #         """
# # #         if not candidates: 
# # #             return []
        
# # #         self.icd_map = icd_map
        
# # #         # Step 1: Filter by clinical category first to remove nonsensical options.
# # #         filtered_codes = self._filter_by_category(complaint, candidates)
        
# # #         # Step 2: Apply the crucial specificity filter.
# # #         filtered_codes = self._filter_by_specificity(filtered_codes)
        
# # #         # Step 3: ONLY if ambiguity still exists, check for a common default.
# # #         if len(filtered_codes) > 1:
# # #             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
# # #         if not filtered_codes and candidates:
# # #             return candidates

# # #         return filtered_codes

# class RulesEngine:
#     """
#     A deterministic engine with a corrected and more robust implementation
#     for applying hard-coded clinical coding rules.
#     """
    
#     def __init__(self, defaults_map: dict):
#         """Initializes the engine with a case-insensitive map of default codes."""
#         self.COMMON_DEFAULTS = {k.lower(): v for k, v in defaults_map.items()}
#         self.icd_map = {}

#     def _filter_by_specificity(self, codes: list) -> list:
#         """Removes less specific parent codes when a more specific child code exists."""
#         if not codes or len(codes) <= 1:
#             return codes
        
#         codes_set = set(codes)
#         to_remove = {c2 for c1 in codes_set for c2 in codes_set if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
#         return [code for code in codes if code not in to_remove]

#     def _filter_by_category(self, complaint: str, codes: list) -> list:
#         """Removes codes from clinically inappropriate categories."""
#         complaint_lower = complaint.lower()
#         if "rash" in complaint_lower or "pruritic" in complaint_lower:
#             return [code for code in codes if code.startswith('L') or code.startswith('R')]
#         if "fall" in complaint_lower or "injury" in complaint_lower:
#             return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
#         return codes

#     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
#         """
#         A more robust method to apply a common default code. It now prioritizes
#         the most specific (longest) keyword match.
#         """
#         complaint_lower = complaint.lower().strip()
        
#         # Find all keys from our defaults map that are present in the complaint
#         matching_keys = [key for key in self.COMMON_DEFAULTS if key in complaint_lower]
        
#         if not matching_keys:
#             # If no keywords from our map are in the complaint, do nothing.
#             return codes
            
#         # From the list of all matches, choose the longest one.
#         # This correctly handles cases like "chest pain" vs. "pain".
#         best_key = max(matching_keys, key=len)
#         default_code = self.COMMON_DEFAULTS[best_key]
        
#         # If this best-match default code is in our candidate list, we have a winner.
#         if default_code in codes:
#             print(f"   -> RulesEngine: Matched complaint to default key '{best_key}', selecting code '{default_code}'.")
#             return [default_code]
            
#         # If the default code isn't a candidate, do nothing.
#         return codes

#     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
#         """
#         Runs the full sequence of rule-based filters in the correct, safer order.
#         """
#         if not candidates: 
#             return []
        
#         self.icd_map = icd_map
        
#         # Run filters in the correct order: Category -> Specificity -> Defaults
#         filtered_codes = self._filter_by_category(complaint, candidates)
        
#         if len(candidates) != len(filtered_codes):
#              print(f"   -> RulesEngine: Category filter reduced candidates to: {filtered_codes}")

#         specificity_filtered_codes = self._filter_by_specificity(filtered_codes)
#         if len(specificity_filtered_codes) != len(filtered_codes):
#             print(f"   -> RulesEngine: Specificity filter reduced candidates to: {specificity_filtered_codes}")
        
#         filtered_codes = specificity_filtered_codes
        
#         if len(filtered_codes) > 1:
#             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
#         # Safety net: If all candidates were somehow filtered out, revert.
#         if not filtered_codes and candidates:
#             print("   -> RulesEngine: Warning! All candidates were filtered out. Reverting to pre-filter list.")
#             return candidates

#         return filtered_codes

# # --- LLM "AUDITOR" CLASS FOR COMPLEX CASES ---
# class ICDReRanker:
#     """The LLM agent, now focused only on complex clinical tie-breaking."""
#     def __init__(self, model, icd_description_map: dict):
#         self.model = model
#         self.icd_map = icd_description_map
#         self.prompt_template = """
#         You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

#         **Your Most Important Rule:** You MUST choose the single best code from the list that most closely matches the clinical text. Even if no candidate is a perfect match, you must select the best possible option. Do not refuse to make a choice.

#         **Auditor's Checklist:**
#         1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
#         2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
#         3.  **Mandatory Reasoning:** State your reasoning in one sentence based on the checklist.
#         ---
#         **EXAMPLE:**
#         **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
#         **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
#         **Reasoning:** Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
#         **Chosen ICD-10 Code:** I50.9
#         ---
#         **ACTUAL AUDIT TASK**
#         **Clinical Text:** "{context}"
#         **Candidate Codes:** {candidate_list}
#         ---
#         **Reasoning:**
#         [Your one-sentence reasoning]
#         **Chosen ICD-10 Code:**
#         [The single best ICD-10 code]
#         """
    
#     def _format_candidates(self, candidate_codes: list) -> str:
#         formatted_string = ""
#         for i, code in enumerate(candidate_codes):
#             description = self.icd_map.get(code, "No description found.")
#             formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
#         return formatted_string.strip()

#     def select_final_code(self, context: str, candidate_codes: list) -> str:
#         """Selects the best code and returns only the code string."""
#         if not candidate_codes: return ""
#         prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
#         try:
#             response = self.model.generate_content(prompt)
#             response_text = response.text.strip()
#             code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
#             if code_match:
#                 code = code_match.group(1).strip()
#                 if code in candidate_codes:
#                     return code
#             return ""
#         except Exception as e:
#             print(f"   ⚠️ Error during LLM call in select_final_code: {e}")
#             return ""

# # # --- MAIN ORCHESTRATOR FUNCTION WITH BATCHING AND NO REPEATED QUERIES ---
# # def run_reranking(input_path: str, kb_csv_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
# #     """Executes Stage 6 with a hybrid architecture, using a single LLM call for tie-breaking."""
# #     try:
# #         # NOTE: Handle your API key securely
# #         genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw") # type: ignore
# #         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
# #     except Exception as e:
# #         print(f"❌ Error configuring Gemini API: {e}"); return
    
# #     try:
# #         df_to_process = pd.read_csv(input_path)
# #         df_kb = pd.read_csv(kb_csv_path)
# #         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
# #         rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
# #         reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)

# #         print(f"--- Starting Final Selection Process (Batch Size: {batch_size}) ---")
# #         final_results = []

# #         # Process the dataframe in batches
# #         for i in range(0, len(df_to_process), batch_size):
# #             batch_df = df_to_process.iloc[i : i + batch_size]
# #             print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")

# #             for index, row in batch_df.iterrows():
# #                 complaint = str(row['chief_complaint'])
# #                 context = str(row['supporting_evidence'])
# #                 candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
                
# #                 print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
# #                 print(f"   -> Initial Candidates: {candidate_codes}")
                
# #                 final_code = ""

# #                 # 1. Apply the deterministic Rules Engine FIRST.
# #                 rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
                
# #                 if len(rule_based_candidates) != len(candidate_codes):
# #                     print(f"   -> Rules Engine Applied. Refined Candidates: {rule_based_candidates}")
                
# #                 if len(rule_based_candidates) == 1:
# #                     final_code = rule_based_candidates[0]
# #                     print(f"   -> ✅ Decided by Rules Engine.")
# #                 elif len(rule_based_candidates) > 1:
# #                     # 2. If ambiguity remains, escalate to the LLM for a single, final decision.
# #                     print(f"   -> Escalating to LLM Auditor for final decision...")
# #                     code = reranker.select_final_code(context, rule_based_candidates)
# #                     if code:
# #                         final_code = code
# #                         print(f"   -> ✅ LLM Auditor Chose: '{final_code}'.")
                
# #                 if not final_code:
# #                     final_code = row.get('concept_identifier', '') # Use fallback from previous stage
# #                     print(f"   -> ⚠️  No definitive code found. Using fallback.")
                
# #                 final_results.append({
# #                     'chief_complaint': complaint,
# #                     'final_predicted_icd_code': final_code,
# #                 })
# #                 time.sleep(1) # Basic rate limiting per individual request

# #             # After processing a batch, wait if it is not the last one
# #             if (i + batch_size) < len(df_to_process):
# #                 print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
# #                 time.sleep(delay_between_batches)

# #         output_df = pd.DataFrame(final_results)
# #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# #         output_df.to_csv(output_path, index=False, encoding='utf-8')
# #         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# #     except Exception as e:
# #         print(f"❌ An unexpected error occurred in Stage 6: {e}")
# # def run_reranking(input_path: str, kb_csv_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
# #     """
# #     Executes Stage 6 with a hybrid architecture and the 5-tier confidence framework.
# #     """
# #     try:
# #         # NOTE: It is best practice to handle your API key securely
# #         genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw")
# #         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0})
# #     except Exception as e:
# #         print(f"❌ Error configuring Gemini API: {e}"); return
    
# #     try:
# #         df_to_process = pd.read_csv(input_path)
# #         df_kb = pd.read_csv(kb_csv_path)
# #         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
# #         rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
# #         reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)

# #         print(f"--- Starting Final Selection Process (Batch Size: {batch_size}) ---")
# #         final_results = []

# #         for i in range(0, len(df_to_process), batch_size):
# #             batch_df = df_to_process.iloc[i : i + batch_size]
# #             print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")

# #             for index, row in batch_df.iterrows():
# #                 complaint = str(row['chief_complaint'])
# #                 context = str(row['supporting_evidence'])
# #                 candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
                
# #                 print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
# #                 print(f"   -> Initial Candidates: {candidate_codes}")
                
# #                 final_code = None
# #                 confidence_category = "Unknown"

# #                 # 1. Apply Rules Engine for a "Very High" confidence decision
# #                 rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
# #                 if len(rule_based_candidates) == 1:
# #                     final_code = rule_based_candidates[0]
# #                     confidence_category = "Very High"
# #                     print(f"   -> ✅ Decided by Rules Engine. Confidence: {confidence_category}.")

# #                 # 2. Escalate to LLM for a "High" confidence decision
# #                 elif len(rule_based_candidates) > 1:
# #                     print(f"   -> Escalating to LLM Auditor...")
# #                     code = reranker.select_final_code(context, rule_based_candidates)
# #                     if code:
# #                         final_code = code
# #                         confidence_category = "High"
# #                         print(f"   -> ✅ LLM Auditor Chose: '{final_code}'. Confidence: {confidence_category}.")

# #                 # 3. If no decision yet, begin fallback sequence
# #                 if not final_code:
# #                     print(f"   -> ⚠️ No definitive code found. Initiating fallback sequence...")
                    
# #                     # Fallback Tier 1: "Medium" confidence
# #                     fallback_code = row.get('concept_identifier')
# #                     if fallback_code and pd.notna(fallback_code):
# #                         final_code = fallback_code
# #                         confidence_category = "Medium"
# #                         print(f"   -> ✅ Fallback Success (Tier 1): Used Stage 4 concept '{final_code}'. Confidence: {confidence_category}.")
                    
# #                     # Fallback Tier 2: "Low" confidence
# #                     elif rule_based_candidates:
# #                         final_code = rule_based_candidates[0]
# #                         confidence_category = "Low"
# #                         print(f"   -> ✅ Fallback Success (Tier 2): Used first available candidate '{final_code}'. Confidence: {confidence_category}.")

# #                     # Fallback Tier 3: "Very Low" confidence
# #                     else:
# #                         final_code = "NEEDS_MANUAL_REVIEW"
# #                         confidence_category = "Very Low"
# #                         print(f"   -> ❌ Fallback Failed. Requires manual review. Confidence: {confidence_category}.")
                
# #                 final_results.append({
# #                     'chief_complaint': complaint,
# #                     'final_predicted_icd_code': final_code,
# #                     'confidence_category': confidence_category
# #                 })
# #                 time.sleep(1)

# #             if (i + batch_size) < len(df_to_process):
# #                 print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
# #                 time.sleep(delay_between_batches)

# #         output_df = pd.DataFrame(final_results)
# #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# #         output_df.to_csv(output_path, index=False, encoding='utf-8')
# #         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# #     except Exception as e:
# #         print(f"❌ An unexpected error occurred in Stage 6: {e}")

# def run_reranking(input_path: str, kb_csv_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
#     """
#     Executes Stage 6 with a corrected hybrid architecture and the full 5-tier confidence framework.
#     """
#     try:
#         genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw")
#         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0})
#     except Exception as e:
#         print(f"❌ Error configuring Gemini API: {e}"); return
    
#     try:
#         df_to_process = pd.read_csv(input_path)
#         df_kb = pd.read_csv(kb_csv_path)
#         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
#         rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
#         reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)

#         print(f"--- Starting Final Selection Process (Batch Size: {batch_size}) ---")
#         final_results = []

#         for i in range(0, len(df_to_process), batch_size):
#             batch_df = df_to_process.iloc[i : i + batch_size]
#             print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")

#             for index, row in batch_df.iterrows():
#                 complaint = str(row['chief_complaint'])
#                 context = str(row['supporting_evidence'])
#                 candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
                
#                 print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
#                 print(f"   -> Initial Candidates: {candidate_codes}")
                
#                 final_code = None
#                 confidence_category = "Unknown"

#                 # Tier 1: "Very High" confidence (Decision by RulesEngine)
#                 rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
#                 if len(rule_based_candidates) == 1:
#                     final_code = rule_based_candidates[0]
#                     confidence_category = "Very High"
#                     print(f"   -> ✅ Decided by Rules Engine. Confidence: {confidence_category}.")

#                 # Tier 2: "High" confidence (Successful decision by LLM Auditor)
#                 elif len(rule_based_candidates) > 1:
#                     print(f"   -> Escalating to LLM Auditor...")
#                     code = reranker.select_final_code(context, rule_based_candidates)
#                     if code:
#                         final_code = code
#                         confidence_category = "High"
#                         print(f"   -> ✅ LLM Auditor Chose: '{final_code}'. Confidence: {confidence_category}.")

#                 # If no decision has been made, begin the fallback sequence
#                 if not final_code:
#                     print(f"   -> ⚠️ No definitive code found. Initiating fallback sequence...")
                    
#                     # Tier 3: "Medium" confidence (Fallback to Stage 4 concept)
#                     fallback_code = row.get('concept_identifier')
#                     if fallback_code and pd.notna(fallback_code):
#                         final_code = fallback_code
#                         confidence_category = "Medium"
#                         print(f"   -> ✅ Fallback Success (Tier 1): Used Stage 4 concept '{final_code}'. Confidence: {confidence_category}.")
                    
#                     # Tier 4: "Low" confidence (Fallback to first available candidate)
#                     elif rule_based_candidates:
#                         final_code = rule_based_candidates[0]
#                         confidence_category = "Low"
#                         print(f"   -> ✅ Fallback Success (Tier 2): Used first available candidate '{final_code}'. Confidence: {confidence_category}.")

#                     # Tier 5: "Very Low" confidence (Last resort)
#                     else:
#                         final_code = "NEEDS_MANUAL_REVIEW"
#                         confidence_category = "Very Low"
#                         print(f"   -> ❌ Fallback Failed. Requires manual review. Confidence: {confidence_category}.")
                
#                 final_results.append({
#                     'chief_complaint': complaint,
#                     'final_predicted_icd_code': final_code
#                     # 'confidence_category': confidence_category
#                 })
#                 time.sleep(1) # API rate limiting

#             if (i + batch_size) < len(df_to_process):
#                 print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
#                 time.sleep(delay_between_batches)

#         output_df = pd.DataFrame(final_results)
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
#         output_df.to_csv(output_path, index=False, encoding='utf-8')
#         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

#     except Exception as e:
#         print(f"❌ An unexpected error occurred in Stage 6: {e}")

#############################################################################
#### Working fine with confidence

# import pandas as pd
# import google.generativeai as genai
# import time
# import ast
# import os
# import re
# from collections import Counter
# from .clinical_defaults import COMMON_DEFAULTS_MAP

# class RulesEngine:
#     def __init__(self, defaults_map: dict):
#         self.COMMON_DEFAULTS = {k.lower(): v for k, v in defaults_map.items()}
#         self.icd_map = {}

#     def _filter_by_specificity(self, codes: list) -> list:
#         if not codes or len(codes) <= 1:
#             return codes
#         codes_set = set(codes)
#         to_remove = {c2 for c1 in codes_set for c2 in codes_set if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
#         return [code for code in codes if code not in to_remove]

#     def _filter_by_category(self, complaint: str, codes: list) -> list:
#         complaint_lower = complaint.lower()
#         if "rash" in complaint_lower or "pruritic" in complaint_lower:
#             return [code for code in codes if code.startswith('L') or code.startswith('R')]
#         if "fall" in complaint_lower or "injury" in complaint_lower:
#             return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
#         return codes

#     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
#         complaint_lower = complaint.lower().strip()
#         matching_keys = [key for key in self.COMMON_DEFAULTS if key in complaint_lower]
#         if not matching_keys:
#             return codes
#         best_key = max(matching_keys, key=len)
#         default_code = self.COMMON_DEFAULTS[best_key]
#         if default_code in codes:
#             print(f"   -> RulesEngine: Matched complaint to default key '{best_key}', selecting code '{default_code}'.")
#             return [default_code]
#         return codes

#     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
#         if not candidates: 
#             return []
#         self.icd_map = icd_map
#         filtered_codes = self._filter_by_category(complaint, candidates)
#         specificity_filtered_codes = self._filter_by_specificity(filtered_codes)
#         filtered_codes = specificity_filtered_codes
#         if len(filtered_codes) > 1:
#             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
#         if not filtered_codes and candidates:
#             print("   -> RulesEngine: Warning! All candidates were filtered out. Reverting to pre-filter list.")
#             return candidates
#         return filtered_codes

# class ICDReRanker:
#     def __init__(self, model, icd_description_map: dict):
#         self.model = model
#         self.icd_map = icd_description_map
#         self.prompt_template = """
#         You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

#         **Your Most Important Rule:** You MUST choose the single best code from the list that most closely matches the clinical text. Even if no candidate is a perfect match, you must select the best possible option. Do not refuse to make a choice.

#         **Auditor's Checklist:**
#         1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
#         2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
#         3.  **Mandatory Reasoning:** State your reasoning in one sentence based on the checklist.
#         4.  **Confidence Rating Required:** Also rate your confidence in the final decision using one of the following categories:
#             - Very High
#             - High
#             - Medium
#             - Low
#             - Very Low

#         ---
#         **EXAMPLE:**
#         **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
#         **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
#         **Reasoning:** Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
#         **Chosen ICD-10 Code:** I50.9
#         **Confidence Category:** High
#         ---
#         **ACTUAL AUDIT TASK**
#         **Clinical Text:** "{context}"
#         **Candidate Codes:** {candidate_list}
#         ---
#         **Reasoning:**
#         [Your one-sentence reasoning]
#         **Chosen ICD-10 Code:**
#         [The single best ICD-10 code]
#         **Confidence Category:**
#         [One of: Very High, High, Medium, Low, Very Low]
#         """

#     def _format_candidates(self, candidate_codes: list) -> str:
#         formatted_string = ""
#         for i, code in enumerate(candidate_codes):
#             description = self.icd_map.get(code, "No description found.")
#             formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
#         return formatted_string.strip()

#     def select_final_code_and_confidence(self, context: str, candidate_codes: list) -> tuple:
#         if not candidate_codes:
#             return ("", "Unknown")
        
#         prompt = self.prompt_template.format(
#             context=context,
#             candidate_list=self._format_candidates(candidate_codes)
#         )
#         try:
#             response = self.model.generate_content(prompt)
#             response_text = response.text.strip()

#             # Enhanced parsing with fallback strategies
#             code = ""
#             confidence = "Unknown"
            
#             # Strategy 1: Direct regex extraction
#             code_match = re.search(r"Chosen ICD-10 Code[:\*]*\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
#             confidence_match = re.search(r"Confidence Category[:\*]*\s*(Very High|High|Medium|Low|Very Low)", response_text, re.IGNORECASE)
            
#             if code_match:
#                 code = code_match.group(1).strip()
#                 if confidence_match:
#                     confidence = confidence_match.group(1).strip()
            
#             # Strategy 2: Line-by-line fallback parsing
#             if not code:
#                 for line in response_text.split('\n'):
#                     if "Chosen ICD-10 Code" in line:
#                         code = re.findall(r'[A-Z0-9\.]+', line)[-1] if re.findall(r'[A-Z0-9\.]+', line) else ""
#                     if "Confidence Category" in line and confidence == "Unknown":
#                         confidence = re.search(r'(Very High|High|Medium|Low|Very Low)', line, re.IGNORECASE)
#                         confidence = confidence.group(0) if confidence else "Unknown"

#             # Strategy 3: Validation and fallback
#             normalized_candidates = [c.strip().upper() for c in candidate_codes]
#             if code.strip().upper() not in normalized_candidates:
#                 print(f"   ⚠️ Extracted code '{code}' not in candidates. Reverting to Stage 4 concept.")
#                 return ("", "Unknown")  # Will trigger fallback in main loop
            
#             return (code, confidence)
        
#         except Exception as e:
#             print(f"   ⚠️ Error during LLM call: {e}")
#             return ("", "Unknown")

# def run_reranking(input_path: str, kb_csv_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
#     try:
#         genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw") # type: ignore
#         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
#     except Exception as e:
#         print(f"❌ Error configuring Gemini API: {e}"); return

#     try:
#         df_to_process = pd.read_csv(input_path)
#         df_kb = pd.read_csv(kb_csv_path)
#         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()

#         rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
#         reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)

#         print(f"--- Starting Final Selection Process (Batch Size: {batch_size}) ---")
#         final_results = []

#         for i in range(0, len(df_to_process), batch_size):
#             batch_df = df_to_process.iloc[i : i + batch_size]
#             print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")

#             for index, row in batch_df.iterrows():
#                 complaint = str(row['chief_complaint'])
#                 context = str(row['supporting_evidence'])
#                 candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []

#                 print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'") # type: ignore
#                 print(f"   -> Initial Candidates: {candidate_codes}")

#                 filtered_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
#                 print(f"   -> Filtered Candidates: {filtered_candidates}")

#                 # Get LLM decision with confidence
#                 code, confidence = reranker.select_final_code_and_confidence(context, filtered_candidates)
        
#                 # Fallback mechanism if LLM parsing fails
#                 if not code:
#                     print("   -> ⚠️ LLM failed to identify valid code. Using Stage 4 concept.")
#                     code = row.get('concept_identifier', '')
#                     confidence = "Medium"  # Default confidence for Stage 4 concept
                
#                 print(f"   -> ✅ Final Code: '{code}' | Confidence: {confidence}")

#                 final_results.append({
#                     'chief_complaint': complaint,
#                     'final_predicted_icd_code': code,
#                     'confidence_category': confidence
#                 })
#                 time.sleep(1)

#             if (i + batch_size) < len(df_to_process):
#                 print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
#                 time.sleep(delay_between_batches)

#         output_df = pd.DataFrame(final_results)
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
#         output_df.to_csv(output_path, index=False, encoding='utf-8')
#         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

#     except Exception as e:
#         print(f"❌ An unexpected error occurred in Stage 6: {e}")

#############################################################################

import pandas as pd
import google.generativeai as genai
import time
import ast
import os
import re
from .clinical_defaults import COMMON_DEFAULTS_MAP

class RulesEngine:
    def __init__(self, defaults_map: dict):
        self.COMMON_DEFAULTS = {k.lower(): v for k, v in defaults_map.items()}
        self.icd_map = {}

    def _filter_by_specificity(self, codes: list) -> list:
        if not codes or len(codes) <= 1:
            return codes
        codes_set = set(codes)
        to_remove = {c2 for c1 in codes_set for c2 in codes_set 
                     if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
        return [code for code in codes if code not in to_remove]

    def _filter_by_category(self, complaint: str, codes: list) -> list:
        complaint_lower = complaint.lower()
        if "rash" in complaint_lower or "pruritic" in complaint_lower:
            return [code for code in codes if code.startswith('L') or code.startswith('R')]
        if "fall" in complaint_lower or "injury" in complaint_lower:
            return [code for code in codes if code.startswith(('S', 'T', 'W')) 
                    or "fall" in self.icd_map.get(code, "").lower()]
        return codes

    def _apply_common_defaults(self, complaint: str, codes: list) -> list:
        complaint_lower = complaint.lower().strip()
        matching_keys = [key for key in self.COMMON_DEFAULTS if key in complaint_lower]
        if not matching_keys:
            return codes
        best_key = max(matching_keys, key=len)
        default_code = self.COMMON_DEFAULTS[best_key]
        if default_code in codes:
            print(f"   -> RulesEngine: Matched complaint to default key '{best_key}', selecting code '{default_code}'.")
            return [default_code]
        return codes

    def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
        if not candidates: 
            return []
        self.icd_map = icd_map
        filtered_codes = self._filter_by_category(complaint, candidates)
        specificity_filtered_codes = self._filter_by_specificity(filtered_codes)
        filtered_codes = specificity_filtered_codes
        if len(filtered_codes) > 1:
            filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        if not filtered_codes and candidates:
            print("   -> RulesEngine: Warning! All candidates were filtered out. Reverting to pre-filter list.")
            return candidates
        return filtered_codes

class ICDReRanker:
    def __init__(self, model, icd_description_map: dict):
        self.model = model
        self.icd_map = icd_description_map
        self.prompt_template = """
        You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

        **Your Most Important Rule:** You MUST choose the single best code from the list that most closely matches the clinical text. Even if no candidate is a perfect match, you must select the best possible option. Do not refuse to make a choice.

        **Auditor's Checklist:**
        1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
        2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
        3.  **Mandatory Reasoning:** State your reasoning in one sentence for choosing the ICD-10 code.
        4.  **Confidence Rating:** Rate your confidence in the final decision using one of the following categories: Very High, High, Medium, Low, Very Low.
        5.  **Confidence Reasoning:** Briefly explain why you chose this confidence category (e.g., "I am very confident because the code directly matches the clinical context.").

        **Instructions for Confidence Assignment:**

        Refer to the below guidelines when providing your "Reasoning for Confidence.":

        - **Very High:** Use when the clinical context is unambiguous and the code directly matches the diagnosis.
        - **High:** Use when the clinical context is clear, but there is minor uncertainty or a close second option.
        - **Medium:** Use when there is some ambiguity or missing information, but the chosen code is still the best match.
        - **Low:** Use when information is limited or conflicting; the chosen code is a best guess.
        - **Very Low:** Use when there is no clear match or insufficient information; manual review is recommended.

        ---
        **EXAMPLE-1:**  
        **Chief Complaint:** "Leg edema"  
        **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."  
        **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]  
        **Reasoning for ICD Code:**  
        Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis. According to coding guidelines, when a symptom is clearly attributed to an underlying diagnosis, the code for the primary diagnosis should be assigned rather than the symptom code.  
        Rule #2 (Best Semantic Match): The clinical text explicitly describes a patient with a history of CHF who now has worsening leg edema, strongly suggesting that the edema is due to heart failure rather than another cause.  
        **Chosen ICD-10 Code:** I50.9  
        **Confidence Category:** High  
        **Reasoning for Confidence:**  
        I am confident because the clinical context clearly describes CHF as the underlying cause of the leg edema. The code I50.9 (Heart failure, unspecified) directly matches the documented diagnosis and provides the most accurate representation of the patient's condition.

        **EXAMPLE-2**
        **Chief Complaint:** "Dyspnea on Exertion"  
        **Clinical Text:** "Patient presents with dyspnea on exertion, without further diagnostic information."  
        **Candidate Codes:** [`R06.02` (Shortness of breath), `R06.09` (Other forms of dyspnea), `I50.9` (Heart failure, unspecified)]  
        **Reasoning for ICD Code:**  
        Rule #1 (Diagnosis Precedence): There is no clear evidence of an underlying condition such as heart failure in the clinical text.  
        Rule #2 (Best Semantic Match): The most accurate code for "dyspnea on exertion" in the absence of an underlying diagnosis is R06.09 ("Other forms of dyspnea"), as this code specifically includes "dyspnea on exertion." R06.02 ("Shortness of breath") is a broader term and may also be used, but R06.09 is preferred for strict ICD-10 compliance.  
        **Chosen ICD-10 Code:** R06.09  
        **Confidence Category:** High  
        **Reasoning for Confidence:**
        I am confident because the clinical text explicitly describes "dyspnea on exertion" and there is no additional diagnostic information to suggest an underlying condition. The code R06.09 directly matches the clinical presentation for "dyspnea on exertion."

        **EXAMPLE-3**
        **Chief Complaint:** "Chest pain"
        **Clinical Text:** "Patient presents with chest pain, history of hypertension but no clear evidence of cardiac disease."
        **Candidate Codes:** [`R07.9` (Chest pain, unspecified), `I20.9` (Angina pectoris, unspecified), `R07.89` (Other chest pain)]
        **Reasoning for ICD Code:**  
        Rule #1 (Diagnosis Precedence): There is a history of hypertension, but no clear evidence of cardiac disease.  
        Rule #2 (Best Semantic Match): The most accurate code is still R07.9 ("Chest pain, unspecified"), but the presence of hypertension introduces some uncertainty.  
        **Chosen ICD-10 Code:** R07.9  
        **Confidence Category:** Medium  
        **Reasoning for Confidence:**  
        I am moderately confident because the clinical text describes chest pain with a history of hypertension but no clear evidence of cardiac disease. The code R07.9 is still the best match, but the presence of a risk factor introduces some uncertainty.

        **EXAMPLE-4**
        **Chief Complaint:** "Headache"
        **Clinical Text:** "Patient reports headache, additional symptoms not specified."
        **Candidate Codes:** [`R51.9` (Headache, unspecified), `G43.909` (Migraine, unspecified), `R51.0` (Headache with facial pain)]
        **Reasoning for ICD Code:**  
        Rule #1 (Diagnosis Precedence): There is no information about underlying conditions or additional symptoms.  
        Rule #2 (Best Semantic Match): The most accurate code is R51.9 ("Headache, unspecified"), but the lack of detail reduces confidence.  
        **Chosen ICD-10 Code:** R51.9  
        **Confidence Category:** Low  
        **Reasoning for Confidence:**  
        I am less confident because the clinical text provides limited information about the headache. The code R51.9 is the best available choice, but the lack of detail introduces uncertainty.

        **EXAMPLE-5**
        **Chief Complaint:** "Acute abdominal pain"
        **Clinical Text:** "Patient presents with acute abdominal pain, no history of chronic abdominal conditions."
        **Candidate Codes:** [`R10.9` (Abdominal pain, unspecified), `K57.30` (Diverticulosis of large intestine without perforation or abscess without bleeding), `K58.9` (Irritable bowel syndrome without diarrhea)]
        **Reasoning for ICD Code:**  
        Rule #1 (Diagnosis Precedence): There is no evidence of an underlying abdominal diagnosis in the clinical text.  
        Rule #2 (Best Semantic Match): The most accurate code for acute abdominal pain with no further diagnostic information is R10.9 ("Abdominal pain, unspecified").  
        **Chosen ICD-10 Code:** R10.9  
        **Confidence Category:** High  
        **Reasoning for Confidence:**  
        I am confident because the clinical text describes acute abdominal pain without evidence of an underlying condition. The code R10.9 directly matches the clinical presentation.

        **Note:** You may vary the wording of the confidence reasoning, but always justify your confidence level.
        ---
        **ACTUAL AUDIT TASK**
        **Chief Complaint:** "{chief_complaint}"
        **Clinical Text:** "{context}"
        **Candidate Codes:** {candidate_list}
        ---
        **Reasoning for ICD Code:**
        [Your one-sentence reasoning for choosing the code]
        **Chosen ICD-10 Code:**
        [The single best ICD-10 code]
        **Confidence Category:**
        [One of: Very High, High, Medium, Low, Very Low]
        **Reasoning for Confidence:**
        [Brief explanation for your confidence category]
        """
    
    def _format_candidates(self, candidate_codes: list) -> str:
        formatted_string = ""
        for i, code in enumerate(candidate_codes):
            description = self.icd_map.get(code, "No description found.")
            formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
        return formatted_string.strip()

    def select_final_code_and_confidence(self, chief_complaint: str, context: str, candidate_codes: list) -> tuple:
        if not candidate_codes:
            return ("", "No reasoning for ICD code", "Unknown", "No reasoning for confidence")
        
        prompt = self.prompt_template.format(
            chief_complaint=chief_complaint,
            context=context,
            candidate_list=self._format_candidates(candidate_codes)
        )
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Parse code
            code = ""
            code_match = re.search(r"Chosen ICD-10 Code[:\*]*\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
            if code_match:
                code = code_match.group(1).strip()
            
            # Parse confidence category
            confidence = "Unknown"
            confidence_match = re.search(r"Confidence Category[:\*]*\s*(Very High|High|Medium|Low|Very Low)", 
                                        response_text, re.IGNORECASE)
            if confidence_match:
                confidence = confidence_match.group(1).strip()
            
            # Parse reasoning for ICD code
            reasoning_icd = "No reasoning for ICD code"
            reasoning_icd_match = re.search(r"Reasoning for ICD Code[:\*]*\s*(.*?)(?:\n\*\*Chosen ICD-10 Code|\n\*\*Confidence Category|\n\*\*Reasoning for Confidence|\Z)", response_text, re.IGNORECASE | re.DOTALL)
            if reasoning_icd_match:
                reasoning_icd = reasoning_icd_match.group(1).strip()
            else:
                # Fallback: Try to find "Reasoning:" if the above fails (for backward compatibility)
                reasoning_icd_match = re.search(r"Reasoning[:\*]*\s*(.*?)(?=\n\*Chosen ICD-10 Code|\n\*Confidence Category|\Z)", 
                                               response_text, re.IGNORECASE | re.DOTALL)
                if reasoning_icd_match:
                    reasoning_icd = reasoning_icd_match.group(1).strip()

            # Parse reasoning for confidence
            reasoning_conf = "No reasoning for confidence"
            reasoning_conf_match = re.search(r"Reasoning for Confidence[:\*]*\s*(.*?)(?:\n\*\*Confidence Category|\n\*\*Reasoning for ICD Code|\Z)", response_text, re.IGNORECASE | re.DOTALL)
            if reasoning_conf_match:
                reasoning_conf = reasoning_conf_match.group(1).strip()

            # Validation
            normalized_candidates = [c.strip().upper() for c in candidate_codes]
            if code.strip().upper() not in normalized_candidates:
                print(f"   ⚠️ Extracted code '{code}' not in candidates. Reverting to Stage 4 concept.")
                return ("", "No reasoning for ICD code", "Unknown", "No reasoning for confidence")
            
            return (code, reasoning_icd, confidence, reasoning_conf)
        
        except Exception as e:
            print(f"   ⚠️ Error during LLM call: {e}")
            return ("", "No reasoning for ICD code", "Unknown", "No reasoning for confidence")

def run_reranking(input_path: str, kb_csv_path: str, output_path: str, batch_size: int, delay_between_batches: int = 15):
    try:
        genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw")
        llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0})
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return

    try:
        df_to_process = pd.read_csv(input_path)
        df_kb = pd.read_csv(kb_csv_path)
        icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()

        rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
        reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)

        print(f"--- Starting Final Selection Process (Batch Size: {batch_size}) ---")
        final_results = []

        for i in range(0, len(df_to_process), batch_size):
            batch_df = df_to_process.iloc[i : i + batch_size]
            print(f"\n--- Processing Batch {i//batch_size + 1} (Rows {i+1} to {i+len(batch_df)}) ---")

            for index, row in batch_df.iterrows():
                complaint = str(row['chief_complaint'])
                context = str(row['supporting_evidence'])
                candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
                concept_identifier = str(row['concept_identifier']) if pd.notna(row['concept_identifier']) else None

                if concept_identifier and concept_identifier not in candidate_codes:
                    candidate_codes.append(concept_identifier)

                print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
                print(f"   -> Initial Candidates: {candidate_codes}")
                
                filtered_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
                print(f"   -> Filtered Candidates: {filtered_candidates}")

                # Get LLM decision with reasoning and confidence
                code, reasoning_icd, confidence, reasoning_conf = reranker.select_final_code_and_confidence(
                    complaint, context, filtered_candidates
                )
        
                # Fallback mechanism
                if not code:
                    print("   -> ⚠️ LLM failed to identify valid code. Using Stage 4 concept.")
                    code = row.get('concept_identifier', '')
                    reasoning_icd = "Fallback to Stage 4 concept"
                    confidence = "Medium"
                    reasoning_conf = "Fallback to Stage 4 concept"
                
                print(f"   -> ✅ Final Code: '{code}' | Confidence: {confidence}")
                print(f"   -> Reasoning for ICD Code: {reasoning_icd}")
                print(f"   -> Reasoning for Confidence: {reasoning_conf}")

                final_results.append({
                    'chief_complaint': complaint,
                    'final_predicted_icd_code': code,
                    'reasoning_icd_code': reasoning_icd,
                    'confidence_category': confidence,
                    'reasoning_confidence': reasoning_conf
                })
                time.sleep(1)

            if (i + batch_size) < len(df_to_process):
                print(f"\n--- Batch Complete. Waiting {delay_between_batches} seconds... ---")
                time.sleep(delay_between_batches)

        output_df = pd.DataFrame(final_results)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

    except Exception as e:
        print(f"❌ An unexpected error occurred in Stage 6: {e}")