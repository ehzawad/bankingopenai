# File: banking-assistant/src/chat/tools/account_tools.py
from typing import List, Dict, Any
from ...services.common.tool_definitions import ACCOUNT_TOOLS

class AccountTools:
    """Defines tools for account-related operations"""
    
    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """Get the list of account-related tools for function calling
        
        Returns:
            List of tool definitions
        """
        return ACCOUNT_TOOLS
