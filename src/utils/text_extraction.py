# File: banking-assistant/src/utils/text_extraction.py
import re
import logging
from typing import Optional, List, Dict, Any, Tuple, Set

logger = logging.getLogger("banking_assistant.utils.text_extraction")

def extract_pin(message: str) -> Optional[str]:
    """Extract a 4-digit PIN from the message
    
    Args:
        message: The user message
        
    Returns:
        Extracted PIN or None
    """
    # Try explicit PIN patterns first (higher priority)
    explicit_patterns = [
        r'pin\s+is\s+(\d{4})',
        r'pin:?\s*(\d{4})',
        r'my\s+pin\s+(?:is\s+)?(\d{4})',
        r'pin.*?(\d{4})',
        r'(\d{4}).*?pin'
    ]
    
    for pattern in explicit_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            logger.debug(f"Extracted PIN via explicit pattern: {match.group(1)}")
            return match.group(1)
    
    # For simple messages with just 4 digits, it's likely a PIN when we're awaiting one
    if message.strip().isdigit() and len(message.strip()) == 4:
        pin = message.strip()
        logger.debug(f"Extracted PIN from simple 4-digit message: {pin}")
        logger.info(f"Found PIN: {pin}")
        return pin
    
    # Generic pattern for any 4 digits in the message
    # Note: This is lower priority to avoid confusion with account numbers
    pin_pattern = r'(?<!\d)(\d{4})(?!\d)'
    pin_match = re.search(pin_pattern, message)
    if pin_match:
        pin = pin_match.group(1)
        logger.debug(f"Extracted PIN: {pin}")
        return pin
        
    return None

def extract_last_4_digits(message: str) -> Optional[str]:
    """Extract last 4 digits of account number from message
    
    Args:
        message: The user message
        
    Returns:
        Last 4 digits or None if not found
    """
    # Patterns for common ways to express last 4 digits
    patterns = [
        r'\b(\d{4})\b',                     # Simple 4 digits
        r'last\s+four\s+digits?\s+(\d{4})',  # "last four digits 1234"
        r'ending\s+in\s+(\d{4})',           # "ending in 1234"
        r'ends?\s+with\s+(\d{4})',          # "ends with 1234"
        r'account\s+\w+\s+(\d{4})'          # "account XXXX 1234"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            logger.debug(f"Extracted last 4 digits: {match.group(1)} using pattern: {pattern}")
            return match.group(1)
    
    return None

def extract_pin_from_conversation(conversation: List[Dict[str, Any]]) -> Optional[str]:
    """Extract PIN from conversation history
    
    Args:
        conversation: List of conversation messages
        
    Returns:
        The PIN or None if not found
    """
    import json
    
    for msg in reversed(conversation):
        # Check user messages
        if msg["role"] == "user":
            content = msg["content"]
            pin = extract_pin(content)
            if pin:
                return pin
        
        # Check tool calls
        if msg["role"] == "assistant" and "tool_calls" in msg:
            for tool_call in msg["tool_calls"]:
                if tool_call["function"]["name"] == "validate_pin":
                    try:
                        args = json.loads(tool_call["function"]["arguments"])
                        pin = args.get("pin")
                        if pin and pin != "****":  # Skip masked pins
                            return pin
                    except json.JSONDecodeError:
                        continue
                        
    return None

def contains_restricted_keywords(text: str, restricted_keywords: Set[str]) -> bool:
    """Check if text contains any restricted keywords using word boundary matching
    
    Args:
        text: Text to check
        restricted_keywords: Set of restricted keywords
        
    Returns:
        True if text contains any restricted keywords
    """
    for keyword in restricted_keywords:
        # Match only if keyword appears as a complete word
        pattern = r'\b{}\b'.format(re.escape(keyword))
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False