# # import pandas as pd
# # import google.generativeai as genai
# # import time
# # import ast
# # import os
# # import re

# # class ICDReRanker:
# #     """Uses an expert-prompted LLM to perform the final re-ranking of candidate codes."""
# #     def __init__(self, model, icd_description_map: dict):
# #         self.model = model
# #         self.icd_map = icd_description_map
# #         # self.prompt_template = """
# #         # You are a Lead Coding Auditor. Your task is to audit the work of a junior coder by selecting the single most accurate and defensible ICD-10 code from the provided candidate list. You must strictly follow the audit checklist below.

# #         # ---
# #         # **Auditor's Checklist (Apply in this exact order):**

# #         # 1.  **Rule of Specificity:** This is the most important rule.
# #         #     *   **Semantic Match:** Does a candidate's description directly match the patient's complaint text (e.g., "Shortness of breath" for `R06.02`)? If so, it is strongly preferred over a general clinical synonym (e.g., "Dyspnea" for `R06.0`).
# #         #     *   **Hierarchical Match:** Always prefer a more specific child code (e.g., `M25.569`) over its general parent code (e.g., `M25.56`).

# #         # 2.  **Rule of Diagnosis Precedence:** An established diagnosis (e.g., "known T2DM") takes priority over its symptoms (e.g., "fatigue").

# #         # 3.  **Rule of Clinical Definition:** Do not infer a condition that isn't explicitly supported.
# #         #     *   A "persistent" cough of one week is **not** chronic. Do not choose the 'Chronic' code.
# #         #     *   "Forgets to take medicine" implies **underdosing**, not general noncompliance. Choose the code that best matches the specific action.

# #         # 4.  **Rule of Common Defaults:** For common, unspecified conditions, use the standard default code. For "Elevated blood pressure" without a specified cause, the correct default is `I10` (Essential Hypertension).

# #         # 5.  **Mandatory Reasoning:** Before making your selection, you must state your reasoning in one sentence, referencing the specific rule from this checklist.

# #         # ---
# #         # **AUDIT EXAMPLE 1 (Applying Rule #1 - Semantic Specificity)**
# #         # **Clinical Text:** "some sob on exertion"
# #         # **Candidate Codes:** [`R06.02` (Shortness of breath), `R06.00` (Dyspnea, unspecified), `R06.09` (Other dyspnea)]
# #         # **Reasoning:** Rule #1 (Semantic Match): `R06.02` is a direct textual match for "shortness of breath" and is therefore the most specific and accurate choice.
# #         # **Chosen ICD-10 Code:** R06.02
# #         # ---
# #         # **AUDIT EXAMPLE 2 (Applying Rule #3 - Clinical Definition)**
# #         # **Clinical Text:** "a persistent, dry cough for the past week."
# #         # **Candidate Codes:** [`R05.3` (Chronic cough), `R05` (Cough, unspecified)]
# #         # **Reasoning:** Rule #3 (Clinical Definition): The duration of one week does not meet the definition of chronic, making `R05` the only appropriate choice.
# #         # **Chosen ICD-10 Code:** R05
# #         # ---
# #         # **AUDIT EXAMPLE 3 (Applying Rule #4 - Common Defaults)**
# #         # **Clinical Text:** "BP in clinic is 165/95."
# #         # **Candidate Codes:** [`I1A` (Resistant hypertension), `I10` (Essential hypertension), `R03.0` (Elevated blood-pressure reading)]
# #         # **Reasoning:** Rule #4 (Common Defaults): With no mention of a cause, `I10` is the standard default code for a high blood pressure diagnosis.
# #         # **Chosen ICD-10 Code:** I10
# #         # ---

# #         # **ACTUAL AUDIT TASK**

# #         # **Clinical Text:**
# #         # "{context}"

# #         # **Candidate Codes:**
# #         # {candidate_list}

# #         # ---
# #         # **Reasoning:**
# #         # """
# #         self.prompt_template = """
# #         You are a Lead Coding Auditor. Your task is to audit the work of a junior coder by selecting the single most accurate and defensible ICD-10 code from the provided candidate list. You must strictly follow the audit checklist below.

# #         ---
# #         **Auditor's Checklist (Apply in this exact order):**

# #         1.  **Category Integrity:** First, ensure the code category matches the complaint. A rash is a dermatological issue ('L' or 'R' code), not an injury ('S' code). Discard any candidates from an obviously incorrect clinical category.

# #         2.  **Rule of Specificity:** From the remaining valid candidates, choose the one whose description is the most direct semantic and hierarchical match for the clinical text.

# #         3.  **Rule of Diagnosis Precedence:** An established diagnosis (e.g., "known CHF") takes priority over its symptoms (e.g., "leg edema").

# #         4.  **Rule of Common Defaults & Definitions:** Use standard defaults for common conditions (e.g., `I10` for hypertension) and respect clinical definitions (e.g., a one-week cough is not 'Chronic').

# #         5.  **Mandatory Reasoning:** Before making your selection, you must state your reasoning in one sentence, referencing the specific rule from this checklist.

