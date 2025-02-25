# File: banking-assistant/src/services/authentication/auth_service.py
import logging
from typing import Dict, Any, List, Optional

from ...core.interfaces.service_interface import ServiceInterface
from ...api.client import BankingAPIClient
from ..common.tool_definitions import AUTH_TOOLS
from .auth_utils import validate_account, validate_pin

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
        return AUTH_TOOLS
    
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
            return validate_account(self.api_client, args["account_number"], mobile_number)
        elif tool_name == "validate_pin":
            mobile_number = args.get("mobile_number")
            return validate_pin(self.api_client, args["account_number"], args["pin"], mobile_number)
        else:
            self.logger.error(f"Unknown authentication tool: {tool_name}")
            raise ValueError(f"Unknown authentication tool: {tool_name}")