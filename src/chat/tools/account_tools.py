# File: banking-assistant/src/chat/tools/account_tools.py
from typing import List, Dict, Any

class AccountTools:
    """Defines tools for account-related operations"""
    
    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """Get the list of account-related tools for function calling
        
        Returns:
            List of tool definitions
        """
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
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_details",
                    "description": "Get detailed information about an account",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "description": "The account number"
                            },
                            "pin": {
                                "type": "string",
                                "description": "The PIN for the account"
                            },
                            "mobile_number": {
                                "type": "string",
                                "description": "Optional mobile number for additional validation"
                            }
                        },
                        "required": ["account_number", "pin"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_field",
                    "description": "Get a specific field from an authenticated account",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "description": "The account number"
                            },
                            "field_name": {
                                "type": "string",
                                "description": "The field to retrieve (e.g., balance, last_transaction, account_status)"
                            }
                        },
                        "required": ["account_number", "field_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_currency_details",
                    "description": "Get details about a currency",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "currency_code": {
                                "type": "string",
                                "description": "The currency code (e.g., USD, EUR)"
                            }
                        },
                        "required": ["currency_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_type_details",
                    "description": "Get details about an account type",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_type": {
                                "type": "string",
                                "description": "The account type (e.g., checking, savings)"
                            }
                        },
                        "required": ["account_type"]
                    }
                }
            }
        ]