# #         ---
# #         **AUDIT EXAMPLE 1 (Applying Rule #1 - Semantic Specificity)**
# #         **Clinical Text:** "some sob on exertion"
# #         **Candidate Codes:** [`R06.02` (Shortness of breath), `R06.00` (Dyspnea, unspecified), `R06.09` (Other dyspnea)]
# #         **Reasoning:** Rule #2 (Specificity): `R06.02` is a direct textual match for "shortness of breath" and is therefore the most specific and accurate choice.
# #         **Chosen ICD-10 Code:** R06.02
# #         ---
# #         **AUDIT EXAMPLE 2 (Applying Rule #3 - Diagnosis Precedence)**
# #         **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
# #         **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
# #         **Reasoning:** Rule #3 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
# #         **Chosen ICD-10 Code:** I50.9
# #         ---
# #         **AUDIT EXAMPLE 3 (Applying Rule #4 - Common Defaults)**
# #         **Clinical Text:** "BP in clinic is 165/95."
# #         **Candidate Codes:** [`I1A` (Resistant hypertension), `I10` (Essential hypertension)]
# #         **Reasoning:** Rule #4 (Common Defaults): With no mention of a cause, `I10` is the standard default code for a high blood pressure diagnosis.
# #         **Chosen ICD-10 Code:** I10
# #         ---

# #         **ACTUAL AUDIT TASK**

# #         **Clinical Text:**
# #         "{context}"

# #         **Candidate Codes:**
# #         {candidate_list}

# #         ---
# #         **Reasoning:**
# #         [Your one-sentence reasoning based on the checklist]
# #         **Chosen ICD-10 Code:**
# #         [The single best ICD-10 code]
# #         **Confidence (0-100%):**
# #         [Your confidence in this selection as a numerical percentage]
# #         """

# #     def _format_candidates(self, candidate_codes: list) -> str:
# #         """Helper function to format the candidate list for the prompt."""
# #         formatted_string = ""
# #         for i, code in enumerate(candidate_codes):
# #             description = self.icd_map.get(code, "No description found.")
# #             formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
# #         return formatted_string.strip()

# #     def select_final_code(self, context: str, candidate_codes: list) -> tuple[str, int]:
# #         """Selects the best code using hierarchical parsing."""
# #         if not candidate_codes:
# #             return "", 0
        
# #         # The prompt is now much more powerful
# #         prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
        
# #         final_code = ""
# #         confidence = 0 # Default confidence is 0

# #         try:
# #             response = self.model.generate_content(prompt)
# #             response_text = response.text.strip()

# #             # --- NEW PARSING LOGIC ---
# #             # Use regular expressions to find the code and confidence score
            
# #             # 1. Parse the ICD Code
# #             code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
# #             if code_match:
# #                 code = code_match.group(1).strip()
# #                 # Validate that the extracted code was one of the original candidates
# #                 if code in candidate_codes:
# #                     final_code = code

# #             # 2. Parse the Confidence Score
# #             confidence_match = re.search(r"Confidence \(0-100%\):\s*(\d{1,3})%?", response_text)
# #             if confidence_match:
# #                 # Convert the extracted string '95' to an integer 95
# #                 confidence = int(confidence_match.group(1))

# #             # Return both extracted values
# #             return final_code, confidence
        
# #         except Exception as e:
# #             print(f"   ⚠️ Error during parsing in select_final_code: {e}")
# #             # If anything goes wrong, return empty/zero values
# #             return "", 0
        
# # class ClinicalInferenceEngine:
# #     """
# #     Performs a final check to see if a symptom code can be replaced
# #     by a more specific, inferred underlying diagnosis.
# #     """
# #     def __init__(self, model):
# #         self.model = model
# #         self.prompt_template = """
# #         You are a senior medical detective. A junior coder has selected an initial
# #         ICD-10 code for a symptom. Your task is to review the clinical text and
# #         determine if the evidence points to a more specific underlying **diagnosis**
# #         that is the root cause of the symptom.

# #         **Rules:**
# #         - If the context provides strong clues (e.g., medications, history) for an
# #           underlying disease, return the ICD-10 code for that **disease**.
# #         - If the evidence is insufficient or the symptom is the only clear issue,
# #           return the original symptom code.
# #         - Your response MUST be ONLY the single, final ICD-10 code.

# #         ---
# #         **EXAMPLE**
# #         **Clinical Text:** "wheezing + tight chest, used inhaler 2x"
# #         **Initial Symptom Code:** "R06.2" (Wheezing)
# #         **Your Inferred Diagnosis Code:** J45.909
# #         *(Reasoning: The mention of an "inhaler" is a strong contextual clue for Asthma.)*
# #         ---
        
# #         **ACTUAL TASK**
# #         **Clinical Text:**
# #         "{context}"

# #         **Initial Symptom Code:**
# #         "{initial_code}"
# #         ---
# #         **Your Inferred Diagnosis Code:**
# #         """
# #     def check_for_underlying_diagnosis(self, context: str, initial_code: str) -> str:
# #         """
# #         Returns a more specific diagnosis code if found, otherwise returns the initial code.
# #         """
# #         # We only run this check if the initial code is a symptom (usually R-codes)
# #         if not initial_code or not initial_code.startswith('R'):
# #             return initial_code

