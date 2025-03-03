#!/usr/bin/env python
# File: banking-assistant/src/api/mock_client.py
import json
import logging
import time
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from .client import BankingAPIClient
from .api_utils import (
    normalize_mobile_number, 
    log_api_call, 
    log_api_response, 
    generate_call_id,
    generate_ref_no
)

class MockBankingAPIClient(BankingAPIClient):
    """Mock implementation of banking API client using sample API responses"""
    
    def __init__(self, data_path: str = "data/mock_api_data.json"):
        self.logger = logging.getLogger("banking_assistant.api.mock")
        now = datetime.now()
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
                    "lastTxnDate": (now - timedelta(days=15)).strftime("%Y-%m-%d"),
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
                    "lastTxnDate": (now - timedelta(days=10)).strftime("%Y-%m-%d"),
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
                    "accOpenDate": "2023-01-05", 
                    "lastTxnDate": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
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
        self.mobile_to_accounts = {}
        for account in self.sample_accounts:
            mobile = account["mobile"]
            if mobile not in self.mobile_to_accounts:
                self.mobile_to_accounts[mobile] = []
            self.mobile_to_accounts[mobile].append(account)
        self.account_lookup = {account["account_number"]: account for account in self.sample_accounts}
        self.logger.info(f"Initialized mock API client with {len(self.sample_accounts)} sample accounts")
    
    def get_accounts_by_mobile(self, mobile_number: str, call_id: Optional[str] = None) -> Dict[str, Any]:
        mobile_number = normalize_mobile_number(mobile_number)
        call_id = call_id or generate_call_id()
        self.logger.info(f"Looking up accounts for mobile number: {mobile_number}")
        url = "http://10.45.14.24/ccmwmtb/account/account-info-by-mobile-no"
        params = {
            "secret": "PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=",
            "rm": "I",
            "callid": call_id,
            "connname": "MWSEIBMN",
            "cli": mobile_number
        }
        log_api_call("data_validation", url, params)
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
            log_api_response(response)
            for account in accounts:
                acc_num = account["account_number"]
                last_4_digits = acc_num[-4:]
                self.logger.info(f"input account number last 4 digit : {last_4_digits} and match account {acc_num}")
            return response
        else:
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
            log_api_response(empty_response)
            return empty_response
    
    def verify_pin(self, account_number: str, pin: str, mobile_number: Optional[str] = None, call_id: Optional[str] = None) -> Dict[str, Any]:
        call_id = call_id or generate_call_id()
        mobile_number = mobile_number or "unknown"
        self.logger.info(f"process : validate_pin_number, sender_id : {call_id}_+8809611888444_{mobile_number}, information : " + 
                           f"{{'input_text': '****', 'last_intent': 'inform', 'intent_confidence': {random.random()}, " +
                           f"'account_number': 1, 'process_interruption': None}}")
        url = "http://10.45.14.24/ccmwmtb/card/verify-tpin"
        params = {
            "secret": "PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=",
            "rm": "I",
            "callid": call_id,
            "connname": "MWVRFTPN",
            "cli": mobile_number,
            "ccn": account_number,
            "crp": pin
        }
        self.logger.critical("Function: account_pin_validation_api")
        self.logger.info("account_pin_validation_api")
        secure_params = params.copy()
        secure_params["crp"] = "****"
        log_api_call("data_validation", url, secure_params)
        
        # CRITICAL FIX: Handle short account numbers before PIN verification
        original_account_number = account_number
        if len(account_number) <= 4 and mobile_number:
            self.logger.warning(f"Short account number detected in verify_pin: {account_number}")
            matching_account = None
            
            # Try to find matching account by last digits
            for acc in self.sample_accounts:
                if acc["account_number"].endswith(account_number) and acc["mobile"] == mobile_number:
                    matching_account = acc
                    self.logger.info(f"Found matching account: {acc['account_number']} for digits: {account_number}")
                    break
            
            if matching_account:
                account_number = matching_account["account_number"]
                self.logger.info(f"Using full account number: {account_number} instead of short digits: {original_account_number}")
            else:
                self.logger.warning(f"No matching account found for {original_account_number}")
                response = {
                    "status": {
                        "gmsg": "ERROR", 
                        "gstatus": False, 
                        "gcode": 404, 
                        "gmcode": 3036, 
                        "gmmsg": "Invalid Account"
                    },
                    "response": {
                        "gdata": [], 
                        "Status": "Failed", 
                        "Reason": f"No account ending with {original_account_number} found for this mobile number"
                    }
                }
                log_api_response(response)
                return response
        
        account = self.account_lookup.get(account_number)
        if account and account["pin"] == pin:
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
            log_api_response(response)
            self.logger.info("PIN validation successful")
            return response
        else:
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
            log_api_response(response)
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
        call_id = call_id or generate_call_id()
        mobile_number = mobile_number or "unknown"
        ref_no = generate_ref_no()
        self.logger.info(f"process:action_account_balance_Response, sender_id : {call_id}_+8809611888444_{mobile_number}, account_number: {account_number}, required service : currentBalance")
        self.logger.critical("Function: account_service_api")
        self.logger.info("account_service_api")
        url = "http://10.45.14.24/ccmwmtb/account/common-api-function"
        params = {
            "secret": "PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=",
            "rm": "I",
            "callid": call_id,
            "connname": "MWSADART",
            "cli": mobile_number,
            "acc": account_number,
            "channelId": "102",
            "refNo": ref_no
        }
        log_api_call("data_validation", url, params)
        
        # CRITICAL FIX: Handle short account numbers by trying to match with the last digits
        if len(account_number) <= 4 and mobile_number:
            self.logger.warning(f"Short account number detected in get_account_details: {account_number}")
            matching_account = None
            
            # Try to find matching account by last digits
            for acc in self.sample_accounts:
                if acc["account_number"].endswith(account_number) and acc["mobile"] == mobile_number:
                    matching_account = acc
                    self.logger.info(f"Found matching account: {acc['account_number']} for digits: {account_number}")
                    break
            
            if matching_account:
                account_number = matching_account["account_number"]
                self.logger.info(f"Using full account number: {account_number} instead of short digits")
        
        if account_number in self.account_lookup:
            account = self.account_lookup[account_number]
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
            log_api_response(response)
            return response
        else:
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
            log_api_response(response)
            return response