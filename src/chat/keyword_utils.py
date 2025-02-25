# File: banking-assistant/src/chat/keyword_utils.py
import re
from typing import Set, Dict, List, Tuple

class KeywordMatcher:
    """Utility class for more sophisticated keyword matching"""
    
    def __init__(self, keywords: Set[str], word_boundaries: bool = True):
        """Initialize the keyword matcher
        
        Args:
            keywords: Set of keywords to match
            word_boundaries: Whether to enforce word boundaries in matching
        """
        self.keywords = keywords
        self.word_boundaries = word_boundaries
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for each keyword"""
        self.patterns = {}
        
        for keyword in self.keywords:
            if self.word_boundaries:
                # Match only if keyword appears as a complete word
                pattern = r'\b{}\b'.format(re.escape(keyword))
            else:
                pattern = re.escape(keyword)
            
            self.patterns[keyword] = re.compile(pattern, re.IGNORECASE)
    
    def match(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains any of the keywords
        
        Args:
            text: Text to check
            
        Returns:
            Tuple containing:
              - Boolean indicating if any keywords matched
              - List of matched keywords
        """
        matched_keywords = []
        
        for keyword, pattern in self.patterns.items():
            if pattern.search(text):
                matched_keywords.append(keyword)
                
        return bool(matched_keywords), matched_keywords

def contains_restricted_keywords(text: str, restricted_keywords: Set[str]) -> bool:
    """Check if text contains any restricted keywords, using word boundary matching
    
    Args:
        text: Text to check
        restricted_keywords: Set of restricted keywords
        
    Returns:
        True if text contains any restricted keywords
    """
    matcher = KeywordMatcher(restricted_keywords, word_boundaries=True)
    matches, _ = matcher.match(text)
    return matches