# #         prompt = self.prompt_template.format(context=context, initial_code=initial_code)
# #         try:
# #             response = self.model.generate_content(prompt)
# #             inferred_code = response.text.strip()
# #             # Basic validation: ensure the response is a plausible code format
# #             if inferred_code and (inferred_code[0].isalpha() and inferred_code[1].isdigit()):
# #                 return inferred_code
# #             return initial_code # Return original if response is invalid
# #         except Exception as e:
# #             print(f"   ⚠️ LLM Error during inference chec`k: {e}")
# #             # If the check fails, safely return the original code.
# #             return initial_code

# # def run_reranking(input_path: str, kb_csv_path: str, output_path: str):
# #     """Executes Stage 6 with the new, two-step inference process."""
# #     try:
# #         # NOTE: Ensure your API key is handled securely, e.g., via environment variables
# #         genai.configure(api_key="AIzaSyBwkGSTkakVfMRJ8zVSwgbU41ieuSFubjU") # type: ignore
# #         llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
# #     except Exception as e:
# #         print(f"❌ Error configuring Gemini API: {e}"); return
    
# #     try:
# #         df_to_process = pd.read_csv(input_path)
# #         df_kb = pd.read_csv(kb_csv_path)
# #         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
# #         # Initialize both of our expert classes
# #         reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)
# #         inference_checker = ClinicalInferenceEngine(model=llm_model)
        
# #         print("--- Starting Final Selection Process (with Inference Check) ---")
# #         final_predictions = []
# #         for index, row in df_to_process.iterrows():
# #             context = str(row['supporting_evidence'])
# #             candidate_codes = ast.literal_eval(row['candidate_icd_codes']) if pd.notna(row['candidate_icd_codes']) else []
# #             stage4_fallback_code = str(row.get('concept_identifier', ''))

# #             print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{row['chief_complaint']}'") # type: ignore
            
# #             # --- Step 1: Initial Selection ---
# #             initial_code = ""
# #             if not candidate_codes:
# #                 initial_code = stage4_fallback_code
# #             elif len(candidate_codes) == 1:
# #                 initial_code = candidate_codes[0]
# #             else:
# #                 initial_code, confidence = reranker.select_final_code(context=context, candidate_codes=candidate_codes)
# #                 if not initial_code: # Fallback if re-ranker fails
# #                     initial_code = stage4_fallback_code
            
# #             print(f"   -> Initial Selected Code: '{initial_code}' with Confidence: {confidence}%")
            
# #             # --- Step 2: Clinical Inference Check ---
# #             # This check is only performed if we have a valid initial code.
# #             if initial_code:
# #                 final_code = inference_checker.check_for_underlying_diagnosis(context, initial_code)
# #                 if final_code != initial_code:
# #                     print(f"   -> Inference Check Replaced Code. Final Code: '{final_code}'")
# #             else:
# #                 final_code = "" # Ensure it's an empty string if no code was ever found
            
# #             final_predictions.append(final_code)
# #             time.sleep(3) # Basic rate limiting

# #         df_to_process['final_predicted_icd_code'] = final_predictions
# #         output_df = df_to_process[['chief_complaint', 'final_predicted_icd_code']]
        
# #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# #         output_df.to_csv(output_path, index=False, encoding='utf-8')
# #         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# #     except Exception as e:
# #         print(f"❌ An unexpected error occurred in Stage 6: {e}")

# # Stage_6_Reranking/reranker.py
# # import pandas as pd
# # import google.generativeai as genai
# # import time
# # import ast
# # import os
# # import re

# # def specificity_filter(candidate_codes: list) -> list:
# #     """
# #     Applies a deterministic filter to remove less specific parent codes
# #     when a more specific child code is present. This version is more robust.
# #     """
# #     if not candidate_codes or len(candidate_codes) <= 1:
# #         return candidate_codes

# #     # Create a set for efficient lookups
# #     codes_set = set(candidate_codes)
# #     codes_to_remove = set()

# #     for code in codes_set:
# #         # A potential parent code is a prefix of the current code, and is shorter.
# #         # Example: 'J45' is a prefix of 'J45.909'.
# #         for other_code in codes_set:
# #             if code != other_code and code.startswith(other_code) and len(code) > len(other_code):
# #                 # 'other_code' is a parent of 'code'. Mark it for removal.
# #                 codes_to_remove.add(other_code)
    
# #     # Return a new list containing only the codes that were not marked for removal.
# #     # Preserve the original order of the candidates if possible.
# #     return [code for code in candidate_codes if code not in codes_to_remove]

# # class ICDReRanker:
# #     """Uses an expert-prompted LLM to perform the final re-ranking and confidence scoring."""
# #     def __init__(self, model, icd_description_map: dict):
# #         self.model = model
# #         self.icd_map = icd_description_map
# #         # The definitive "Platinum Standard" prompt
# #         self.prompt_template = """
# #         You are a Lead Coding Auditor. Your task is to audit the work of a junior coder by selecting the single most accurate and defensible ICD-10 code from the provided candidate list. You must strictly follow the audit checklist below.

# #         ---
# #         **Auditor's Checklist (Apply in this exact order):**

