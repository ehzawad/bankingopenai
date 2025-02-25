# File: banking-assistant/src/services/mobile_auth/mobile_auth_service.py
import logging
from typing import Dict, Any, List, Optional

from ...core.interfaces.service_interface import ServiceInterface
from ...api.client import BankingAPIClient
from ..common.tool_definitions import MOBILE_AUTH_TOOLS

class MobileAuthService(ServiceInterface):
    """Service for mobile-based authentication operations"""
    
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
            return self.get_accounts_by_mobile(
                args["mobile_number"],
                args.get("call_id"),
                args.get("session_id")
            )
        else:
            self.logger.error(f"Unknown tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def get_accounts_by_mobile(
        self, 
        mobile_number: str, 
        call_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get accounts associated with a mobile number
        
        Args:
            mobile_number: The mobile number to lookup
            call_id: Optional call ID for API calls
            session_id: Optional session ID for context
            
        Returns:
            Dictionary with account numbers and validation result
        """
        # Log details for debugging
        self.logger.info(f"Looking up accounts for mobile: {mobile_number}, call_id: {call_id}, session_id: {session_id}")
        
        # Call the API to get accounts by mobile number
        response = self.api_client.get_accounts_by_mobile(mobile_number, call_id)
        
        # If successful, format the response for the tools interface
        if response["status"]["gstatus"]:
            accounts = response["response"]["responseData"]
            account_list = []
            
            for account in accounts:
                account_list.append({
                    "account_number": account["key"],
                    "masked_account": account["value"]
                })
            
            self.logger.info(f"Found {len(account_list)} accounts for mobile {mobile_number}")
            
            # Log the account numbers for debugging
            for account in account_list:
                self.logger.debug(f"Account: {account['account_number']} (masked: {account['masked_account']})")
            
            return {
                "status": "success",
                "message": f"Found {len(account_list)} accounts",
                "accounts": account_list
            }
        else:
            self.logger.warning(f"No accounts found for mobile {mobile_number}")
            return {
                "status": "error",
                "message": response["status"].get("gmmsg", "No accounts found for this mobile number"),
                "accounts": []
            }
