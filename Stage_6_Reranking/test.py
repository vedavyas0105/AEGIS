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

        ---
        **EXAMPLE:**
        **Chief Complaint:** "Leg edema"
        **Clinical Text:** "72 y/o F with a hx of CHF presents with worsening leg edema..."
        **Candidate Codes:** [`R60.0` (Edema), `I50.9` (Heart Failure)]
        **Reasoning for ICD Code:** Rule #1 (Diagnosis Precedence): The leg edema is a symptom of the established CHF diagnosis, so the code for the primary diagnosis is correct.
        **Chosen ICD-10 Code:** I50.9
        **Confidence Category:** High
        **Reasoning for Confidence:** I am confident because the context clearly describes CHF and the code directly matches the diagnosis.
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
            reasoning_icd_match = re.search(r"Reasoning for ICD Code[:\*]*\s*(.*?)(?=\n\*Chosen ICD-10 Code|\n\*Confidence Category|\Z)", 
                                           response_text, re.IGNORECASE | re.DOTALL)
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
            reasoning_conf_match = re.search(r"Reasoning for Confidence[:\*]*\s*(.*?)(?=\n\*Confidence Category|\n\*Reasoning for ICD Code|\Z)", 
                                           response_text, re.IGNORECASE | re.DOTALL)
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
        genai.configure(api_key="AIzaSyAbm0LFZav5iNse3DBBBA1f1cEchGZoVCw") # type: ignore
        llm_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": 0}) # type: ignore
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