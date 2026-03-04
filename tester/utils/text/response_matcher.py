# import re
import difflib
from typing import List, Protocol

import utils.log_manager as log_manager

logger = log_manager.get_logger(__name__)


class ResponseMatcher(Protocol):
    """
    Protocol for response matchers.
    """
    def match(self, response: str, expected_keywords: List[str]) -> bool:
        raise NotImplementedError("Subclasses must implement this method")

class FuzzyMatcher:
    """
    Fuzzy response matcher implementation.
    """
    def __init__(self, fuzzy_threshold: float = 0.6):
        # 0.6 means 60% of the characters need to match (good for typos)
        self.fuzzy_threshold = fuzzy_threshold

    def match(self, response: str, expected_keywords: List[str]) -> bool:
        response_lower = response.lower()
        
        for keyword in expected_keywords:
            kw_lower = keyword.lower()
            
            # We check if the keyword is 'fuzzily' inside the response
            # by comparing the keyword to words in the response
            response_words = response_lower.split()
            for word in response_words:
                similarity = difflib.SequenceMatcher(None, kw_lower, word).ratio()
                if similarity >= self.fuzzy_threshold:
                    logger.debug(f"Fuzzy match found: '{kw_lower}' matched with '{word}' (score: {similarity:.2f})")
                    return True
                    
        return False
    

class DynamicResponseMatcher:
    def __init__(self, fuzzy_threshold: float = 0.5):
        self._semantic_threshold = fuzzy_threshold
        self._fuzzy_matcher = FuzzyMatcher(fuzzy_threshold=fuzzy_threshold)

    def match(self, response: str, expected_keywords: List[str]) -> bool:
        # 1- direct keyword match
        if self._keyword_match(response, expected_keywords):
            logger.debug("Keyword match successful.")
            return True

        # 2- fallback: semantic similarity match
        logger.debug("Keyword match failed. Falling back to fuzzy match check...")
        return self._fuzzy_matcher.match(response, expected_keywords)

    def _keyword_match(self, response: str, keywords: List[str]) -> bool:
        response_lower = response.lower()
        return any(k.lower() in response_lower for k in keywords)
