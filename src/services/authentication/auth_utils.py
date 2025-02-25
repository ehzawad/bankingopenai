# File: banking-assistant/src/services/authentication/auth_utils.py
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("banking_assistant.services.auth_utils")

def validate_account(api_client, account_number: str, mobile_number: Optional[str] = None) -> Dict[str, Any]:
    """Validate if an account exists
    
    Args:
        api_client: The API client instance to use
        account_number: The account number to validate
        mobile_number: Optional mobile number for additional validation
        
    Returns:
        Dictionary with validation result
    """
    # Get account details to validate
    response = api_client.get_account_details(account_number, mobile_number)
    is_valid = response["status"]["gstatus"] and response["response"]["responseData"]
    
    account_status = None
    if is_valid and response["response"]["responseData"]:
        account_status = response["response"]["responseData"][0]["accStatus"]
        
    logger.info(f"Account validation for {account_number}: {is_valid}")
    
    return {
        "valid": is_valid,
        "message": "Account found" if is_valid else "Account not found",
        "account_status": account_status
    }

def validate_pin(api_client, account_number: str, pin: str, mobile_number: Optional[str] = None) -> Dict[str, Any]:
    """Validate account PIN
    
    Args:
        api_client: The API client instance to use
        account_number: The account number
        pin: The PIN to validate
        mobile_number: Optional mobile number for additional validation
        
    Returns:
        Dictionary with validation result
    """
    response = api_client.verify_pin(account_number, pin, mobile_number)
    is_valid = response["status"]["gstatus"] and response["response"]["Status"] == "Successfull"
    
    logger.info(f"PIN validation for account {account_number}: {is_valid}")
    
    return {
        "valid": is_valid,
        "message": "PIN validated" if is_valid else "Invalid PIN"
    }
