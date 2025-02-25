# File: banking-assistant/src/services/authentication/auth_service.py
import logging
from typing import Dict, Any, List, Optional

from ...core.interfaces.service_interface import ServiceInterface
from ...api.client import BankingAPIClient

class AuthenticationService(ServiceInterface):
    """Service for authentication operations"""
    
    def __init__(self, api_client: BankingAPIClient):
        self.api_client = api_client
        self.logger = logging.getLogger("banking_assistant.services.auth")
        self.logger.info("Authentication service initialized")
    
    @property
    def domain(self) -> str:
        return "authentication"
    
    @property
    def supported_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "validate_account",
                    "description": "Validates if an account number exists in the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "description": "The account number to validate"
                            },
                            "mobile_number": {
                                "type": "string",
                                "description": "Optional mobile number for additional validation"
                            }
                        },
                        "required": ["account_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_pin",
                    "description": "Validates if the PIN is correct for the given account number",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "description": "The account number"
                            },
                            "pin": {
                                "type": "string",
                                "description": "The PIN to validate"
                            },
                            "mobile_number": {
                                "type": "string",
                                "description": "Optional mobile number for additional validation"
                            }
                        },
                        "required": ["account_number", "pin"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an authentication tool
        
        Args:
            tool_name: The name of the tool to execute
            args: Arguments for the tool
            
        Returns:
            Result of the tool execution
            
        Raises:
            ValueError: If the tool is not supported
        """
        self.logger.debug(f"Executing authentication tool: {tool_name} with args: {args}")
        
        if tool_name == "validate_account":
            mobile_number = args.get("mobile_number")
            return self.validate_account(args["account_number"], mobile_number)
        elif tool_name == "validate_pin":
            mobile_number = args.get("mobile_number")
            return self.validate_pin(args["account_number"], args["pin"], mobile_number)
        else:
            self.logger.error(f"Unknown authentication tool: {tool_name}")
            raise ValueError(f"Unknown authentication tool: {tool_name}")
    
    def validate_account(self, account_number: str, mobile_number: Optional[str] = None) -> Dict[str, Any]:
        """Validate if an account exists
        
        Args:
            account_number: The account number to validate
            mobile_number: Optional mobile number for additional validation
            
        Returns:
            Dictionary with validation result
        """
        # Get account details to check if it exists
        response = self.api_client.get_account_details(account_number, mobile_number)
        is_valid = response["status"]["gstatus"] and response["response"]["responseData"]
        
        account_status = None
        if is_valid and response["response"]["responseData"]:
            account_status = response["response"]["responseData"][0]["accStatus"]
            
        self.logger.info(f"Account validation for {account_number}: {is_valid}")
        
        return {
            "valid": is_valid,
            "message": "Account found" if is_valid else "Account not found",
            "account_status": account_status
        }
    
    def validate_pin(self, account_number: str, pin: str, mobile_number: Optional[str] = None) -> Dict[str, Any]:
        """Validate account PIN
        
        Args:
            account_number: The account number
            pin: The PIN to validate
            mobile_number: Optional mobile number for additional validation
            
        Returns:
            Dictionary with validation result
        """
        response = self.api_client.verify_pin(account_number, pin, mobile_number)
        is_valid = response["status"]["gstatus"] and response["response"]["Status"] == "Successfull"
        
        self.logger.info(f"PIN validation for account {account_number}: {is_valid}")
        
        return {
            "valid": is_valid,
            "message": "PIN validated" if is_valid else "Invalid PIN"
        }