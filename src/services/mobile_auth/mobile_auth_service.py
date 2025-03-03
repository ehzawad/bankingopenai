#!/usr/bin/env python
# File: banking-assistant/src/services/mobile_auth/mobile_auth_service.py
import logging
from typing import Dict, Any, List, Optional

from ...core.interfaces.service_interface import ServiceInterface
from ...api.client import BankingAPIClient
from ..common.tool_definitions import MOBILE_AUTH_TOOLS

class MobileAuthService(ServiceInterface):
    """Service for mobile-based authentication operations.
       This simplified version uses the mobile number only as a parameter for API calls.
    """
    
    def __init__(self, api_client: BankingAPIClient):
        self.api_client = api_client
        self.logger = logging.getLogger("banking_assistant.services.mobile_auth")
        self.logger.info("Mobile authentication service initialized")
    
    @property
    def domain(self) -> str:
        return "mobile_auth"
    
    @property
    def supported_tools(self) -> List[Dict[str, Any]]:
        return MOBILE_AUTH_TOOLS
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mobile auth tool
        
        Args:
            tool_name: The name of the tool to execute
            args: Arguments for the tool
            
        Returns:
            Result of the tool execution
            
        Raises:
            ValueError: If the tool name is not recognized
        """
        self.logger.debug(f"Executing mobile auth tool: {tool_name} with args: {args}")
        if tool_name == "get_accounts_by_mobile":
            return self.get_accounts_by_mobile(args["mobile_number"], args.get("call_id"))
        else:
            self.logger.error(f"Unknown tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def get_accounts_by_mobile(self, mobile_number: str, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Get accounts associated with a mobile number
        
        Args:
            mobile_number: The mobile number to lookup
            call_id: Optional call ID for API calls
            
        Returns:
            Dictionary with account numbers and validation result
        """
        self.logger.info(f"Looking up accounts for mobile: {mobile_number}, call_id: {call_id}")
        try:
            response = self.api_client.get_accounts_by_mobile(mobile_number, call_id)
            if response.get("status", {}).get("gstatus"):
                accounts = response["response"]["responseData"]
                account_list = [{
                    "account_number": acc["key"],
                    "masked_account": acc["value"]
                } for acc in accounts]
                self.logger.info(f"Found {len(account_list)} accounts for mobile {mobile_number}")
                return {
                    "status": "success",
                    "message": f"Found {len(account_list)} accounts",
                    "accounts": account_list
                }
            else:
                self.logger.warning(f"No accounts found for mobile {mobile_number}")
                return {
                    "status": "error",
                    "message": response.get("status", {}).get("gmmsg", "No accounts found"),
                    "accounts": []
                }
        except Exception as e:
            self.logger.error(f"Error looking up accounts for mobile {mobile_number}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error looking up accounts: {str(e)}",
                "accounts": []
            }
