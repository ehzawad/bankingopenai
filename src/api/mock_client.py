# File: banking-assistant/src/api/mock_client.py
import json
import logging
import time
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from .client import BankingAPIClient

class MockBankingAPIClient(BankingAPIClient):
    """Mock implementation of banking API client using sample API responses"""
    
    def __init__(self, data_path: str = "data/mock_api_data.json"):
        self.logger = logging.getLogger("banking_assistant.api.mock")
        
        # Sample account data based on the provided API responses but with randomized information
        self.sample_accounts = [
            {
                "account_number": "1311002345678",
                "masked_account": "131100***5678",
                "pin": "1234",
                "mobile": "01712345678",
                "details": {
                    "accNo": "1311002345678", 
                    "currencyCode": "BDT", 
                    "accStatus": "OPERATIVE", 
                    "branchCode": "00057", 
                    "productName": "MTB REGULARSAVINGSSTAFF", 
                    "productCode": "1311", 
                    "productSubCode": "1012", 
                    "intRate": "2.0000", 
                    "accName": "AHMED RAHMAN", 
                    "mobile": "01712345678", 
                    "accOpenDate": "2023-06-12", 
                    "lastTxnDate": "2025-01-15", 
                    "currentBalance": "1250.75 ", 
                    "unclearFund": "0.00", 
                    "availableBalance": "1250.75 ", 
                    "holdAmount": "0.00", 
                    "customerCIF": "100123456", 
                    "modeOfOperation": "SINGLY", 
                    "smsMobileNo": "1712345678", 
                    "productType": "SB", 
                    "maturityDate": ""
                }
            },
            {
                "account_number": "1308001234567",
                "masked_account": "130800***4567",
                "pin": "5678",
                "mobile": "01712345678",
                "details": {
                    "accNo": "1308001234567", 
                    "currencyCode": "BDT", 
                    "accStatus": "OPERATIVE", 
                    "branchCode": "00012", 
                    "productName": "MTB REGULAR SAVINGS", 
                    "productCode": "1308", 
                    "productSubCode": "1010", 
                    "intRate": "3.5000", 
                    "accName": "AHMED RAHMAN", 
                    "mobile": "01712345678", 
                    "accOpenDate": "2023-08-23", 
                    "lastTxnDate": "2025-01-20", 
                    "currentBalance": "8540.25 ", 
                    "unclearFund": "0.00", 
                    "availableBalance": "8540.25 ", 
                    "holdAmount": "0.00", 
                    "customerCIF": "100123456", 
                    "modeOfOperation": "SINGLY", 
                    "smsMobileNo": "1712345678", 
                    "productType": "SB", 
                    "maturityDate": ""
                }
            },
            {
                "account_number": "1311003456789",
                "masked_account": "131100***6789",
                "pin": "9012",
                "mobile": "01712345678",
                "details": {
                    "accNo": "1311003456789", 
                    "currencyCode": "BDT", 
                    "accStatus": "OPERATIVE", 
                    "branchCode": "00034", 
                    "productName": "MTB REGULAR SAVINGS", 
                    "productCode": "1311", 
                    "productSubCode": "1010", 
                    "intRate": "3.5000", 
                    "accName": "AHMED RAHMAN", 
                    "mobile": "01712345678", 
                    "accOpenDate": "2024-01-05", 
                    "lastTxnDate": "2025-02-01", 
                    "currentBalance": "25480.50 ", 
                    "unclearFund": "0.00", 
                    "availableBalance": "25480.50 ", 
                    "holdAmount": "0.00", 
                    "customerCIF": "100123456", 
                    "modeOfOperation": "SINGLY", 
                    "smsMobileNo": "1712345678", 
                    "productType": "SB", 
                    "maturityDate": ""
                }
            }
        ]
        
        # Create a lookup from mobile to accounts
        self.mobile_to_accounts = {}
        for account in self.sample_accounts:
            mobile = account["mobile"]
            if mobile not in self.mobile_to_accounts:
                self.mobile_to_accounts[mobile] = []
            self.mobile_to_accounts[mobile].append(account)
            
        # Create account number lookup
        self.account_lookup = {account["account_number"]: account for account in self.sample_accounts}
        
        self.logger.info(f"Initialized mock API client with {len(self.sample_accounts)} sample accounts")
    
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
        
        self.logger.info(f"Looking up accounts for mobile number: {mobile_number}")
        self.logger.critical(f"Function: data_validation")
        self.logger.critical(f"http://10.45.14.24/ccmwmtb/account/account-info-by-mobile-no?sercret=PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=&rm=I&callid={call_id}&connname=MWSEIBMN&cli={mobile_number}")
        
        # Find accounts matching this mobile number
        accounts = self.mobile_to_accounts.get(mobile_number, [])
        
        if accounts:
            response_data = []
            for account in accounts:
                response_data.append({
                    "key": account["account_number"],
                    "value": account["masked_account"]
                })
                
            response = {
                "status": {
                    "gmsg": "OK", 
                    "gstatus": True, 
                    "gcode": 200, 
                    "gmcode": "2000", 
                    "gmmsg": "Service extensive info by mobile number able to read successfully"
                },
                "response": {
                    "gdata": [], 
                    "logId": random.randint(400000000, 499999999), 
                    "noOfRows": 1, 
                    "resCode": "000", 
                    "resMsg": "Request Successful", 
                    "responseData": response_data
                }
            }
            
            # Log response in the format from the example
            combined_response = [{**response["status"], **response["response"]}]
            self.logger.critical(combined_response)
            
            # Log account numbers for debugging
            for account in accounts:
                acc_num = account["account_number"]
                last_4_digits = acc_num[-4:]
                self.logger.info(f"input account number last 4 digit : {last_4_digits} and match account {acc_num}")
                
            return response
            
        else:
            # Return empty response
            empty_response = {
                "status": {
                    "gmsg": "ERROR", 
                    "gstatus": False, 
                    "gcode": 404, 
                    "gmcode": "2001", 
                    "gmmsg": "No accounts found for this mobile number"
                },
                "response": {
                    "gdata": [], 
                    "logId": random.randint(400000000, 499999999), 
                    "noOfRows": 0, 
                    "resCode": "404", 
                    "resMsg": "No accounts found", 
                    "responseData": []
                }
            }
            
            # Log empty response
            combined_response = [{**empty_response["status"], **empty_response["response"]}]
            self.logger.critical(combined_response)
            
            return empty_response
    
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
        
        # Log process message
        self.logger.info(f"process : validate_pin_number, sender_id : {call_id}_+8809611888444_{mobile_number}, information : " + 
                       f"{{'input_text': '{pin}', 'last_intent': 'inform', 'intent_confidence': {random.random()}, " +
                       f"'account_number': 1, 'process_interruption': None}}")
        
        self.logger.critical(f"Function: account_pin_validation_api")
        self.logger.info(f"account_pin_validation_api")
        self.logger.critical(f"Function: data_validation")
        self.logger.critical(f"http://10.45.14.24/ccmwmtb/card/verify-tpin?sercret=PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=&rm=I&callid={call_id}&connname=MWVRFTPN&cli={mobile_number}&ccn={account_number}&crp={pin}")
        
        # Check if account exists
        account = self.account_lookup.get(account_number)
        
        if account and account["pin"] == pin:
            # Valid PIN
            response = {
                "status": {
                    "gmsg": "OK", 
                    "gstatus": True, 
                    "gcode": 200, 
                    "gmcode": 3035, 
                    "gmmsg": "Verify Tpin unable to read"
                },
                "response": {
                    "gdata": [], 
                    "Status": "Successfull", 
                    "Reason": "NA"
                }
            }
            
            # Log response in exact format from example
            combined_response = [{**response["status"], **response["response"]}]
            self.logger.critical(combined_response)
            self.logger.info(f"{{pin_number}} validation successful")
            
            return response
        else:
            # Invalid PIN
            response = {
                "status": {
                    "gmsg": "ERROR", 
                    "gstatus": False, 
                    "gcode": 400, 
                    "gmcode": 3036, 
                    "gmmsg": "Invalid PIN"
                },
                "response": {
                    "gdata": [], 
                    "Status": "Failed", 
                    "Reason": "Invalid PIN"
                }
            }
            
            # Log response in exact format from example
            combined_response = [{**response["status"], **response["response"]}]
            self.logger.critical(combined_response)
            
            return response
    
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
        
        # Get account PIN (for log message only)
        account = self.account_lookup.get(account_number)
        pin = account["pin"] if account else "unknown"
        
        self.logger.info(f"process:action_account_balance_Response, sender_id : {call_id}_+8809611888444_{mobile_number}, account_number: {account_number}, pin number {pin}, required service : currentBalance")
        self.logger.critical(f"Function: account_service_api")
        self.logger.info(f"account_service_api")
        self.logger.critical(f"Function: data_validation")
        self.logger.critical(f"http://10.45.14.24/ccmwmtb/account/common-api-function?sercret=PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=&rm=I&callid={call_id}&connname=MWSADART&cli={mobile_number}&acc={account_number}&channelId=102&refNo={ref_no}")
        
        if account:
            # Return account details
            response = {
                "status": {
                    "gmsg": "OK", 
                    "gstatus": True, 
                    "gcode": 200, 
                    "gmcode": "2065", 
                    "gmmsg": "Account Statement From DB able to read successfully"
                },
                "response": {
                    "gdata": [], 
                    "resCode": "000", 
                    "resMsg": "Successful.", 
                    "logId": random.randint(400000000, 499999999), 
                    "serviceId": ref_no, 
                    "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "msg": None, 
                    "responseData": [account["details"]]
                }
            }
            
            # Log response in exact format from example
            combined_response = [{**response["status"], **response["response"]}]
            self.logger.critical(combined_response)
            
            return response
        else:
            # Account not found
            response = {
                "status": {
                    "gmsg": "ERROR", 
                    "gstatus": False, 
                    "gcode": 404, 
                    "gmcode": "2066", 
                    "gmmsg": "Account not found"
                },
                "response": {
                    "gdata": [], 
                    "resCode": "404", 
                    "resMsg": "Account not found.", 
                    "logId": random.randint(400000000, 499999999), 
                    "serviceId": ref_no, 
                    "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "msg": "Account not found", 
                    "responseData": []
                }
            }
            
            # Log response
            combined_response = [{**response["status"], **response["response"]}]
            self.logger.critical(combined_response)
            
            return response
    
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