# llm_expander.py
import json
import re

class LLMContextualExpander:
    """
    A class that uses a Large Language Model to perform contextual abbreviation
    expansion on a BATCH of texts in a single API call.
    """
    def __init__(self, model):
        self.model = model
        # The prompt is now engineered to handle a list of inputs and request a JSON output.
        # self.prompt_template = """
        # You are an expert clinical NLP assistant. Your task is to rewrite EACH medical text
        # in the following numbered list by expanding ALL clinical abbreviations.

        # Return your response as a single, raw JSON array of strings. Each string in the array
        # should be the fully expanded text. The order and number of items in your JSON response
        # MUST match the input list exactly.

        # Example Input:
        # 1. "pt c/o sob"
        # 2. "hx of GERD"

        # Example JSON Array Response:
        # ["patient complains of shortness of breath", "history of Gastroesophageal Reflux Disease"]

        # ---
        # Texts to Expand:
        # {text_list}
        # ---

        # JSON Array Response:
        # """

        self.prompt_template = """
        You are an expert clinical NLP assistant. Your task is to rewrite EACH medical text in the following numbered list by expanding ALL clinical abbreviations.

        **Rules:**
        1. **Expand every abbreviation in context.** Do not leave any abbreviations unexpanded.
        2. **Preserve the original meaning and context** of each input string.
        3. **Return your response as a single, raw JSON array of strings.**
        4. **Each string in the array should be the fully expanded text.**
        5. **The order and number of items in your JSON response MUST match the input list exactly.**
        6. **Do not add any explanations, notes, or extra formatting outside the JSON array.**

        **Examples:**

        **Input:**
        1. "pt c/o sob"
        2. "hx of GERD"
        3. "pt w/ HTN and DM2"
        4. "ECG shows ST elevation"
        5. "pt w/ hx of CABG"

        **Output:**
        ["patient complains of shortness of breath", "history of Gastroesophageal Reflux Disease", "patient with hypertension and type 2 diabetes mellitus", "electrocardiogram shows ST elevation", "patient with history of coronary artery bypass graft"]

        **Input:**
        {text_list}

        **Output:**
        """

    def expand_batch(self, texts: list[str]) -> list[str]:
        """
        Sends a batch of texts to the LLM for expansion.

        Args:
            texts: A list of strings to be expanded.

        Returns:
            A list of fully expanded strings, in the same order as the input.
        """
        if not texts:
            return []

        # Format the list of texts as a numbered list for the prompt.
        formatted_list = "\n".join([f"{i+1}. \"{text}\"" for i, text in enumerate(texts)])
        prompt = self.prompt_template.format(text_list=formatted_list)

        try:
            response = self.model.generate_content(prompt)
            # The LLM's response should be a string containing a JSON array.
            # We need to find the JSON block and parse it.
            json_str = response.text.strip()
            
            # A simple regex to find content between '[' and ']'
            match = re.search(r'\[.*\]', json_str, re.DOTALL)
            if not match:
                print("   ⚠️ LLM Warning: Did not return a valid JSON array. Returning original texts.")
                return texts

            parsed_json = json.loads(match.group(0))

            # Sanity check: ensure the LLM returned the correct number of items.
            if len(parsed_json) != len(texts):
                print(f"   ⚠️ LLM Warning: Mismatch in item count (expected {len(texts)}, got {len(parsed_json)}). Returning original texts.")
                return texts

            return parsed_json

        except Exception as e:
            print(f"   ⚠️ LLM Error: Could not process batch. Returning original texts. Details: {e}")
            return texts # Return the original batch if any error occurs.