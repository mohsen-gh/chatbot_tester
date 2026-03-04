import re
from typing import Iterable, Protocol


class IntentMatcher(Protocol):
    """
    Protocol for intent matchers.
    """
    def match(self, intent: str | None, expected_intents: Iterable[str] | None) -> bool:
        raise NotImplementedError("Subclasses must implement this method")

class ExactIntentMatcher:
    """
    Intent matcher implementation.
    """
    @staticmethod
    def _normalize(s: str | None) -> str:
        """
        Normalize an intent string by standardizing its format.
        
        Converts the input string to lowercase, removes extra whitespace,
        replaces hyphens and spaces with underscores, and collapses
        consecutive underscores into a single underscore.
        
        Args:
            s (str | None): The intent string to normalize. Can be None.
        
        Returns:
            str: The normalized intent string with lowercase letters,
                 underscores as separators, and no consecutive underscores.
        
        Example:
            >>> IntentMatchValidator.norm_intent("User-Intent Name")
            'user_intent_name'
            >>> IntentMatchValidator.norm_intent("  multiple___spaces  ")
            'multiple_spaces'
            >>> IntentMatchValidator.norm_intent(None)
            ''
        """
        # Convert None to empty string, strip whitespace, convert to lowercase
        s = (s or "").strip().lower().replace("-", "_").replace(" ", "_")
        # Replace multiple consecutive underscores with a single underscore
        s = re.sub(r"_+", "_", s)
        return s

    @classmethod
    def match(cls, intent: str | None, expected_intents: Iterable[str] | None) -> bool:
        """
        Validate if a given intent matches any of the expected intents.
        Normalizes both the input intent and expected intents before comparison
        to ensure case-insensitive and standardized matching.
        Args:
            cls: The class reference.
            intent (str | None): The intent string to validate.
            expected_intents (Iterable[str] | None): An iterable of expected intent strings to match against.
        Returns:
            bool: True if the normalized intent matches any of the normalized expected intents,
                  False if expected_intents is empty or if no match is found.
        Examples:
            >>> validate("HELLO", ["hello", "hi"])
            True
            >>> validate("bye", ["hello", "hi"])
            False
            >>> validate("hello", None)
            False
        """

        if not expected_intents:
            return False

        intent_n = cls._normalize(intent)
        expected_n = {cls._normalize(e) for e in expected_intents}
        return intent_n in expected_n
