# File: banking-assistant/src/utils/error_handling.py
"""
Standard error handling utilities for consistent error management
throughout the application.
"""

import logging
import functools
from typing import Any, Callable, Dict, Type, Optional

# Configure logger
logger = logging.getLogger("banking_assistant.error_handling")

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ValidationError(APIError):
    """Error for validation failures"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)

class NotFoundError(APIError):
    """Error for resources not found"""
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} not found: {identifier}"
        super().__init__(message, code=404)

class AuthenticationError(APIError):
    """Error for authentication failures"""
    def __init__(self, message: str):
        super().__init__(message, code=401)

def handle_exceptions(
    func: Callable = None, 
    default_value: Any = None,
    error_map: Dict[Type[Exception], Any] = None
) -> Callable:
    """Decorator for consistent exception handling
    
    Args:
        func: Function to decorate
        default_value: Default value to return on exception
        error_map: Mapping of exception types to return values
        
    Returns:
        Decorated function
    """
    if func is None:
        return functools.partial(
            handle_exceptions, default_value=default_value, error_map=error_map
        )
        
    error_map = error_map or {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get the calling function or module name for logging
            caller = func.__qualname__
            
            # Handle specific exception types if in error_map
            for exc_type, return_value in error_map.items():
                if isinstance(e, exc_type):
                    logger.warning(f"Handled {exc_type.__name__} in {caller}: {str(e)}")
                    return return_value
            
            # Generic exception handling
            logger.error(f"Exception in {caller}: {str(e)}", exc_info=True)
            return default_value
            
    return wrapper

async def handle_async_exceptions(
    func: Callable = None, 
    default_value: Any = None,
    error_map: Dict[Type[Exception], Any] = None
) -> Callable:
    """Decorator for consistent async exception handling
    
    Args:
        func: Async function to decorate
        default_value: Default value to return on exception
        error_map: Mapping of exception types to return values
        
    Returns:
        Decorated async function
    """
    if func is None:
        return functools.partial(
            handle_async_exceptions, default_value=default_value, error_map=error_map
        )
        
    error_map = error_map or {}
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Get the calling function or module name for logging
            caller = func.__qualname__
            
            # Handle specific exception types if in error_map
            for exc_type, return_value in error_map.items():
                if isinstance(e, exc_type):
                    logger.warning(f"Handled {exc_type.__name__} in {caller}: {str(e)}")
                    return return_value
            
            # Generic exception handling
            logger.error(f"Exception in {caller}: {str(e)}", exc_info=True)
            return default_value
            
    return wrapper

def format_error_response(error: Exception) -> Dict[str, Any]:
    """Format error as a standardized API response
    
    Args:
        error: The exception to format
        
    Returns:
        Standardized error response dictionary
    """
    if isinstance(error, APIError):
        response = {
            "status": "error",
            "error": {
                "message": error.message,
                "code": error.code
            }
        }
        
        # Add details if available
        if hasattr(error, "details") and error.details:
            response["error"]["details"] = error.details
            
        return response
    else:
        # Generic error formatting
        return {
            "status": "error",
            "error": {
                "message": str(error),
                "code": 500
            }
        }