# #         1.  **Category Integrity:** First, ensure the code category matches the complaint. A rash is a dermatological issue ('L' or 'R' code), not an injury ('S' code). Discard any candidates from an obviously incorrect clinical category.
# #         2.  **Rule of Specificity:** From the remaining valid candidates, choose the one whose description is the most direct semantic and hierarchical match for the clinical text.
# #         3.  **Rule of Diagnosis Precedence:** An established diagnosis (e.g., "known CHF") takes priority over its symptoms (e.g., "leg edema").
# #         4.  **Rule of Common Defaults & Definitions:** Use standard defaults for common conditions (e.g., `I10` for hypertension) and respect clinical definitions (e.g., a one-week cough is not 'Chronic').
# #         5.  **Mandatory Reasoning:** Before making your selection, you must state your reasoning in one sentence, referencing the specific rule from this checklist.

# #         ---
# #         **AUDIT EXAMPLE 1 (Applying Rule #2 - Specificity)**
# #         **Clinical Text:** "some sob on exertion"
# #         **Candidate Codes:** [`R06.02` (Shortness of breath), `R06.00` (Dyspnea, unspecified), `R06.09` (Other dyspnea)]
# #         **Reasoning:** Rule #2 (Specificity): `R06.02` is a direct textual match for "shortness of breath" and is therefore the most specific and accurate choice.
# #         **Chosen ICD-10 Code:** R06.02
# #         ---
# #         **AUDIT EXAMPLE 2 (Applying Rule #3 - Diagnosis Precedence)**
# #         **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
# #         **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
# #         **Reasoning:** Rule #3 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
# #         **Chosen ICD-10 Code:** I50.9
# #         ---
# #         **ACTUAL AUDIT TASK**

# #         **Clinical Text:**
# #         "{context}"

# #         **Candidate Codes:**
# #         {candidate_list}
# #         ---
# #         **Reasoning:**
# #         [Your one-sentence reasoning based on the checklist]
# #         **Chosen ICD-10 Code:**
# #         [The single best ICD-10 code]
# #         **Confidence (0-100%):**
# #         [Your confidence in this selection as a numerical percentage]
# #         """

# #     def _format_candidates(self, candidate_codes: list) -> str:
# #         """Helper function to format the candidate list for the prompt."""
# #         formatted_string = ""
# #         for i, code in enumerate(candidate_codes):
# #             description = self.icd_map.get(code, "No description found.")
# #             formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
# #         return formatted_string.strip()

# #     def select_final_code(self, context: str, candidate_codes: list) -> tuple[str, int]:
# #         """Selects the best code and extracts the confidence score."""
# #         if not candidate_codes:
# #             return "", 0
        
# #         prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
# #         final_code = ""
# #         confidence = 0

# #         try:
# #             response = self.model.generate_content(prompt)
# #             response_text = response.text.strip()
            
# #             code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
# #             if code_match:
# #                 code = code_match.group(1).strip()
# #                 if code in candidate_codes:
# #                     final_code = code

# #             confidence_match = re.search(r"Confidence(?: Score)?\s*(?:\(0-100%\))?:\s*(\d{1,3})%?", response_text, re.IGNORECASE)
# #             if confidence_match:
# #                 confidence = int(confidence_match.group(1))

# #             return final_code, confidence
# #         except Exception as e:
# #             print(f"   ⚠️ Error during parsing in select_final_code: {e}")
# #             return "", 0
        
# # class ClinicalInferenceEngine:
# #     """Performs a final check to see if a symptom code can be replaced by a more specific, inferred underlying diagnosis."""
# #     def __init__(self, model):
# #         self.model = model
# #         self.prompt_template = """
# #         You are a senior medical detective...
# #         (The rest of this prompt from your file is correct and remains unchanged)
# #         """

# #     def check_for_underlying_diagnosis(self, context: str, initial_code: str) -> str:
# #         """Returns a more specific diagnosis code if found, otherwise returns the initial code."""
# #         if not initial_code or not initial_code.startswith('R'):
# #             return initial_code

# #         prompt = self.prompt_template.format(context=context, initial_code=initial_code)
# #         try:
# #             response = self.model.generate_content(prompt)
# #             inferred_code = response.text.strip()
# #             if inferred_code and (inferred_code[0].isalpha() and inferred_code[1].isdigit()):
# #                 return inferred_code
# #             return initial_code
# #         except Exception as e:
# #             print(f"   ⚠️ LLM Error during inference check: {e}")
# #             return initial_code

# # def run_reranking(input_path: str, kb_csv_path: str, output_path: str):
# #     """Executes Stage 6 with the new, hybrid rule-based and AI logic."""
# #     try:
# #         # NOTE: Handle your API key securely, e.g., using environment variables.
# #         genai.configure(api_key="AIzaSyBwkGSTkakVfMRJ8zVSwgbU41ieuSFubjU") #type: ignore
# #         llm_model = genai.GenerativeModel('gemini-2.0-latest', generation_config={"temperature": 0}) #type: ignore
# #     except Exception as e:
# #         print(f"❌ Error configuring Gemini API: {e}"); return
    
# #     try:
# #         df_to_process = pd.read_csv(input_path)
# #         df_kb = pd.read_csv(kb_csv_path)
# #         icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
# #         reranker = ICDReRanker(model=llm_model, icd_description_map=icd_description_map)
# #         inference_checker = ClinicalInferenceEngine(model=llm_model)
        
