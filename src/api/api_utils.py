# File: banking-assistant/src/api/api_utils.py
import logging
import re
import random
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
from datetime import datetime

logger = logging.getLogger("banking_assistant.api.utils")

def normalize_mobile_number(mobile_number: str) -> str:
    """Normalize mobile number for consistent lookup
    
    Args:
        mobile_number: Mobile number to normalize
        
    Returns:
        Normalized mobile number
    """
    # Handle numeric digits
    mobile_number = re.sub(r'\D', '', mobile_number)
    
    # Handle Bangladesh country code
    if mobile_number.startswith("880"):
        mobile_number = mobile_number[3:]
    
    # Add leading 0 if needed
    if not mobile_number.startswith("0") and len(mobile_number) == 10:
        mobile_number = "0" + mobile_number
        
    return mobile_number

def log_api_call(function_name: str, url: str, params: Dict[str, str]) -> None:
    """Log API call in a consistent format
    
    Args:
        function_name: Name of the function being called
        url: Base URL for the API call
        params: Parameters for the API call
    """
    logger.critical(f"Function: {function_name}")
    
    # Build full URL for logging
    full_url = f"{url}?{'&'.join([f'{k}={quote_plus(str(v))}' for k, v in params.items()])}"
    logger.critical(full_url)

def log_api_response(response: Dict[str, Any]) -> None:
    """Log API response in a consistent format
    
    Args:
        response: API response to log
    """
    if isinstance(response, dict):
        # Extract status and response from the JSON
        status = response.get("status", {})
        resp = response.get("response", {})
        
        # Combine and log them
        combined_response = [{**status, **resp}]
        logger.critical(combined_response)

def generate_call_id() -> str:
    """Generate a call ID for API calls
    
    Returns:
        Generated call ID
    """
    return f"{int(datetime.now().timestamp())}{random.randint(100000000, 999999999)}"

def generate_ref_no() -> str:
    """Generate a reference number for API calls
    
    Returns:
        Generated reference number
    """
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}AHw{random.randint(10, 99)}"

def create_error_response(error_message: str, code: int = 500, additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized error response
    
    Args:
        error_message: Error message to include
        code: Error code
        additional_info: Additional information to include in the response
        
    Returns:
        Formatted error response
    """
    response = {
        "status": {
            "gmsg": "ERROR", 
            "gstatus": False, 
            "gcode": code, 
            "gmcode": "9999", 
            "gmmsg": error_message
        },
        "response": {
            "gdata": [], 
            "logId": random.randint(400000000, 499999999), 
            "resCode": str(code), 
            "resMsg": "API error", 
            "responseData": []
        }
    }
    
    # Add additional info if provided
    if additional_info:
        response["response"].update(additional_info)
    
    # Log error response
    log_api_response(response)
    
    return response
