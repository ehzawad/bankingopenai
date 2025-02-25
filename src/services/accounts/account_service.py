# File: banking-assistant/src/services/accounts/account_service.py
import logging
from typing import Dict, Any, List, Optional

from ...core.interfaces.service_interface import ServiceInterface
from ...api.client import BankingAPIClient
from ..common.tool_definitions import ACCOUNT_TOOLS
from ..authentication.auth_utils import validate_account, validate_pin

class AccountService(ServiceInterface):
    """Service for account-related operations"""
    
    def __init__(self, api_client: BankingAPIClient):
        self.api_client = api_client
        self.logger = logging.getLogger("banking_assistant.services.account")
        self.logger.info("Account service initialized")
    
    @property
    def domain(self) -> str:
        return "account"
    
    @property
    def supported_tools(self) -> List[Dict[str, Any]]:
        return ACCOUNT_TOOLS
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an account-related tool
        
        Args:
            tool_name: The name of the tool to execute
            args: Arguments for the tool
            
        Returns:
            Result of the tool execution
            
        Raises:
            ValueError: If the tool name is not recognized
        """
        self.logger.debug(f"Executing account tool: {tool_name} with args: {args}")
        
        if tool_name == "validate_account":
            mobile_number = args.get("mobile_number")
            return validate_account(self.api_client, args["account_number"], mobile_number)
        elif tool_name == "validate_pin":
            mobile_number = args.get("mobile_number")
            return validate_pin(self.api_client, args["account_number"], args["pin"], mobile_number)
        elif tool_name == "get_account_details":
            mobile_number = args.get("mobile_number")
            return self.get_account_details(args["account_number"], args["pin"], mobile_number)
        elif tool_name == "get_account_field":
            return self.get_account_field(args["account_number"], args["field_name"])
        elif tool_name == "get_currency_details":
            return self.get_currency_details(args["currency_code"])
        elif tool_name == "get_account_type_details":
            return self.get_account_type_details(args["account_type"])
        else:
            self.logger.error(f"Unknown tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def get_account_details(self, account_number: str, pin: str, mobile_number: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed account information
        
        Args:
            account_number: The account number
            pin: The account PIN
            mobile_number: Optional mobile number for additional validation
            
        Returns:
            Dictionary with account details or error message
        """
        # First validate PIN
        pin_validation = validate_pin(self.api_client, account_number, pin, mobile_number)
        if not pin_validation["valid"]:
            self.logger.warning(f"Invalid credentials for account {account_number}")
            return {"status": "error", "message": "Invalid credentials"}
        
        # Get account details
        response = self.api_client.get_account_details(account_number, mobile_number)
        if not response["status"]["gstatus"] or not response["response"]["responseData"]:
            self.logger.warning(f"Account not found: {account_number}")
            return {"status": "error", "message": "Account not found"}
        
        # Extract account data
        account_data = response["response"]["responseData"][0]
        
        # Format balance (handling the trailing space in the API response)
        balance = account_data["currentBalance"].strip()
        currency_code = account_data["currencyCode"]
        currency_details = self.get_currency_details(currency_code)
        currency_symbol = currency_details.get("symbol", currency_code)
        
        # Try to format as float
        try:
            balance_float = float(balance)
            formatted_balance = f"{currency_symbol}{balance_float:,.2f}"
        except ValueError:
            formatted_balance = f"{currency_symbol}{balance}"
        
        # Get account type details
        account_type = account_data["productType"]
        account_type_details = self.get_account_type_details(account_type)
        
        self.logger.info(f"Account details retrieved for {account_number}: balance={formatted_balance}")
        
        return {
            "status": "success",
            "data": {
                "balance": float(balance) if balance else 0.0,
                "formatted_balance": formatted_balance,
                "currency": currency_code,
                "account_type": account_type,
                "account_holder": account_data["accName"],
                "account_status": account_data["accStatus"],
                "last_transaction": account_data["lastTxnDate"],
                "account_features": account_type_details,
                "currency_details": currency_details
            }
        }

    def get_account_field(self, account_number: str, field_name: str) -> Dict[str, Any]:
        """Get a specific field from an account
        
        Args:
            account_number: The account number
            field_name: The field to retrieve
            
        Returns:
            Dictionary with the field value
        """
        # Get account details
        response = self.api_client.get_account_details(account_number)
        if not response["status"]["gstatus"] or not response["response"]["responseData"]:
            return {"status": "error", "message": "Account not found"}
        
        account_data = response["response"]["responseData"][0]
        
        # Map field names to response fields
        field_mapping = {
            "balance": "currentBalance",
            "account_status": "accStatus",
            "currency": "currencyCode",
            "account_type": "productType",
            "last_transaction": "lastTxnDate"
        }
        
        if field_name in field_mapping and field_mapping[field_name] in account_data:
            value = account_data[field_mapping[field_name]]
            
            # Format special fields
            if field_name == "balance":
                currency_code = account_data["currencyCode"]
                currency_details = self.get_currency_details(currency_code)
                currency_symbol = currency_details.get("symbol", currency_code)
                
                try:
                    balance_float = float(value.strip())
                    value = f"{currency_symbol}{balance_float:,.2f}"
                except ValueError:
                    value = f"{currency_symbol}{value}"
                
            return {"status": "success", "value": value}
        
        return {"status": "error", "message": f"Field '{field_name}' not found"}
    
    def get_currency_details(self, currency_code: str) -> Dict[str, Any]:
        """Get currency details
        
        Args:
            currency_code: Currency code
            
        Returns:
            Dictionary with currency details
        """
        # Map of currency codes to details
        currencies = {
            "BDT": {
                "name": "Bangladeshi Taka",
                "symbol": "৳",
                "code": "BDT"
            },
            "USD": {
                "name": "US Dollar",
                "symbol": "$",
                "code": "USD"
            },
            "EUR": {
                "name": "Euro",
                "symbol": "€",
                "code": "EUR"
            }
        }
        
        if currency_code in currencies:
            return {
                "status": "success",
                **currencies[currency_code]
            }
        
        return {
            "status": "success",
            "name": currency_code,
            "symbol": currency_code,
            "code": currency_code
        }
    
    def get_account_type_details(self, account_type: str) -> Dict[str, Any]:
        """Get account type details
        
        Args:
            account_type: Account type
            
        Returns:
            Dictionary with account type details
        """
        # Map of account types to details
        account_types = {
            "SB": {
                "name": "Savings Account",
                "daily_withdrawal_limit": 50000,
                "monthly_fee": 0.00,
                "interest_rate": 3.5,
                "features": ["Debit Card", "Online Banking", "Mobile Banking"]
            },
            "CA": {
                "name": "Current Account",
                "daily_withdrawal_limit": 100000,
                "monthly_fee": 10.00,
                "interest_rate": 0.0,
                "features": ["Checkbook", "Overdraft", "Online Banking"]
            },
            "TD": {
                "name": "Time Deposit",
                "daily_withdrawal_limit": 0,
                "monthly_fee": 0.00,
                "interest_rate": 6.5,
                "features": ["Fixed Tenure", "Higher Interest"]
            }
        }
        
        if account_type in account_types:
            return {
                "status": "success",
                **account_types[account_type]
            }
        
        return {
            "status": "success",
            "name": f"Unknown Account Type ({account_type})",
            "daily_withdrawal_limit": 0,
            "monthly_fee": 0.00,
            "interest_rate": 0.0,
            "features": []
        }