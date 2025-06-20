import re

class LLMClassifier:
    """
    Uses a Large Language Model to select the most accurate concept (and its
    identifier) from a list of candidates, based on the provided clinical context.
    This implements the "expert selector" substage of the pipeline.
    """
    def __init__(self, model):
        """
        Initializes the classifier with a configured generative model.
        """
        self.model = model
        # This prompt is engineered to be a pure selection task.
        # self.prompt_template = """
        # You are an expert clinical terminologist. Your task is to select the single most
        # accurate ICD-10 Code from the provided list of candidates that matches the medical complaint.

        # Use the "Clinical Context" to understand the situation. The "Complaint Text" is the
        # specific phrase you need to map. The "Candidate Concepts" are your options, each with
        # an identifier and a description.

        # **CRITICAL RULE: You MUST validate your choice against the patient's sex.** Do not select a gender-specific code (e.g., for pregnancy, childbirth, or male/female-specific conditions) if it contradicts the provided `patient_sex`. A violation of this rule is a critical failure.

        # Analyze the candidates and select the one that is the most precise and relevant match.

        # IMPORTANT: Your response MUST be ONLY the identifier string from the best matching candidate
        # (e.g., 'J06.9' or 'I10'). Do not add any explanation, preamble, or any text other than the chosen identifier.

        # ---
        # **Clinical Context:**
        # {context}

        # **Complaint Text to Map:**
        # "{normalized_text}"

        # **Candidate Concepts:**
        # {candidate_list}
        # ---

        # **Chosen Identifier:**
        # """
        self.prompt_template = """
        You are an expert clinical terminologist. Your task is to select the single most accurate ICD-10 Code from the provided list of candidates that matches the medical complaint.

        Use the "Clinical Context" to understand the situation. The "Complaint Text" is the specific phrase you need to map. The "Candidate Concepts" are your options, each with an identifier and a description.

        **CRITICAL RULES:**
        1. **You MUST validate your choice against the patient's sex.** Do not select a gender-specific code (e.g., for pregnancy, childbirth, or male/female-specific conditions) if it contradicts the provided `patient_sex`. A violation of this rule is a critical failure.
        2. **Always choose the most precise and relevant match.** If there is no perfect match, choose the best available option.
        3. **Your response MUST be ONLY the identifier string from the best matching candidate (e.g., 'J06.9' or 'I10'). Do not add any explanation, preamble, or any text other than the chosen identifier.**

        ---
        **Examples:**

        **Example 1:**
        Clinical Context: 45 y/o male with no history of heart disease.
        Complaint Text to Map: "chest pain"
        Candidate Concepts:
        - I20.9: Angina pectoris, unspecified
        - R07.9: Chest pain, unspecified
        Chosen Identifier: R07.9

        **Example 2:**
        Clinical Context: 28 y/o female, currently pregnant.
        Complaint Text to Map: "vaginal bleeding"
        Candidate Concepts:
        - N93.9: Abnormal uterine and vaginal bleeding, unspecified
        - O26.9: Pregnancy-related condition, unspecified
        - O20.9: Hemorrhage in early pregnancy, unspecified
        Chosen Identifier: O20.9

        **Example 3:**
        Clinical Context: 65 y/o male with history of diabetes.
        Complaint Text to Map: "blurry vision"
        Candidate Concepts:
        - H53.8: Other visual disturbances
        - E11.39: Type 2 diabetes mellitus with other diabetic ophthalmic complication
        Chosen Identifier: H53.8

        **Example 4:**
        Clinical Context: 32 y/o female, not pregnant.
        Complaint Text to Map: "dysuria"
        Candidate Concepts:
        - N39.0: Urinary tract infection, site not specified
        - R30.0: Dysuria
        Chosen Identifier: N39.0

        ---

        **Clinical Context:**
        {context}

        **Complaint Text to Map:**
        "{normalized_text}"

        **Candidate Concepts:**
        {candidate_list}
        ---

        **Chosen Identifier:**
        """

    def _format_candidates(self, candidates: list[dict]) -> str:
        """Helper function to format the candidate list for the prompt."""
        formatted_string = ""
        for i, cand in enumerate(candidates):
            # We use the key 'CUI' as that's what the generator class provides.
            formatted_string += f"{i+1}. Identifier: {cand['CUI']}, Description: \"{cand['Description']}\"\n"
        return formatted_string.strip()

    def select_best_concept(self, context: str, normalized_text: str, candidates: list[dict]) -> str:
        """
        Selects the best concept identifier from a list of candidates using the LLM.

        Returns:
            The identifier string of the best concept, or an empty string if an error occurs.
        """
        if not candidates:
            return ""

        candidate_list_str = self._format_candidates(candidates)
        
        prompt = self.prompt_template.format(
            context=context,
            normalized_text=normalized_text,
            candidate_list=candidate_list_str
        )
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # This is a robust way to parse: check if the LLM's response is one of the valid options.
            valid_identifiers = {str(cand['CUI']) for cand in candidates}
            
            if response_text in valid_identifiers:
                return response_text
            
            for identifier in valid_identifiers:
                if identifier in response_text:
                    return identifier
            
            print(f"   ⚠️ LLM Warning: Response '{response_text}' did not contain any of the valid candidate identifiers.")
            return ""
            
        except Exception as e:
            print(f"   ⚠️ LLM Error during classification: {e}")
            return ""