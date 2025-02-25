# File: banking-assistant/src/api/real_client.py
import logging
import requests
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime

from .client import BankingAPIClient
from .api_utils import (
    normalize_mobile_number, 
    log_api_call, 
    log_api_response, 
    generate_call_id,
    generate_ref_no,
    create_error_response
)

class RealBankingAPIClient(BankingAPIClient):
    """Implementation of banking API client using real HTTP requests"""
    
    def __init__(self, 
                 base_url: str = "http://10.45.14.24/ccmwmtb",
                 api_secret: str = "PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=",
                 timeout: int = 30):
        self.base_url = base_url
        self.api_secret = api_secret
        self.timeout = timeout
        self.logger = logging.getLogger("banking_assistant.api.real")
        self.logger.info(f"Initialized real API client with base URL: {base_url}")
    
    def get_accounts_by_mobile(self, mobile_number: str, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Get accounts associated with a mobile number
        
        Args:
            mobile_number: The mobile number to look up
            call_id: Optional call ID for tracking
            
        Returns:
            API response containing account numbers
        """
        mobile_number = normalize_mobile_number(mobile_number)
        call_id = call_id or generate_call_id()
        
        # Build URL for account lookup - Fixed typo in parameter name (sercret -> secret)
        url = f"{self.base_url}/account/account-info-by-mobile-no"
        params = {
            "secret": self.api_secret,
            "rm": "I",
            "callid": call_id,
            "connname": "MWSEIBMN",
            "cli": mobile_number
        }
        
        self.logger.info(f"Looking up accounts for mobile number: {mobile_number}")
        
        # Log API call
        log_api_call("data_validation", url, params)
        
        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=self.timeout)
            response_json = response.json()
            
            # Log the response
            log_api_response(response_json)
            
            # Log account numbers if successful
            if response_json.get("status", {}).get("gstatus") and "responseData" in response_json.get("response", {}):
                for account in response_json["response"]["responseData"]:
                    acc_num = account.get("key", "")
                    if acc_num:
                        last_4_digits = acc_num[-4:]
                        self.logger.info(f"input account number last 4 digit : {last_4_digits} and match account {acc_num}")
            
            return response_json
            
        except Exception as e:
            self.logger.error(f"Error calling accounts by mobile API: {str(e)}")
            return create_error_response(f"API error: {str(e)}")
    
    def verify_pin(self, account_number: str, pin: str, mobile_number: Optional[str] = None, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify PIN for an account
        
        Args:
            account_number: The account number
            pin: The PIN to verify
            mobile_number: Optional mobile number for the customer
            call_id: Optional call ID for tracking
            
        Returns:
            API response with verification result
        """
        call_id = call_id or generate_call_id()
        mobile_number = mobile_number or "unknown"
        
        # Log process message with minimal sensitive info
        self.logger.info(f"process : validate_pin_number, sender_id : {call_id}_+8809611888444_{mobile_number}, information : " + 
                       f"{{'input_text': '****', 'last_intent': 'inform', 'intent_confidence': {random.random()}, " +
                       f"'account_number': 1, 'process_interruption': None}}")
        
        # Build URL for PIN verification - Fixed typo in parameter name (sercret -> secret)
        url = f"{self.base_url}/card/verify-tpin"
        params = {
            "secret": self.api_secret,
            "rm": "I",
            "callid": call_id,
            "connname": "MWVRFTPN",
            "cli": mobile_number,
            "ccn": account_number,
            "crp": pin
        }
        
        self.logger.critical(f"Function: account_pin_validation_api")
        self.logger.info(f"account_pin_validation_api")
        
        # Don't log PIN in parameters
        secure_params = params.copy()
        secure_params["crp"] = "****"
        log_api_call("data_validation", url, secure_params)
        
        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=self.timeout)
            response_json = response.json()
            
            # Log the response
            log_api_response(response_json)
            
            # Log success/failure message
            if response_json.get("status", {}).get("gstatus"):
                self.logger.info(f"PIN validation successful")
            else:
                self.logger.info("PIN validation failed")
            
            return response_json
            
        except Exception as e:
            self.logger.error(f"Error calling PIN verification API: {str(e)}")
            
            # Return error response with specific structure for PIN verification
            error_response = create_error_response(
                f"API error: {str(e)}", 
                additional_info={
                    "Status": "Failed", 
                    "Reason": f"API error: {str(e)}"
                }
            )
            
            return error_response
    
    def get_account_details(self, account_number: str, mobile_number: Optional[str] = None, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed account information
        
        Args:
            account_number: The account number
            mobile_number: Optional mobile number for the customer
            call_id: Optional call ID for tracking
            
        Returns:
            API response with account details
        """
        call_id = call_id or generate_call_id()
        mobile_number = mobile_number or "unknown"
        ref_no = generate_ref_no()
        
        # Log request information (without PIN)
        self.logger.info(f"process:action_account_balance_Response, sender_id : {call_id}_+8809611888444_{mobile_number}, account_number: {account_number}, required service : currentBalance")
        
        # Build URL for account details - Fixed typo in parameter name (sercret -> secret)
        url = f"{self.base_url}/account/common-api-function"
        params = {
            "secret": self.api_secret,
            "rm": "I",
            "callid": call_id,
            "connname": "MWSADART",
            "cli": mobile_number,
            "acc": account_number,
            "channelId": "102",
            "refNo": ref_no
        }
        
        self.logger.critical(f"Function: account_service_api")
        self.logger.info(f"account_service_api")
        
        # Log API call
        log_api_call("data_validation", url, params)
        
        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=self.timeout)
            response_json = response.json()
            
            # Log the response
            log_api_response(response_json)
            
            return response_json
            
        except Exception as e:
            self.logger.error(f"Error calling account details API: {str(e)}")
            
            # Return error response with specific structure for account details
            error_response = create_error_response(
                f"API error: {str(e)}",
                additional_info={
                    "resCode": "500", 
                    "resMsg": "API error", 
                    "serviceId": ref_no, 
                    "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "msg": f"API error: {str(e)}"
                }
            )
            
            return error_response
