# File: banking-assistant/src/chat/tools/tool_factory.py
from typing import List, Dict, Any, Optional
from ...core.registry import ServiceRegistry

class ToolFactory:
    """Factory for creating and managing LLM tool definitions"""
    
    @staticmethod
    def create_tools(
        registry: ServiceRegistry,
        domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Create tool definitions for the specified domains
        
        Args:
            registry: The service registry containing registered services
            domains: Optional list of domains to include. If None, all domains are included.
            
        Returns:
            List of tool definitions for function calling
        """
        if domains is None:
            # If no domains specified, get tools from all registered services
            return registry.get_all_tools()
        
        # Otherwise, get tools only from the specified domains
        tools = []
        for domain in domains:
            service = registry.get_service(domain)
            if service:
                tools.extend(service.supported_tools)
        
        return tools
