from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ServiceInterface(ABC):
    """Base interface for all domain-specific services in the system"""
    
    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the domain identifier for this service"""
        pass
    
    @property
    @abstractmethod
    def supported_tools(self) -> List[Dict[str, Any]]:
        """Return the tools supported by this service for LLM function calling"""
        pass
    
    @abstractmethod
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool provided by this service"""
        pass
