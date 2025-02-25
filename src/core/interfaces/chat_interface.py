from abc import ABC, abstractmethod
from typing import Dict, Any

class ChatInterface(ABC):
    """Interface for chat interaction methods"""
    
    @abstractmethod
    async def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process incoming message and return response
        
        Args:
            session_id: Unique identifier for the chat session
            message: User message content
            
        Returns:
            Dictionary containing the response and any additional data
        """
        pass
    
    @abstractmethod
    async def end_session(self, session_id: str) -> bool:
        """End a chat session
        
        Args:
            session_id: Unique identifier for the chat session
            
        Returns:
            True if session was successfully ended, False otherwise
        """
        pass
        
    @abstractmethod
    async def inject_prompt(self, session_id: str, prompt: str) -> bool:
        """Inject a custom prompt into an ongoing session
        
        Args:
            session_id: Unique identifier for the chat session
            prompt: The prompt to inject
            
        Returns:
            True if prompt was successfully injected, False otherwise
        """
        pass