# #         print("--- Starting Final Selection Process (Hybrid Logic) ---")
# #         final_results = []
# #         for index, row in df_to_process.iterrows():
# #             context = str(row['supporting_evidence'])
# #             candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
# #             stage4_fallback_code = str(row.get('concept_identifier', ''))

# #             print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{row['chief_complaint']}'")
# #             print(f"   -> Initial Candidates: {candidate_codes}")

# #             # --- NEW HYBRID LOGIC ---
# #             initial_code = ""
# #             confidence = 0
            
# #             # 1. Apply the deterministic rule-based filter FIRST.
# #             filtered_candidates = specificity_filter(candidate_codes)
# #             if len(filtered_candidates) != len(candidate_codes):
# #                  print(f"   -> Specificity Filter Applied. Refined Candidates: {filtered_candidates}")
            
# #             # 2. Decide the next step based on the filter's output.
# #             if not filtered_candidates:
# #                 initial_code = stage4_fallback_code
# #                 confidence = 50 # Lower confidence for fallbacks
# #             elif len(filtered_candidates) == 1:
# #                 initial_code = filtered_candidates[0]
# #                 confidence = 100 # Rule-based decisions are 100% confident
# #                 print(f"   -> Decided by Specificity Filter.")
# #             else:
# #                 # 3. Only if ambiguity remains, call the LLM Auditor.
# #                 print(f"   -> Ambiguity remains. Escalating to LLM Auditor...")
# #                 initial_code, confidence = reranker.select_final_code(context=context, candidate_codes=filtered_candidates)
# #                 if not initial_code: # Fallback if re-ranker fails
# #                     initial_code = stage4_fallback_code
# #                     confidence = 50

# #             print(f"   -> Initial Selected Code: '{initial_code}' with Confidence: {confidence}%")

# #             # 4. The final inference check remains the same.
# #             final_code = inference_checker.check_for_underlying_diagnosis(context, initial_code)
# #             if final_code != initial_code:
# #                 print(f"   -> Inference Check Replaced Code. Final Code: '{final_code}'")
            
# #             final_results.append({
# #                 'chief_complaint': row['chief_complaint'],
# #                 'final_predicted_icd_code': final_code,
# #                 'confidence_score': confidence
# #             })
# #             time.sleep(1) # Basic rate limiting

# #         output_df = pd.DataFrame(final_results)
# #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# #         output_df.to_csv(output_path, index=False, encoding='utf-8')
# #         print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# #     except Exception as e:
# #         print(f"❌ An unexpected error occurred in Stage 6: {e}")

# # Stage_6_Reranking/reranker.py
# # Stage_6_Reranking/reranker.py
# import pandas as pd
# import google.generativeai as genai
# import time
# import ast
# import os
# import re
# from collections import Counter
# import asyncio

# # --- IMPORTING DEFAULTS FROM THE SEPARATE FILE ---
# from .clinical_defaults import COMMON_DEFAULTS_MAP

# # --- ARCHITECTURAL UPGRADE 1: A DETERMINISTIC RULES ENGINE ---
# class RulesEngine:
#     """A deterministic engine to apply hard-coded clinical coding rules."""
#     def __init__(self, defaults_map: dict):
#         self.COMMON_DEFAULTS = defaults_map
#         self.icd_map = {}

#     def _filter_by_specificity(self, codes: list) -> list:
#         """Removes less specific parent codes when a more specific child code exists."""
#         if not codes or len(codes) <= 1:
#             return codes
        
#         # Sort codes by length descending to ensure we check children before parents
#         sorted_codes = sorted(codes, key=len, reverse=True)
        
#         codes_to_keep = set(sorted_codes)
        
#         for code in sorted_codes:
#             # Find potential parents (shorter prefixes of the current code)
#             for i in range(len(code) - 1, 2, -1): # Iterate backwards from len-1 down to 3
#                 prefix = code[:i]
#                 if prefix in codes_to_keep:
#                     codes_to_keep.remove(prefix)

#         # Return a list that preserves original order as much as possible
#         return [c for c in codes if c in codes_to_keep]

#     def _filter_by_category(self, complaint: str, codes: list) -> list:
#         """Removes codes from clinically inappropriate categories."""
#         complaint_lower = complaint.lower()
#         if "rash" in complaint_lower or "pruritic" in complaint_lower:
#             return [code for code in codes if code.startswith('L') or code.startswith('R')]
#         if "fall" in complaint_lower or "injury" in complaint_lower:
#             return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
#         return codes

#     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
#         """Checks if a common default code can be applied for a generic complaint."""
#         complaint_lower = complaint.lower().strip()
#         if complaint_lower in self.COMMON_DEFAULTS:
#             default_code = self.COMMON_DEFAULTS[complaint_lower]
#             if default_code in codes:
#                 return [default_code]
#         for key, default_code in self.COMMON_DEFAULTS.items():
#             if key in complaint_lower and default_code in codes:
#                 return [default_code]
#         return codes

#     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
#         """
#         Runs the full sequence of rule-based filters in the correct, safer order.
#         """
#         if not candidates: return []
        
#         self.icd_map = icd_map
        
