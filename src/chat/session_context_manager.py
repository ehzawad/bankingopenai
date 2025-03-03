# File: banking-assistant/src/chat/session_context_manager.py
import logging
import time
from typing import Dict, Any, Optional, List

class SessionContextManager:
    """Manages session-level context data including caller information"""
    
    def __init__(self):
        self.logger = logging.getLogger("banking_assistant.session_context")
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        self.logger.info("Session context manager initialized")
    
    def initialize_session(
        self, 
        session_id: str, 
        caller_id: Optional[str] = None,
        channel: str = "web"
    ) -> None:
        """Initialize a new session with context data
        
        Args:
            session_id: The session identifier
            caller_id: The phone number of the caller (for IVR/phone channels)
            channel: The channel type (web, ivr, sms, etc.)
        """
        self.session_contexts[session_id] = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "caller_id": caller_id,
            "channel": channel,
            "account_retrieved": False,
            "account_selected": False,  # Track account selection state
            "retrieved_accounts": [],
            "selected_account": None,
            "awaiting_pin": False,  # Track if we're waiting for PIN
            "call_id": f"{int(time.time())}{session_id[-10:]}"  # Generate a call ID similar to the logs
        }
        self.logger.info(f"Initialized session context for {session_id} with caller_id {caller_id}")
    
    def update_session_context(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update session context with new values
        
        Args:
            session_id: The session identifier
            updates: Dictionary of key/value pairs to update
        """
        if session_id not in self.session_contexts:
            self.initialize_session(session_id)
            
        for key, value in updates.items():
            self.session_contexts[session_id][key] = value
            
        # Always update last activity time
        self.session_contexts[session_id]["last_activity"] = time.time()
        
        # Log the current state for debugging
        self.logger.debug(f"Updated session context for {session_id}: {updates}")
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get the full context data for a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session context dictionary or empty dict if not found
        """
        if session_id not in self.session_contexts:
            self.initialize_session(session_id)
            
        return self.session_contexts[session_id]
    
    def get_caller_id(self, session_id: str) -> Optional[str]:
        """Get the caller ID associated with a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            Caller ID (phone number) or None if not available
        """
        context = self.get_session_context(session_id)
        return context.get("caller_id")
    
    def get_call_id(self, session_id: str) -> str:
        """Get the call ID associated with a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            Call ID for API calls
        """
        context = self.get_session_context(session_id)
        return context.get("call_id", f"{int(time.time())}{session_id[-10:]}")
    
    def set_retrieved_accounts(self, session_id: str, accounts: list) -> None:
        """Set the accounts retrieved for a session
        
        Args:
            session_id: The session identifier
            accounts: List of account information dictionaries
        """
        self.logger.info(f"Setting retrieved accounts for session {session_id}")
        for account in accounts:
            self.logger.info(f"Account: {account['account_number']} (masked: {account.get('masked_account', 'N/A')})")
            
        self.update_session_context(session_id, {
            "retrieved_accounts": accounts,
            "account_retrieved": True,
            "account_selected": False,  # Reset selection state
            "selected_account": None,  # Clear any previous selection
            "awaiting_pin": False  # Not waiting for PIN yet
        })
    
    def set_selected_account(self, session_id: str, account_number: str) -> None:
        """Set the currently selected account for a session
        
        Args:
            session_id: The session identifier
            account_number: The selected account number
        """
        # Validate that we're storing a full account number, not just the last digits
        if len(account_number) < 10:
            self.logger.error(f"Attempted to store incomplete account number: {account_number}")
            raise ValueError(f"Invalid account number format: {account_number}")
        
        self.update_session_context(session_id, {
            "selected_account": account_number,
            "account_selected": True,
            "awaiting_pin": True  # Now waiting for PIN
        })
        self.logger.info(f"Account {account_number} selected for session {session_id}, now awaiting PIN")
    
    def get_selected_account(self, session_id: str) -> Optional[str]:
        """Get the currently selected account for a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            Selected account number or None if not set
        """
        context = self.get_session_context(session_id)
        account_number = context.get("selected_account")
        
        # Add validation to ensure we're not returning just the last digits
        if account_number and len(account_number) < 10:
            self.logger.error(f"Retrieved incomplete account number: {account_number}")
            return None
            
        return account_number
    
    def is_account_selected(self, session_id: str) -> bool:
        """Check if an account has been selected
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if an account has been selected
        """
        context = self.get_session_context(session_id)
        return context.get("account_selected", False)
    
    def is_awaiting_pin(self, session_id: str) -> bool:
        """Check if we're waiting for a PIN
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if waiting for PIN
        """
        context = self.get_session_context(session_id)
        return context.get("awaiting_pin", False)
    
    def get_retrieved_accounts(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the accounts retrieved for a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of account information dictionaries
        """
        context = self.get_session_context(session_id)
        accounts = context.get("retrieved_accounts", [])
        self.logger.debug(f"Retrieved {len(accounts)} accounts for session {session_id}")
        for account in accounts:
            self.logger.debug(f"Account: {account['account_number']} (masked: {account.get('masked_account', 'N/A')})")
        return accounts
    
    def has_accounts(self, session_id: str) -> bool:
        """Check if accounts have been retrieved for a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if accounts have been retrieved
        """
        context = self.get_session_context(session_id)
        return context.get("account_retrieved", False)
    
    def clear_expired_sessions(self, expired_session_ids: list) -> None:
        """Remove expired sessions
        
        Args:
            expired_session_ids: List of expired session IDs to remove
        """
        for session_id in expired_session_ids:
            if session_id in self.session_contexts:
                del self.session_contexts[session_id]
                self.logger.info(f"Cleared expired session context for {session_id}")
    
    def end_session(self, session_id: str) -> bool:
        """End a session by removing its context
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session was found and removed
        """
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
            self.logger.info(f"Ended session context for {session_id}")
            return True
        return False
