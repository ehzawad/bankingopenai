#!/usr/bin/env python
# File: banking-assistant/src/interfaces/fastapi_interface.py
import logging
import uuid
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ..core.interfaces.chat_interface import ChatInterface

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    caller_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str

class ChatHistory(BaseModel):
    """Chat history model"""
    history: List[Dict[str, Any]]

class FastAPIInterface:
    """FastAPI interface for the Banking Assistant"""
    
    def __init__(self, chat_interface: ChatInterface, app: FastAPI):
        """Initialize the FastAPI interface
        
        Args:
            chat_interface: Chat interface implementation
            app: FastAPI application
        """
        self.chat = chat_interface
        self.app = app
        self.logger = logging.getLogger("banking_assistant.interface.fastapi")
        
        # Register routes
        self._register_routes()
        self.logger.info("FastAPI interface initialized")
    
    def _register_routes(self):
        """Register API routes"""
        
        @self.app.post("/chat", response_model=ChatResponse, tags=["Chat"])
        async def chat(request: ChatRequest, user_agent: str = Header(None)):
            """Chat endpoint
            
            Args:
                request: Chat request
                user_agent: User agent header
                
            Returns:
                Chat response
            """
            try:
                session_id = request.session_id or str(uuid.uuid4())
                self.logger.info(f"Chat request from {user_agent or 'unknown'} with session {session_id}")
                
                # Process the message
                result = await self.chat.process_message(
                    session_id=session_id,
                    message=request.message,
                    caller_id=request.caller_id,
                    channel="web"
                )
                
                return {
                    "response": result["response"],
                    "session_id": session_id
                }
            except Exception as e:
                self.logger.error(f"Error processing chat request: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while processing your request"
                )
        
        @self.app.post("/inject_prompt", tags=["System"])
        async def inject_prompt(
            prompt: str,
            session_id: str,
            api_key: Optional[str] = Header(None)
        ):
            """Inject a prompt into a session
            
            Args:
                prompt: The prompt to inject
                session_id: The session ID
                api_key: API key for authentication
                
            Returns:
                Success status
            """
            # In a real application, you'd verify the API key here
            try:
                result = await self.chat.inject_prompt(session_id, prompt)
                return {"success": result}
            except Exception as e:
                self.logger.error(f"Error injecting prompt: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while injecting the prompt"
                )
        
        @self.app.post("/end_session", tags=["Chat"])
        async def end_session(session_id: str):
            """End a chat session
            
            Args:
                session_id: The session ID to end
                
            Returns:
                Success status
            """
            try:
                result = await self.chat.end_session(session_id)
                return {"success": result}
            except Exception as e:
                self.logger.error(f"Error ending session: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while ending the session"
                )
                
        # IVR-specific endpoint for phone interactions
        @self.app.post("/ivr/chat", response_model=ChatResponse, tags=["IVR"])
        async def ivr_chat(
            request: Request,
            message: str,
            session_id: Optional[str] = None,
            caller_id: Optional[str] = Header(None),
            call_id: Optional[str] = Header(None)
        ):
            """IVR chat endpoint
            
            Args:
                request: Request object
                message: User message
                session_id: Session ID
                caller_id: Caller ID (phone number)
                call_id: Call ID from IVR system
                
            Returns:
                Chat response
            """
            try:
                # Generate session ID if not provided
                session_id = session_id or f"ivr_{str(uuid.uuid4())}"
                
                # If caller_id not in header, try to get from request params
                if not caller_id:
                    caller_id = request.query_params.get("cli")
                
                self.logger.info(f"IVR chat request from {caller_id or 'unknown'} with session {session_id}")
                
                # Process the message
                result = await self.chat.process_message(
                    session_id=session_id,
                    message=message,
                    caller_id=caller_id,
                    channel="ivr"
                )
                
                return {
                    "response": result["response"],
                    "session_id": session_id
                }
            except Exception as e:
                self.logger.error(f"Error processing IVR chat request: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while processing your request"
                )
        
        self.logger.info("API routes registered")
