#!/usr/bin/env python
# File: banking-assistant/src/services/authentication/auth_manager.py
import logging
import time
from typing import Dict, Tuple, Optional, List

class AuthenticationManager:
    """Manages authentication state and session management"""
    
    # Session timeout in seconds (15 minutes)
    SESSION_TIMEOUT = 15 * 60
    
    def __init__(self):
        self.logger = logging.getLogger("banking_assistant.auth_manager")
        # Store authenticated sessions with account number and timestamp
        self.authenticated_sessions: Dict[str, Tuple[str, float]] = {}
        self.logger.info("Authentication manager initialized")
    
    def authenticate_session(self, session_id: str, account_number: str) -> None:
        """Mark a session as authenticated for an account
        
        Args:
            session_id: The session identifier
            account_number: The authenticated account number
        """
        self.authenticated_sessions[session_id] = (account_number, time.time())
        self.logger.info(f"Session {session_id} authenticated for account {account_number}")
    
    def get_authenticated_account(self, session_id: str) -> Optional[str]:
        """Get the account number for an authenticated session
        
        Args:
            session_id: The session identifier
            
        Returns:
            The account number or None if not authenticated
        """
        if session_id in self.authenticated_sessions:
            account_number, _ = self.authenticated_sessions[session_id]
            return account_number
        return None
    
    def is_authenticated(self, session_id: str) -> bool:
        """Check if a session is authenticated and not expired
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session is authenticated and active
        """
        if session_id not in self.authenticated_sessions:
            return False
            
        _, last_activity = self.authenticated_sessions[session_id]
        return (time.time() - last_activity) <= self.SESSION_TIMEOUT
    
    def update_session_activity(self, session_id: str) -> None:
        """Update the last activity timestamp for a session
        
        Args:
            session_id: The session identifier
        """
        if session_id in self.authenticated_sessions:
            account_number, _ = self.authenticated_sessions[session_id]
            self.authenticated_sessions[session_id] = (account_number, time.time())
    
    def cleanup_expired_sessions(self) -> List[str]:
        """Remove expired sessions based on timeout
        
        Returns:
            List of expired session IDs that were removed
        """
        current_time = time.time()
        expired_sessions = []
        for session_id, (_, last_activity) in list(self.authenticated_sessions.items()):
            if current_time - last_activity > self.SESSION_TIMEOUT:
                expired_sessions.append(session_id)
        for session_id in expired_sessions:
            self.logger.info(f"Removing expired session: {session_id}")
            if session_id in self.authenticated_sessions:
                del self.authenticated_sessions[session_id]
        return expired_sessions
    
    def end_session(self, session_id: str) -> bool:
        """End a session by removing authentication
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session was ended, False otherwise
        """
        if session_id in self.authenticated_sessions:
            del self.authenticated_sessions[session_id]
            self.logger.info(f"Session {session_id} ended")
            return True
        return False
