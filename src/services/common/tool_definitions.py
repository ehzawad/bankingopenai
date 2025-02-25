# File: banking-assistant/src/services/common/tool_definitions.py
"""
Centralized definitions of tools used by various services
to prevent duplication and ensure consistency.
"""

# Authentication tools
AUTH_TOOLS = [
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

# Account tools
ACCOUNT_TOOLS = [
    # Include the auth tools
    *AUTH_TOOLS,
    # Account-specific tools
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

# Mobile authentication tools
MOBILE_AUTH_TOOLS = [
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
