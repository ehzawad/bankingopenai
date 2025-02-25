# File: banking-assistant/src/providers/llm/openai_provider.py
import logging
import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from ...core.interfaces.llm_provider import LLMProvider

class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLMProvider interface"""
    
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_TEMPERATURE = 0.0  # Low temperature for more consistent responses
    
    def __init__(
        self, 
        api_key: str = None, 
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """Initialize the OpenAI provider
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
            model: The model to use for chat completions (defaults to DEFAULT_MODEL)
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate in the response
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.temperature = temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", self.DEFAULT_TEMPERATURE))
        self.max_tokens = max_tokens if max_tokens is not None else int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        
        self.logger = logging.getLogger("banking_assistant.llm.openai")
        self.logger.info(f"Initialized OpenAI provider with model: {self.model}, temperature: {self.temperature}")

    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a response from the OpenAI language model
        
        Args:
            messages: List of message objects with role and content
            tools: Optional list of tool definitions for function calling
            
        Returns:
            Dictionary containing the response content and any tool calls
        """
        try:
            self.logger.debug(f"Sending request to OpenAI with {len(messages)} messages")
            if tools:
                self.logger.debug(f"Request includes {len(tools)} tools")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            
            result = response.choices[0].message

            # Serialize tool_calls if present
            tool_calls = []
            if hasattr(result, 'tool_calls') and result.tool_calls:
                self.logger.info(f"Response contains {len(result.tool_calls)} tool calls")
                for tc in result.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
            
            return {
                "content": result.content,
                "tool_calls": tool_calls
            }
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"OpenAI API error: {error_message}", exc_info=True)
            
            # Provide more specific error messages based on common issues
            if "Rate limit" in error_message:
                return {"content": "Sorry, the service is currently busy. Please try again in a moment.", "tool_calls": []}
            elif "Invalid API key" in error_message:
                return {"content": "Service configuration error. Please contact support.", "tool_calls": []}
            elif "context_length_exceeded" in error_message:
                return {"content": "The conversation has become too long. Please start a new session.", "tool_calls": []}
            else:
                return {"content": "Sorry, I encountered an error processing your request.", "tool_calls": []}
