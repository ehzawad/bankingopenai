# File: banking-assistant/src/chat/conversation_manager.py
import logging
from typing import Dict, List, Any, Set, Optional

class ConversationManager:
    """Manages chat conversation state and history"""
    
    def __init__(self, system_prompt: str):
        self.logger = logging.getLogger("banking_assistant.conversation")
        self.system_prompt = system_prompt
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.logger.info("Conversation manager initialized")
    
    def get_conversation(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of conversation messages
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = self._get_initial_prompt()
        return self.conversations[session_id]
    
    def _get_initial_prompt(self) -> List[Dict[str, str]]:
        """Create initial system prompt message
        
        Returns:
            List with system prompt message
        """
        return [{
            "role": "system",
            "content": self.system_prompt
        }]
    
    def add_user_message(self, session_id: str, message: str) -> None:
        """Add a user message to the conversation
        
        Args:
            session_id: The session identifier
            message: User message content
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = self._get_initial_prompt()
        
        self.conversations[session_id].append({
            "role": "user",
            "content": message
        })
        self.logger.debug(f"Added user message for session {session_id}")
    
    def add_assistant_message(self, session_id: str, message: str) -> None:
        """Add an assistant message to the conversation
        
        Args:
            session_id: The session identifier
            message: Assistant message content
        """
        if session_id not in self.conversations:
            self.logger.warning(f"Adding assistant message to non-existent session: {session_id}")
            self.conversations[session_id] = self._get_initial_prompt()
        
        self.conversations[session_id].append({
            "role": "assistant",
            "content": message
        })
        self.logger.debug(f"Added assistant message for session {session_id}")
    
    def add_system_message(self, session_id: str, message: str) -> None:
        """Add a system message to the conversation
        
        Args:
            session_id: The session identifier
            message: System message content
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = self._get_initial_prompt()
        
        self.conversations[session_id].append({
            "role": "system",
            "content": message
        })
        self.logger.debug(f"Added system message for session {session_id}")
    
    def add_tool_call(self, session_id: str, tool_call: Dict[str, Any]) -> None:
        """Add a tool call to the conversation
        
        Args:
            session_id: The session identifier
            tool_call: Tool call data
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = self._get_initial_prompt()
        
        self.conversations[session_id].append({
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        })
        self.logger.debug(f"Added tool call for session {session_id}")
    
    def add_tool_response(self, session_id: str, tool_call_id: str, content: str) -> None:
        """Add a tool response to the conversation
        
        Args:
            session_id: The session identifier
            tool_call_id: The ID of the tool call
            content: Tool response content
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = self._get_initial_prompt()
        
        self.conversations[session_id].append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })
        self.logger.debug(f"Added tool response for session {session_id}")
    
    def end_conversation(self, session_id: str) -> bool:
        """End a conversation by removing its history
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if conversation existed and was removed
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            self.logger.info(f"Ended conversation for session {session_id}")
            return True
        return False
    
    def clear_expired_conversations(self, expired_sessions: List[str]) -> None:
        """Remove conversations for expired sessions
        
        Args:
            expired_sessions: List of expired session IDs
        """
        for session_id in expired_sessions:
            if session_id in self.conversations:
                del self.conversations[session_id]
                self.logger.info(f"Cleared expired conversation for session {session_id}")