#         # Step 1: Filter by clinical category first to remove nonsensical options.
#         filtered_codes = self._filter_by_category(complaint, candidates)
        
#         # Step 2: Apply the crucial specificity filter.
#         filtered_codes = self._filter_by_specificity(filtered_codes)
        
#         # Step 3: ONLY if ambiguity still exists, check for a common default.
#         # This is now the last rule, preventing it from overriding more specific codes.
#         if len(filtered_codes) > 1:
#             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
#         return filtered_codes

# # class RulesEngine:
# #     """A deterministic engine with a corrected rule application hierarchy."""
# #     def __init__(self, defaults_map: dict):
# #         self.COMMON_DEFAULTS = defaults_map
# #         self.icd_map = {}

# #     def _filter_by_specificity(self, codes: list) -> list:
# #         """A more robust specificity filter."""
# #         if not codes or len(codes) <= 1:
# #             return codes
        
# #         sorted_codes = sorted(codes, key=len, reverse=True)
# #         codes_to_keep = set(sorted_codes)
        
# #         for code in sorted_codes:
# #             for i in range(len(code) - 1, 2, -1):
# #                 prefix = code[:i]
# #                 if prefix in codes_to_keep:
# #                     codes_to_keep.remove(prefix)

# #         return [c for c in codes if c in codes_to_keep]

# #     def _filter_by_category(self, complaint: str, codes: list) -> list:
# #         """Removes codes from clinically inappropriate categories."""
# #         # This function can be expanded with more rules
# #         return codes

# #     def _apply_common_defaults(self, complaint: str, codes: list) -> list:
# #         """Checks for a common default code, now used as a last resort."""
# #         complaint_lower = complaint.lower().strip()
# #         if complaint_lower in self.COMMON_DEFAULTS:
# #             default_code = self.COMMON_DEFAULTS[complaint_lower]
# #             if default_code in codes:
# #                 return [default_code]
# #         return codes

# #     def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
# #         """
# #         Runs the full sequence of rule-based filters in the correct, safer order.
# #         """
# #         if not candidates: return []
# #         self.icd_map = icd_map
        
# #         # Step 1: Filter by clinical category first.
# #         filtered_codes = self._filter_by_category(complaint, candidates)
        
# #         # Step 2: Apply the crucial specificity filter.
# #         filtered_codes = self._filter_by_specificity(filtered_codes)
        
# #         # Step 3: ONLY if ambiguity still exists, check for a common default.
# #         if len(filtered_codes) > 1:
# #             filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
# #         return filtered_codes

# # --- LLM "AUDITOR" CLASS FOR COMPLEX CASES ---
# class ICDReRanker:
#     """The LLM agent, now focused only on complex clinical tie-breaking."""
#     def __init__(self, model, icd_description_map: dict):
#         self.model = model
#         self.icd_map = icd_description_map
#         self.prompt_template = """
#         You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

#         **Auditor's Checklist:**
#         1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
#         2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
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
#         # ... same as before
#         pass

#     async def select_final_code_async(self, context: str, candidate_codes: list) -> str:
#         """Async version of the LLM call for concurrent execution."""
#         if not candidate_codes: return ""
#         prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
#         try:
#             # Use the async version of the generate_content method
#             response = await self.model.generate_content_async(prompt)
#             response_text = response.text.strip()
#             code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
#             if code_match:
#                 code = code_match.group(1).strip()
#                 if code in candidate_codes:
#                     return code
#             return ""
#         except Exception as e:
#             print(f"   ⚠️ Async LLM call failed: {e}")
#             return ""

# # --- MAIN ORCHESTRATOR FUNCTION WITH GENERALIZED & ASYNC LOGIC ---
# async def run_reranking_async(input_path: str, kb_csv_path: str, output_path: str, n_samples=5):
#     """The async main function to run the entire Stage 6 process."""
#     try:
#         genai.configure(api_key="AIzaSyBwkGSTkakVfMRJ8zVSwgbU41ieuSFubjU")
#         # We only need one model instance for async calls
#         stochastic_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0.2})
#     except Exception as e:
#         print(f"❌ Error configuring Gemini API: {e}"); return
    
#     df_to_process = pd.read_csv(input_path)
#     df_kb = pd.read_csv(kb_csv_path)
#     icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
    
#     rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
#     reranker = ICDReRanker(model=stochastic_model, icd_description_map=icd_description_map)

#     print("--- Starting Final Selection Process (Generalized Hybrid Logic) ---")
#     final_results = []
    
#     for index, row in df_to_process.iterrows():
#         complaint = str(row['chief_complaint'])
#         context = str(row['supporting_evidence'])
#         candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
        
#         print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
#         print(f"   -> Initial Candidates: {candidate_codes}")
        
#         final_code = ""
#         confidence = 0

#         rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
        
#         if len(rule_based_candidates) != len(candidate_codes):
#             print(f"   -> Rules Engine Applied. Refined Candidates: {rule_based_candidates}")

#         if len(rule_based_candidates) == 1:
#             final_code = rule_based_candidates[0]
#             confidence = 100
#             print(f"   -> ✅ Decided by Rules Engine.")
#         elif len(rule_based_candidates) > 1:
#             print(f"   ->  Escalating to LLM Auditor for Self-Consistency...")
#             tasks = [reranker.select_final_code_async(context, rule_based_candidates) for _ in range(n_samples)]
#             llm_predictions = await asyncio.gather(*tasks, return_exceptions=True)
            
