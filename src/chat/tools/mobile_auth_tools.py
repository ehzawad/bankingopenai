# File: banking-assistant/src/chat/tools/mobile_auth_tools.py
from typing import List, Dict, Any
from ...services.common.tool_definitions import MOBILE_AUTH_TOOLS

class MobileAuthTools:
    """Defines tools for mobile number-based authentication"""
    
    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """Get the list of mobile auth tools for function calling
        
        Returns:
            List of tool definitions
        """
        return MOBILE_AUTH_TOOLS
