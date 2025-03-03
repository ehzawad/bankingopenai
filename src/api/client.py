#!/usr/bin/env python
# File: banking-assistant/src/api/client.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BankingAPIClient(ABC):
    """Abstract interface for banking API client"""
    
    @abstractmethod
    def get_accounts_by_mobile(self, mobile_number: str, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Get accounts associated with a mobile number
        
        Args:
            mobile_number: The mobile number to look up
            call_id: Optional call ID for tracking
            
        Returns:
            API response containing account numbers
        """
        pass
    
    @abstractmethod
    def verify_pin(self, account_number: str, pin: str, mobile_number: Optional[str] = None, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify PIN for an account
        
        Args:
            account_number: The account number
            pin: The PIN to verify
            mobile_number: Optional mobile number for the customer
            call_id: Optional call ID for tracking
            
        Returns:
            API response with verification result
        """
        pass
    
    @abstractmethod
    def get_account_details(self, account_number: str, mobile_number: Optional[str] = None, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed account information
        
        Args:
            account_number: The account number
            mobile_number: Optional mobile number for the customer
            call_id: Optional call ID for tracking
            
        Returns:
            API response with account details
        """
        pass
