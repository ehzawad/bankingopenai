# File: banking-assistant/src/core/registry.py
import logging
from typing import Dict, Any, List, Optional
from .interfaces.service_interface import ServiceInterface

class ServiceRegistry:
    """Registry for all service implementations in the system"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInterface] = {}
        self.logger = logging.getLogger("banking_assistant.registry")
        
    def register_service(self, service: ServiceInterface) -> None:
        """Register a service with the registry
        
        Args:
            service: The service implementation to register
        """
        domain = service.domain
        self.services[domain] = service
        self.logger.info(f"Registered service for domain: {domain}")
        
    def get_service(self, domain: str) -> Optional[ServiceInterface]:
        """Get a service by its domain
        
        Args:
            domain: The domain identifier
            
        Returns:
            The service implementation or None if not found
        """
        service = self.services.get(domain)
        if not service:
            self.logger.warning(f"No service registered for domain: {domain}")
        return service
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all registered services
        
        Returns:
            List of all tool definitions from all services
        """
        all_tools = []
        for service in self.services.values():
            all_tools.extend(service.supported_tools)
        return all_tools
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name across all services
        
        Args:
            tool_name: The name of the tool to execute
            args: Arguments to pass to the tool
            
        Returns:
            Result of the tool execution
            
        Raises:
            ValueError: If the tool is not found in any service
        """
        for service in self.services.values():
            for tool in service.supported_tools:
                if tool["function"]["name"] == tool_name:
                    self.logger.info(f"Executing tool: {tool_name} with args: {args}")
                    return service.execute_tool(tool_name, args)
        
        self.logger.error(f"No service found with tool: {tool_name}")
        raise ValueError(f"Tool not found: {tool_name}")
    
    @property
    def domains(self) -> List[str]:
        """Get list of all registered domains
        
        Returns:
            List of domain identifiers
        """
        return list(self.services.keys())
