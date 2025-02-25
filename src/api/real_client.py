# File: banking-assistant/src/api/real_client.py
import logging
import requests
import time
import random
import re
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

from .client import BankingAPIClient

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
        mobile_number = self._normalize_mobile_number(mobile_number)
        call_id = call_id or f"{int(time.time())}{random.randint(100000000, 999999999)}"
        
        # Build URL for account lookup
        url = f"{self.base_url}/account/account-info-by-mobile-no"
        params = {
            "sercret": self.api_secret,
            "rm": "I",
            "callid": call_id,
            "connname": "MWSEIBMN",
            "cli": mobile_number
        }
        
        self.logger.info(f"Looking up accounts for mobile number: {mobile_number}")
        self.logger.critical(f"Function: data_validation")
        
        # Log the full URL
        full_url = f"{url}?{'&'.join([f'{k}={quote_plus(str(v))}' for k, v in params.items()])}"
        self.logger.critical(full_url)
        
        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=self.timeout)
            response_json = response.json()
            
            # Log the response in the expected format
            if isinstance(response_json, dict):
                # Extract status and response from the JSON
                status = response_json.get("status", {})
                resp = response_json.get("response", {})
                
                # Combine and log them
                combined_response = [{**status, **resp}]
                self.logger.critical(combined_response)
                
                # Log account numbers if successful
                if status.get("gstatus") and "responseData" in resp:
                    for account in resp["responseData"]:
                        acc_num = account.get("key", "")
                        if acc_num:
                            last_4_digits = acc_num[-4:]
                            self.logger.info(f"input account number last 4 digit : {last_4_digits} and match account {acc_num}")
            
            return response_json
            
        except Exception as e:
            self.logger.error(f"Error calling accounts by mobile API: {str(e)}")
            
            # Return error response
            error_response = {
                "status": {
                    "gmsg": "ERROR", 
                    "gstatus": False, 
                    "gcode": 500, 
                    "gmcode": "9999", 
                    "gmmsg": f"API error: {str(e)}"
                },
                "response": {
                    "gdata": [], 
                    "logId": 0, 
                    "noOfRows": 0, 
                    "resCode": "500", 
                    "resMsg": "API error", 
                    "responseData": []
                }
            }
            
            # Log error response
            combined_response = [{**error_response["status"], **error_response["response"]}]
            self.logger.critical(combined_response)
            
            return error_response
    
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
        call_id = call_id or f"{int(time.time())}{random.randint(100000000, 999999999)}"
        mobile_number = mobile_number or "unknown"
        
        # Log process information
        self.logger.info(f"process : validate_pin_number, sender_id : {call_id}_+8809611888444_{mobile_number}, information : " + 
                       f"{{'input_text': '{pin}', 'last_intent': 'inform', 'intent_confidence': {random.random()}, " +
                       f"'account_number': 1, 'process_interruption': None}}")
        
        # Build URL for PIN verification
        url = f"{self.base_url}/card/verify-tpin"
        params = {
            "sercret": self.api_secret,
            "rm": "I",
            "callid": call_id,
            "connname": "MWVRFTPN",
            "cli": mobile_number,
            "ccn": account_number,
            "crp": pin
        }
        
        self.logger.critical(f"Function: account_pin_validation_api")
        self.logger.info(f"account_pin_validation_api")
        self.logger.critical(f"Function: data_validation")
        
        # Log the full URL
        full_url = f"{url}?{'&'.join([f'{k}={quote_plus(str(v))}' for k, v in params.items()])}"
        self.logger.critical(full_url)
        
        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=self.timeout)
            response_json = response.json()
            
            # Log the response in the expected format
            if isinstance(response_json, dict):
                status = response_json.get("status", {})
                resp = response_json.get("response", {})
                
                combined_response = [{**status, **resp}]
                self.logger.critical(combined_response)
                
                # Log success/failure message
                if status.get("gstatus"):
                    self.logger.info(f"{{pin_number}} validation successful")
                else:
                    self.logger.info("PIN validation failed")
            
            return response_json
            
        except Exception as e:
            self.logger.error(f"Error calling PIN verification API: {str(e)}")
            
            # Return error response
            error_response = {
                "status": {
                    "gmsg": "ERROR", 
                    "gstatus": False, 
                    "gcode": 500, 
                    "gmcode": "9999", 
                    "gmmsg": f"API error: {str(e)}"
                },
                "response": {
                    "gdata": [], 
                    "Status": "Failed", 
                    "Reason": f"API error: {str(e)}"
                }
            }
            
            # Log error response
            combined_response = [{**error_response["status"], **error_response["response"]}]
            self.logger.critical(combined_response)
            
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
        call_id = call_id or f"{int(time.time())}{random.randint(100000000, 999999999)}"
        mobile_number = mobile_number or "unknown"
        ref_no = f"{datetime.now().strftime('%Y%m%d%H%M%S')}AHw{random.randint(10, 99)}"
        
        # Log request information
        pin_part = account_number[-4:] if account_number else "unknown"
        self.logger.info(f"process:action_account_balance_Response, sender_id : {call_id}_+8809611888444_{mobile_number}, account_number: {account_number}, pin number {pin_part}, required service : currentBalance")
        
        # Build URL for account details
        url = f"{self.base_url}/account/common-api-function"
        params = {
            "sercret": self.api_secret,
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
        self.logger.critical(f"Function: data_validation")
        
        # Log the full URL
        full_url = f"{url}?{'&'.join([f'{k}={quote_plus(str(v))}' for k, v in params.items()])}"
        self.logger.critical(full_url)
        
        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=self.timeout)
            response_json = response.json()
            
            # Log the response
            if isinstance(response_json, dict):
                status = response_json.get("status", {})
                resp = response_json.get("response", {})
                
                combined_response = [{**status, **resp}]
                self.logger.critical(combined_response)
            
            return response_json
            
        except Exception as e:
            self.logger.error(f"Error calling account details API: {str(e)}")
            
            # Return error response
            error_response = {
                "status": {
                    "gmsg": "ERROR", 
                    "gstatus": False, 
                    "gcode": 500, 
                    "gmcode": "9999", 
                    "gmmsg": f"API error: {str(e)}"
                },
                "response": {
                    "gdata": [], 
                    "resCode": "500", 
                    "resMsg": "API error", 
                    "logId": 0, 
                    "serviceId": ref_no, 
                    "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "msg": f"API error: {str(e)}", 
                    "responseData": []
                }
            }
            
            # Log error response
            combined_response = [{**error_response["status"], **error_response["response"]}]
            self.logger.critical(combined_response)
            
            return error_response
    
    def _normalize_mobile_number(self, mobile_number: str) -> str:
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
