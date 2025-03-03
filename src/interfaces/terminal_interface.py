#!/usr/bin/env python
# File: banking-assistant/src/interfaces/terminal_interface.py
import requests
import json
import uuid
import sys
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple

class TerminalInterface:
    """Terminal interface for the Banking Assistant"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the terminal interface
        
        Args:
            base_url: URL of the Banking Assistant server
        """
        self.server_url = base_url
        self.session_id = f"terminal-{str(uuid.uuid4())}"
        self.caller_id = None  # This now holds the mobile number for API calls
        
        # Print banner
        print("=== Banking Assistant Terminal Interface ===")
        print(f"Connected to server: {base_url}")
        print("Type 'quit' to exit")
        print("Special commands:")
        print("  !inject <prompt> - Inject a system prompt")
        print("  !caller <number> - Set your caller ID (mobile number)")
    
    async def run(self) -> None:
        """Run the terminal interface"""
        # Initial greeting
        self._print_assistant_message("How can I help you today?")
        
        # Main loop
        while True:
            try:
                # Get user input
                user_input = input("You: ")
                
                # Check for quit command
                if user_input.lower() == "quit":
                    print("Goodbye!")
                    await self._end_session()
                    break
                
                # Check for inject command
                if user_input.startswith("!inject "):
                    prompt = user_input[8:]
                    success = await self._inject_prompt(prompt)
                    if success:
                        print("Prompt injected successfully.")
                    else:
                        print("Failed to inject prompt.")
                    continue
                
                # Check for setting caller ID (mobile number)
                if user_input.startswith("!caller "):
                    self.caller_id = user_input[8:].strip()
                    print(f"Caller ID (mobile number) set to: {self.caller_id}")
                    # Note: No account lookup is triggered here.
                    continue
                
                # Send message to server
                response = await self._send_message(user_input)
                
                # Print assistant response
                if response:
                    self._print_assistant_message(response)
                else:
                    self._print_assistant_message("Sorry, there was a server error. Please try again.")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                await self._end_session()
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    async def _send_message(self, message: str) -> Optional[str]:
        """Send a message to the server
        
        Args:
            message: The message to send
            
        Returns:
            The assistant's response or None if there was an error
        """
        try:
            # Prepare request payload
            payload = {
                "message": message,
                "session_id": self.session_id
            }
            
            # Add caller_id (mobile number) if set
            if self.caller_id:
                payload["caller_id"] = self.caller_id
            
            # Send request to server
            response = requests.post(
                f"{self.server_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Check for errors
            if response.status_code != 200:
                print(f"Server error: {response.status_code} - {response.text}")
                return None
            
            # Parse and return response
            data = response.json()
            return data.get("response")
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def _inject_prompt(self, prompt: str) -> bool:
        """Inject a prompt into the session
        
        Args:
            prompt: The prompt to inject
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/inject_prompt",
                params={"prompt": prompt, "session_id": self.session_id}
            )
            
            if response.status_code != 200:
                print(f"Server error: {response.status_code} - {response.text}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error injecting prompt: {e}")
            return False
    
    async def _end_session(self) -> bool:
        """End the current session
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/end_session",
                params={"session_id": self.session_id}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error ending session: {e}")
            return False
    
    def _print_assistant_message(self, message: str) -> None:
        """Print an assistant message
        
        Args:
            message: The message to print
        """
        print("Assistant:", message)
