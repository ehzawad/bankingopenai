#!/usr/bin/env python
# File: banking-assistant/src/core/flow/flow_manager.py
import logging
from typing import Dict, Any, List, Callable, Optional
from ..registry import ServiceRegistry

class FlowStep:
    """Represents a single step in a service flow"""
    
    def __init__(
        self, 
        name: str,
        tool_name: str, 
        required_args: List[str],
        optional_args: List[str] = None,
        precondition: Callable[[Dict[str, Any]], bool] = None,
        postcondition: Callable[[Dict[str, Any], Dict[str, Any]], bool] = None,
        result_processor: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]] = None
    ):
        """Initialize a flow step
        
        Args:
            name: Step name for identification
            tool_name: The name of the tool to execute
            required_args: List of required argument names
            optional_args: List of optional argument names
            precondition: Function that determines if step should execute
            postcondition: Function that validates step result
            result_processor: Function to process and extract result values
        """
        self.name = name
        self.tool_name = tool_name
        self.required_args = required_args
        self.optional_args = optional_args or []
        self.precondition = precondition
        self.postcondition = postcondition
        self.result_processor = result_processor
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if this step can be executed with the given context
        
        Args:
            context: The current flow context
            
        Returns:
            True if step can be executed
        """
        # Check if all required args are available
        for arg in self.required_args:
            if arg not in context:
                return False
                
        # Check precondition if specified
        if self.precondition and not self.precondition(context):
            return False
            
        return True
    
    def build_args(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build arguments dictionary from context
        
        Args:
            context: The current flow context
            
        Returns:
            Dictionary of arguments for tool
        """
        args = {}
        for arg in self.required_args:
            args[arg] = context[arg]
        for arg in self.optional_args:
            if arg in context:
                args[arg] = context[arg]
        return args
    
    def process_result(self, args: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the result to extract values for context
        
        Args:
            args: The arguments used for this step
            result: The result from executing the tool
            
        Returns:
            Dictionary of extracted values to add to context
        """
        if self.result_processor:
            return self.result_processor(args, result)
        return {}
    
    def validate_result(self, args: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Validate the result of this step
        
        Args:
            args: The arguments used for this step
            result: The result from executing the tool
            
        Returns:
            True if result is valid
        """
        if self.postcondition:
            return self.postcondition(args, result)
        return True

class ServiceFlow:
    """Defines a sequence of service tool calls"""
    
    def __init__(self, name: str, description: str, steps: List[FlowStep]):
        """Initialize a service flow
        
        Args:
            name: Flow name for identification
            description: Description of the flow
            steps: List of flow steps
        """
        self.name = name
        self.description = description
        self.steps = steps
        self.logger = logging.getLogger(f"banking_assistant.flow.{name}")
        
    async def execute(
        self, 
        registry: ServiceRegistry, 
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the flow with the given context
        
        Args:
            registry: Service registry for executing tools
            initial_context: Initial flow context
            
        Returns:
            Final flow context with results
        """
        context = initial_context.copy()
        executed_steps = []
        context["flow_results"] = {}
        self.logger.info(f"Starting flow execution: {self.name}")
        
        for step in self.steps:
            if not step.can_execute(context):
                self.logger.info(f"Skipping step {step.name}: cannot execute")
                continue
                
            self.logger.info(f"Executing step: {step.name}")
            args = step.build_args(context)
            try:
                result = registry.execute_tool(step.tool_name, args)
                if not step.validate_result(args, result):
                    self.logger.warning(f"Step {step.name} failed validation, stopping flow")
                    context["flow_results"][step.name] = {
                        "status": "validation_failed",
                        "result": result
                    }
                    break
                context["flow_results"][step.name] = {
                    "status": "success",
                    "result": result
                }
                extracted = step.process_result(args, result)
                for key, value in extracted.items():
                    context[key] = value
                executed_steps.append(step.name)
            except Exception as e:
                self.logger.error(f"Error executing step {step.name}: {e}")
                context["flow_results"][step.name] = {
                    "status": "error",
                    "error": str(e)
                }
                break
        
        context["executed_steps"] = executed_steps
        self.logger.info(f"Flow {self.name} completed with {len(executed_steps)} steps")
        return context

class FlowManager:
    """Manages and executes service flows"""
    
    def __init__(self, registry: ServiceRegistry):
        """Initialize the flow manager
        
        Args:
            registry: Service registry for executing tools
        """
        self.registry = registry
        self.logger = logging.getLogger("banking_assistant.flow_manager")
        self.flows: Dict[str, ServiceFlow] = {}
        self._register_standard_flows()
        
    def register_flow(self, flow: ServiceFlow) -> None:
        """Register a flow with the manager
        
        Args:
            flow: The flow to register
        """
        self.flows[flow.name] = flow
        self.logger.info(f"Registered flow: {flow.name}")
        
    async def execute_flow(
        self, 
        flow_name: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a flow by name
        
        Args:
            flow_name: The name of the flow to execute
            context: Initial flow context
            
        Returns:
            Final flow context with results
            
        Raises:
            ValueError: If flow not found
        """
        if flow_name not in self.flows:
            self.logger.error(f"Flow not found: {flow_name}")
            raise ValueError(f"Flow not found: {flow_name}")
        flow = self.flows[flow_name]
        return await flow.execute(self.registry, context)
        
    def _register_standard_flows(self) -> None:
        """Register standard flows"""
        
        # Authentication flow: user provides account number (last 4 digits confirmation) and PIN.
        auth_flow = ServiceFlow(
            name="authentication",
            description="Authenticate a user with account number and PIN",
            steps=[
                FlowStep(
                    name="validate_account",
                    tool_name="validate_account",
                    required_args=["account_number"],
                    result_processor=lambda args, result: {
                        "validate_account_valid": result.get("valid", False)
                    }
                ),
                FlowStep(
                    name="validate_pin",
                    tool_name="validate_pin",
                    required_args=["account_number", "pin"],
                    precondition=lambda ctx: ctx.get("validate_account_valid", False) == True and not ctx.get("validate_pin_valid", False),
                    result_processor=lambda args, result: {
                        "validate_pin_valid": result.get("valid", False)
                    }
                ),
                FlowStep(
                    name="get_account_details",
                    tool_name="get_account_details",
                    required_args=["account_number", "pin"],
                    precondition=lambda ctx: ctx.get("validate_pin_valid", False) == True
                )
            ]
        )
        
        # Account query flow remains unchanged.
        account_query_flow = ServiceFlow(
            name="account_query",
            description="Query specific account information",
            steps=[
                FlowStep(
                    name="get_account_field",
                    tool_name="get_account_field",
                    required_args=["account_number", "field_name"],
                    result_processor=lambda args, result: {
                        "get_account_field_status": result.get("status"),
                        "field_value": result.get("value", "")
                    }
                ),
                FlowStep(
                    name="get_currency_details",
                    tool_name="get_currency_details",
                    required_args=["currency_code"],
                    precondition=lambda ctx: ctx.get("field_name") == "currency" and 
                                              ctx.get("get_account_field_status") == "success" and
                                              ctx.get("field_value", "")
                ),
                FlowStep(
                    name="get_account_type_details",
                    tool_name="get_account_type_details",
                    required_args=["account_type"],
                    precondition=lambda ctx: ctx.get("field_name") == "account_type" and 
                                              ctx.get("get_account_field_status") == "success" and
                                              ctx.get("field_value", "")
                )
            ]
        )
        
        # Note: The previous mobile_authentication flow is removed since we now simply use the mobile number as a static configuration.
        
        self.register_flow(auth_flow)
        self.register_flow(account_query_flow)
