# File: banking-assistant/src/api/client_factory.py
import os
import logging
from typing import Dict, Any

from .client import BankingAPIClient
from .mock_client import MockBankingAPIClient
from .real_client import RealBankingAPIClient

class APIClientFactory:
    """Factory for creating API clients"""
    
    @staticmethod
    def create_client(use_real_api: bool = False, config: Dict[str, Any] = None) -> BankingAPIClient:
        """Create an API client
        
        Args:
            use_real_api: Whether to use the real API client
            config: Optional configuration for the client
            
        Returns:
            An instance of BankingAPIClient
        """
        logger = logging.getLogger("banking_assistant.api.factory")
        
        # Use environment variable if not explicitly specified
        if not use_real_api:
            use_real_api = os.getenv("USE_REAL_API", "").lower() in ("true", "1", "yes")
        
        # Default config if none provided
        if config is None:
            config = {}
        
        if use_real_api:
            # Get config for real API client
            base_url = config.get("base_url") or os.getenv("API_BASE_URL", "http://10.45.14.24/ccmwmtb")
            api_secret = config.get("api_secret") or os.getenv("API_SECRET", "PVFzWnlWQmJsdkNxQUszcWJrbFlUNjJVREpVMXR6R09kTHN5QXNHYSt1ZWM=")
            timeout = int(config.get("timeout") or os.getenv("API_TIMEOUT", "30"))
            
            logger.info(f"Creating real API client with base URL: {base_url}")
            return RealBankingAPIClient(
                base_url=base_url,
                api_secret=api_secret,
                timeout=timeout
            )
        else:
            # Use mock client
            logger.info("Creating mock API client")
            return MockBankingAPIClient()
