# File: banking-assistant/src/chat/tools/mobile_auth_tools.py
from typing import List, Dict, Any

class MobileAuthTools:
    """Defines tools for mobile number-based authentication"""
    
    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """Get the list of mobile auth tools for function calling
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_accounts_by_mobile",
                    "description": "Get account numbers associated with a mobile number",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mobile_number": {
                                "type": "string",
                                "description": "The mobile number to lookup accounts for"
                            },
                            "call_id": {
                                "type": "string",
                                "description": "Optional call ID for tracking purposes"
                            }
                        },
                        "required": ["mobile_number"]
                    }
                }
            }
        ]