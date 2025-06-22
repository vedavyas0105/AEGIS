import json
from spacy.tokens import Token
from spacy.language import Language

@Language.factory("abbreviation_expander") 
def create_abbreviation_expander(nlp: Language, name: str, dictionary_path: str):
    """
    This factory function is registered with spaCy. When you call nlp.add_pipe(),
    spaCy finds this function and uses it to create an instance of your component.
    """
    return AbbreviationExpander(nlp, dictionary_path)


class AbbreviationExpander:
    """
    A custom spaCy pipeline component to expand abbreviations
    based on a provided dictionary.
    """
    # The __init__ method now only needs the arguments for the component itself.
    # The 'nlp' and 'name' arguments are handled by the factory function.
    def __init__(self, nlp, dictionary_path: str):
        with open(dictionary_path, "r", encoding="utf-8") as f:
            self.abbreviations = json.load(f)

        # Register custom attributes on the Token class if they don't already exist.
        if not Token.has_extension("is_abbreviation"):
            Token.set_extension("is_abbreviation", default=False)
        if not Token.has_extension("expansion"):
            Token.set_extension("expansion", default=None)

    def __call__(self, doc):
        """
        This method is executed when a text is processed by the pipeline.
        """
        for token in doc:
            # Match in a case-insensitive way by checking the lowercase form.
            expansion = self.abbreviations.get(token.text.lower())
            
            if expansion:
                # If a match is found, set the custom attributes.
                token._.is_abbreviation = True
                token._.expansion = expansion
        return doc