#             valid_predictions = [p for p in llm_predictions if p and not isinstance(p, Exception)]
            
#             if valid_predictions:
#                 vote_count = Counter(valid_predictions)
#                 most_common = vote_count.most_common(1)[0]
#                 final_code = most_common[0]
#                 confidence = (most_common[1] / len(valid_predictions)) * 100
#                 print(f"   -> ✅ LLM Consensus Chose: '{final_code}' with {confidence:.0f}% confidence.")
        
#         if not final_code:
#             final_code = row.get('concept_identifier', '')
#             confidence = 20
#             print(f"   -> ⚠️ No definitive code found. Using fallback.")
            
#         final_results.append({'chief_complaint': complaint, 'final_predicted_icd_code': final_code, 'confidence_score': confidence})

#     output_df = pd.DataFrame(final_results)
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     output_df.to_csv(output_path, index=False, encoding='utf-8')
#     print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

# # --- Wrapper to run the async function from a synchronous context ---
# def run_reranking(input_path: str, kb_csv_path: str, output_path: str, n_samples=5):
#     """Synchronous wrapper for the main async function."""
#     try:
#         asyncio.run(run_reranking_async(input_path, kb_csv_path, output_path, n_samples))
#     except RuntimeError as e:
#         # This handles cases where an event loop is already running (e.g., in Jupyter/Streamlit)
#         if "cannot run loop while another loop is running" in str(e):
#             import nest_asyncio
#             nest_asyncio.apply()
#             asyncio.run(run_reranking_async(input_path, kb_csv_path, output_path, n_samples))
#         else:
#             raise e

# Stage_6_Reranking/reranker.py
import pandas as pd
import google.generativeai as genai
import time
import ast
import os
import re
from .clinical_defaults import COMMON_DEFAULTS_MAP

# --- ARCHITECTURAL UPGRADE 1: A DETERMINISTIC RULES ENGINE ---
class RulesEngine:
    """
    A deterministic engine to apply hard-coded clinical coding rules before
    escalating to a probabilistic LLM.
    """

    def _filter_by_specificity(self, codes: list) -> list:
        """Removes less specific parent codes when a more specific child code exists."""
        if not codes or len(codes) <= 1:
            return codes
        
        codes_set = set(codes)
        to_remove = {c2 for c1 in codes_set for c2 in codes_set if c1 != c2 and c1.startswith(c2) and len(c1) > len(c2)}
        return [code for code in codes if code not in to_remove]

    def _filter_by_category(self, complaint: str, codes: list) -> list:
        """Removes codes from clinically inappropriate categories."""
        complaint_lower = complaint.lower()
        if "rash" in complaint_lower or "pruritic" in complaint_lower:
            # A rash is a symptom (R) or dermatological (L) issue, not an injury (S).
            return [code for code in codes if code.startswith('L') or code.startswith('R')]
        if "fall" in complaint_lower or "injury" in complaint_lower:
            # A fall or injury should not be coded as a general symptom or disease unless specified.
            return [code for code in codes if code.startswith(('S', 'T', 'W')) or "fall" in self.icd_map.get(code, "").lower()]
        return codes

    def _apply_common_defaults(self, complaint: str, codes: list) -> list:
        """Checks if a common default code can be applied."""
        complaint_lower = complaint.lower().strip()
        
        # Check for an exact match first for higher precision
        if complaint_lower in self.COMMON_DEFAULTS:
            default_code = self.COMMON_DEFAULTS[complaint_lower]
            if default_code in codes:
                return [default_code]
        
        # Then check for partial matches (as before)
        for key, default_code in self.COMMON_DEFAULTS.items():
            if key in complaint_lower and default_code in codes:
                return [default_code]
        
        return codes

    def apply_all_rules(self, complaint: str, candidates: list, icd_map: dict) -> list:
        """Runs the full sequence of rule-based filters."""
        if not candidates:
            return []
        
        self.icd_map = icd_map
        filtered_codes = self._filter_by_specificity(candidates)
        filtered_codes = self._filter_by_category(complaint, filtered_codes)
        filtered_codes = self._apply_common_defaults(complaint, filtered_codes)
        
        return filtered_codes

