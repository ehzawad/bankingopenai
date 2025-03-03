# File: banking-assistant/src/services/authentication/auth_utils.py

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("banking_assistant.services.auth_utils")

def validate_account(api_client, account_number: str, mobile_number: Optional[str] = None) -> Dict[str, Any]:
    """Validate if an account exists
    
    Args:
        api_client: The API client instance to use
        account_number: The account number to validate
        mobile_number: Optional mobile number for API calls
        
    Returns:
        Dictionary with validation result
    """
    # CRITICAL FIX: Check for short account numbers and try to find full accounts if possible
    if mobile_number and len(account_number) <= 4:
        logger.warning(f"Short account number detected: {account_number}, attempting to find full account")
        try:
            # Call get_accounts_by_mobile to get list of accounts
            accounts_response = api_client.get_accounts_by_mobile(mobile_number)
            if accounts_response.get("status", {}).get("gstatus") and accounts_response.get("response", {}).get("responseData"):
                accounts = accounts_response["response"]["responseData"]
                found_match = False
                for acc in accounts:
                    full_account = acc.get("key")
                    if full_account and full_account.endswith(account_number):
                        logger.info(f"Found matching full account: {full_account} for short account: {account_number}")
                        account_number = full_account
                        found_match = True
                        break
                
                # If no account was found that matches the last 4 digits
                if not found_match:
                    logger.warning(f"No account found ending with {account_number} for mobile {mobile_number}")
                    return {
                        "valid": False,
                        "message": f"No account ending with {account_number} found for this mobile number",
                        "account_status": None
                    }
            else:
                # No accounts found for this mobile number
                return {
                    "valid": False,
                    "message": "No accounts found for this mobile number",
                    "account_status": None
                }
        except Exception as e:
            logger.error(f"Error attempting to find full account number: {e}")
    
    logger.info(f"Validating account number: {account_number}")
    
    # Call get_account_details to validate the account number using the last 4 digits confirmation.
    response = api_client.get_account_details(account_number, mobile_number)
    is_valid = response.get("status", {}).get("gstatus") and response.get("response", {}).get("responseData")
    account_status = None
    if is_valid and response["response"]["responseData"]:
        account_status = response["response"]["responseData"][0].get("accStatus")
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
        mobile_number: Optional mobile number for API calls
        
    Returns:
        Dictionary with validation result
    """
    # CRITICAL FIX: Check for short account numbers and try to find full accounts if possible
    if mobile_number and len(account_number) <= 4:
        logger.warning(f"Short account number detected: {account_number}, attempting to find full account")
        try:
            # Call get_accounts_by_mobile to get list of accounts
            accounts_response = api_client.get_accounts_by_mobile(mobile_number)
            if accounts_response.get("status", {}).get("gstatus") and accounts_response.get("response", {}).get("responseData"):
                accounts = accounts_response["response"]["responseData"]
                found_match = False
                for acc in accounts:
                    full_account = acc.get("key")
                    if full_account and full_account.endswith(account_number):
                        logger.info(f"Found matching full account: {full_account} for short account: {account_number}")
                        account_number = full_account
                        found_match = True
                        break
                
                # If no account was found that matches the last 4 digits
                if not found_match:
                    logger.warning(f"No account found ending with {account_number} for mobile {mobile_number}")
                    return {
                        "valid": False,
                        "message": f"No account ending with {account_number} found for this mobile number",
                    }
            else:
                # No accounts found for this mobile number
                return {
                    "valid": False,
                    "message": "No accounts found for this mobile number",
                }
        except Exception as e:
            logger.error(f"Error attempting to find full account number: {e}")
    
    logger.info(f"Validating PIN for account number: {account_number}")
    
    response = api_client.verify_pin(account_number, pin, mobile_number)
    is_valid = response.get("status", {}).get("gstatus") and response.get("response", {}).get("Status") == "Successfull"
    logger.info(f"PIN validation for account {account_number}: {is_valid}, PIN: {pin}")
    result = {
        "valid": is_valid,
        "message": "PIN validated" if is_valid else "Invalid PIN"
    }
    logger.info(f"Returning PIN validation result: {result}")
    return result