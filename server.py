#!/usr/bin/env python3
# File: banking-assistant/server.py

import os
import sys
import uvicorn
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import project modules
from src.providers.llm.openai_provider import OpenAIProvider
from src.api.client_factory import APIClientFactory
from src.services.accounts.account_service import AccountService
from src.services.authentication.auth_service import AuthenticationService
from src.services.mobile_auth.mobile_auth_service import MobileAuthService
from src.chat.banking_chatbot import BankingChatbot
from src.interfaces.fastapi_interface import FastAPIInterface
from src.core.registry import ServiceRegistry
from config.prompts.prompt_manager import PromptManager

# Removed unused PromptInjection class

def setup_logger():
    """Configure logging for the application"""
    logger = logging.getLogger("banking_assistant")
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler("banking_assistant.log")
    file_handler.setLevel(logging.DEBUG)
    
    # Format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def main():
    # Setup logger
    logger = setup_logger()
    logger.info("Starting Banking Assistant Server")
    
    # Get configuration from environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
    use_real_api = os.getenv("USE_REAL_API", "").lower() in ("true", "1", "yes")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Validate required configuration
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set!")
        print("Error: OPENAI_API_KEY environment variable not set!")
        return
    
    # Initialize OpenAI provider with configuration
    logger.info(f"Initializing OpenAI provider with model: {openai_model}")
    llm_provider = OpenAIProvider(
        api_key=openai_api_key,
        model=openai_model
    )
    
    # Create API client
    logger.info(f"Creating banking API client (using real API: {use_real_api})")
    api_client = APIClientFactory.create_client(use_real_api)
    
    # Initialize service registry
    logger.info("Initializing service registry")
    registry = ServiceRegistry()
    
    # Initialize account service and register it
    logger.info("Initializing account service")
    account_service = AccountService(api_client)
    registry.register_service(account_service)
    
    # Initialize authentication service and register it
    logger.info("Initializing authentication service")
    auth_service = AuthenticationService(api_client)
    registry.register_service(auth_service)
    
    # Initialize mobile authentication service and register it
    logger.info("Initializing mobile authentication service")
    mobile_auth_service = MobileAuthService(api_client)
    registry.register_service(mobile_auth_service)
    
    # Initialize prompt manager
    logger.info("Initializing prompt manager")
    prompt_manager = PromptManager()
    
    # Initialize banking chatbot with all services
    logger.info("Initializing banking chatbot")
    chatbot = BankingChatbot(llm_provider, registry, prompt_manager)
    
    # Create FastAPI app and interface
    logger.info("Setting up FastAPI interface")
    app = FastAPI(
        title="Banking Assistant API",
        description="API for the Banking Assistant chatbot",
        version="1.0.0"
    )
    interface = FastAPIInterface(chatbot, app)
    
    # Add middleware for logging
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    
    # Add health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint
        
        Returns:
            Service health status
        """
        return {
            "status": "ok",
            "version": "1.0.0",
            "services": {
                "account": True,
                "authentication": True,
                "mobile_auth": True
            }
        }
    
    logger.info(f"Starting Banking Assistant API server on http://{host}:{port}")
    print(f"Starting Banking Assistant API server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
