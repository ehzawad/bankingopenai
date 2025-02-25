# File: banking-assistant/src/core/interfaces/llm_provider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProvider(ABC):
    """Interface for Language Model providers"""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a response from the language model
        
        Args:
            messages: List of message objects with role and content
            tools: Optional list of tool definitions for function calling
            
        Returns:
            Dictionary containing the response content and any tool calls
        """
        pass