# --- LLM "AUDITOR" CLASS FOR COMPLEX CASES ---
class ICDReRanker:
    """The LLM agent, now focused only on complex clinical tie-breaking."""
    def __init__(self, model, icd_description_map: dict):
        self.model = model
        self.icd_map = icd_description_map
        self.prompt_template = """
        You are a Lead Coding Auditor. The easy cases have been filtered out. Your task is to resolve a clinically ambiguous case by selecting the single best ICD-10 code from the provided candidate list. Strictly follow the checklist below.

        **Auditor's Checklist:**
        1.  **Diagnosis Precedence:** Prioritize a diagnosed disease over its symptoms (e.g., Heart Failure over Edema if context supports it).
        2.  **Best Semantic Match:** Choose the code whose description most closely matches the clinical nuance of the complaint.
        3.  **Mandatory Reasoning:** State your reasoning in one sentence based on the checklist.
        ---
        **EXAMPLE:**
        **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
        **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
        **Reasoning:** Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
        **Chosen ICD-10 Code:** I50.9
        ---
        **ACTUAL AUDIT TASK**
        **Clinical Text:** "{context}"
        **Candidate Codes:** {candidate_list}
        ---
        **Reasoning:**
        [Your one-sentence reasoning]
        **Chosen ICD-10 Code:**
        [The single best ICD-10 code]
        """
    
    def _format_candidates(self, candidate_codes: list) -> str:
        formatted_string = ""
        for i, code in enumerate(candidate_codes):
            description = self.icd_map.get(code, "No description found.")
            formatted_string += f"{i+1}. Code: {code}, Description: \"{description}\"\n"
        return formatted_string.strip()

    def select_final_code(self, context: str, candidate_codes: list) -> str:
        """Selects the best code and returns only the code string."""
        if not candidate_codes: return ""
        prompt = self.prompt_template.format(context=context, candidate_list=self._format_candidates(candidate_codes))
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            code_match = re.search(r"Chosen ICD-10 Code:\s*([A-Z0-9\.]+)", response_text, re.IGNORECASE)
            if code_match:
                code = code_match.group(1).strip()
                if code in candidate_codes:
                    return code
            return ""
        except Exception:
            return ""

# --- FINAL INFERENCE CHECKER (Unchanged but included for completeness) ---
class ClinicalInferenceEngine:
    def __init__(self, model):
        self.model = model
        self.prompt_template = """...""" # Your existing prompt here
    def check_for_underlying_diagnosis(self, context: str, initial_code: str) -> str:
        # Your existing logic here
        pass

# --- MAIN ORCHESTRATOR FUNCTION WITH GENERALIZED LOGIC ---
def run_reranking(input_path: str, kb_csv_path: str, output_path: str, n_samples=5):
    """Executes Stage 6 with the generalized, hybrid architecture."""
    try:
        genai.configure(api_key="AIzaSyBwkGSTkakVfMRJ8zVSwgbU41ieuSFubjU")
        # deterministic_model = genai.GenerativeModel('gemini-1.5-flash-latest', generation_config={"temperature": 0})
        stochastic_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0})
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}"); return
    
    try:
        df_to_process = pd.read_csv(input_path)
        df_kb = pd.read_csv(kb_csv_path)
        icd_description_map = pd.Series(df_kb.Description.values, index=df_kb.CUI).to_dict()
        
        rules_engine = RulesEngine(defaults_map=COMMON_DEFAULTS_MAP)
        reranker = ICDReRanker(model=stochastic_model, icd_description_map=icd_description_map)
        # inference_checker = ClinicalInferenceEngine(model=deterministic_model) # Optional final check

        print("--- Starting Final Selection Process (Generalized Hybrid Logic) ---")
        final_results = []
        for index, row in df_to_process.iterrows():
            complaint = str(row['chief_complaint'])
            context = str(row['supporting_evidence'])
            candidate_codes = ast.literal_eval(str(row['candidate_icd_codes'])) if pd.notna(row['candidate_icd_codes']) else []
            
            print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'")
            print(f"   -> Initial Candidates: {candidate_codes}")
            
            final_code = ""
            confidence = 0

            # 1. Apply the deterministic Rules Engine FIRST.
            rule_based_candidates = rules_engine.apply_all_rules(complaint, candidate_codes, icd_description_map)
            
            if len(rule_based_candidates) != len(candidate_codes):
                print(f"   -> Rules Engine Applied. Refined Candidates: {rule_based_candidates}")

            if len(rule_based_candidates) == 1:
                final_code = rule_based_candidates[0]
                confidence = 100
                print(f"   -> ✅ Decided by Rules Engine.")
            elif len(rule_based_candidates) > 1:
                # 2. If ambiguity remains, use Self-Consistency with the LLM.
                print(f"   ->  Escalating to LLM Auditor for Self-Consistency...")
                llm_predictions = []
                for _ in range(n_samples):
                    code = reranker.select_final_code(context, rule_based_candidates)
                    if code:
                        llm_predictions.append(code)
                
                if llm_predictions:
                    vote_count = Counter(llm_predictions)
                    most_common = vote_count.most_common(1)[0]
                    final_code = most_common[0]
                    confidence = (most_common[1] / len(llm_predictions)) * 100
                    print(f"   -> ✅ LLM Consensus Chose: '{final_code}' with {confidence:.0f}% confidence.")
            
            if not final_code:
                final_code = row.get('concept_identifier', '')
                confidence = 20 # Low confidence for fallbacks
                print(f"   -> ⚠️ No definitive code found. Using fallback.")

            # Optional: final_code = inference_checker.check_for_underlying_diagnosis(context, final_code)
            
            final_results.append({
                'chief_complaint': complaint,
                'final_predicted_icd_code': final_code,
                'confidence_score': confidence
            })
            time.sleep(1)

        output_df = pd.DataFrame(final_results)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n🎉 Pipeline Complete! Final predictions saved to '{output_path}'.")

    except Exception as e:
        print(f"❌ An unexpected error occurred in Stage 6: {e}")