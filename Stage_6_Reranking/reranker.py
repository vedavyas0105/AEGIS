import pandas as pd
import google.generativeai as genai
import time
import ast
import os
import re
import config

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
        genai.configure(api_key=config.STAGE_6_GEMINI_API_KEY) # type: ignore
        llm_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME, generation_config={"temperature": 0}) # type: ignore
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

                print(f"\nProcessing complaint ({index + 1}/{len(df_to_process)}): '{complaint}'") # type: ignore
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