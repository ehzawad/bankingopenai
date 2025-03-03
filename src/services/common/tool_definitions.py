#!/usr/bin/env python
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
            "description": "Validates if an account number exists in the system using the confirmed last 4 digits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The account number to validate (including last 4 digit confirmation)"
                    },
                    "mobile_number": {
                        "type": "string",
                        "description": "Mobile number used for API calls"
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
            "description": "Validates if the PIN is correct for the given account number.",
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
                        "description": "Mobile number used for API calls"
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
            "description": "Retrieves detailed account information for a validated account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The account number"
                    },
                    "mobile_number": {
                        "type": "string",
                        "description": "Mobile number used for API calls"
                    }
                },
                "required": ["account_number"]
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
            "description": "Retrieves accounts associated with a given mobile number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mobile_number": {
                        "type": "string",
                        "description": "The mobile number to look up"
                    },
                    "call_id": {
                        "type": "string",
                        "description": "Optional call ID for tracking"
                    }
                },
                "required": ["mobile_number"]
            }
        }
    }
]

# Account-specific tools
ACCOUNT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_account_field",
            "description": "Retrieves a specific field from an account",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The account number"
                    },
                    "field_name": {
                        "type": "string",
                        "description": "The specific field to retrieve"
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
            "description": "Retrieves details about the account currency",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code of the account"
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
            "description": "Retrieves details about the account type",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "description": "Type of the account"
                    }
                },
                "required": ["account_type"]
            }
        }
    }
]
