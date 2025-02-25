# File: banking-assistant/src/chat/banking_chatbot.py
import json
import logging
import re
from typing import Dict, List, Any, Set, Optional, Tuple
from ..core.interfaces.chat_interface import ChatInterface
from ..core.interfaces.llm_provider import LLMProvider
from ..core.registry import ServiceRegistry
from ..core.flow.flow_manager import FlowManager
from .tools.tool_factory import ToolFactory
from .conversation_manager import ConversationManager
from .session_context_manager import SessionContextManager
from ..services.authentication.auth_manager import AuthenticationManager
from config.prompts.prompt_manager import PromptManager

class BankingChatbot(ChatInterface):
    """Implementation of the ChatInterface for banking services"""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        service_registry: ServiceRegistry,
        prompt_manager: PromptManager,
        active_domains: List[str] = None
    ):
        self.logger = logging.getLogger("banking_assistant.chatbot")
        self.llm = llm_provider
        self.registry = service_registry
        self.prompt_manager = prompt_manager
        self.active_domains = active_domains or service_registry.domains
        self.logger.info(f"Active domains: {', '.join(self.active_domains)}")
        
        # Initialize new components
        self.system_prompt = prompt_manager.compose_prompt(self.active_domains)
        self.logger.info(f"Loaded system prompt: {self.system_prompt[:100]}...")
        self.conversation_manager = ConversationManager(self.system_prompt)
        self.auth_manager = AuthenticationManager()
        self.flow_manager = FlowManager(service_registry)
        self.session_context = SessionContextManager()
        
        self.restricted_keywords: Set[str] = {
            "credit card", "loan", "investment", "mortgage", "insurance", 
            "wealth management", "stock", "trading", "mutual fund", "bond"
        }
        
        self.logger.info("Banking chatbot initialized with authentication flow")
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools for active domains
        
        Returns:
            List of tool definitions
        """
        self.logger.debug("Getting available tools for active domains")
        return ToolFactory.create_tools(self.registry, self.active_domains)
    
    async def process_message(
        self, 
        session_id: str, 
        message: str, 
        caller_id: Optional[str] = None,
        channel: str = "web"
    ) -> Dict[str, Any]:
        """Process a user message and generate a response
        
        Args:
            session_id: The session identifier
            message: User message content
            caller_id: Optional caller ID (phone number) for automatic account lookup
            channel: Channel type (web, ivr, etc.)
            
        Returns:
            Dictionary with response
        """
        try:
            self.logger.info(f"Processing message for session {session_id}")
            
            # Initialize or update session context with caller information
            if not self.session_context.get_caller_id(session_id) and caller_id:
                self.logger.info(f"Initializing session with caller_id: {caller_id}")
                self.session_context.initialize_session(session_id, caller_id, channel)
            elif caller_id:
                self.logger.info(f"Updating session with caller_id: {caller_id}")
                self.session_context.update_session_context(
                    session_id, {"caller_id": caller_id, "channel": channel}
                )
            
            # Cleanup expired sessions
            expired_sessions = self.auth_manager.cleanup_expired_sessions()
            self.conversation_manager.clear_expired_conversations(expired_sessions)
            self.session_context.clear_expired_sessions(expired_sessions)
            
            # Update session activity timestamp if authenticated
            self.auth_manager.update_session_activity(session_id)
            
            # Debugging: Log the current state
            session_state = self.session_context.get_session_context(session_id)
            self.logger.debug(f"Current session state: {session_state}")
            
            # Check for restricted keywords
            if self._contains_restricted_keywords(message):
                self.logger.info(f"Message contains restricted keywords: {message}")
                return {
                    "response": (
                        "I'm sorry, but I can only provide account balance information for standard deposit accounts. "
                        "For inquiries regarding other products like loans, credit cards, or investments, "
                        "please contact our customer support team."
                    )
                }
            
            # Automatic account lookup if we have caller_id and no accounts yet
            session_ctx = self.session_context.get_session_context(session_id)
            caller_id = session_ctx.get("caller_id")
            
            if caller_id and not self.session_context.has_accounts(session_id):
                self.logger.info(f"Performing automatic account lookup for caller: {caller_id}")
                await self._auto_lookup_accounts(session_id, caller_id)
            
            # If already authenticated, try handling field-specific queries
            if self.auth_manager.is_authenticated(session_id):
                account_number = self.auth_manager.get_authenticated_account(session_id)
                self.logger.info(f"User is already authenticated for account: {account_number}")
                field_response = await self._handle_field_query(session_id, account_number, message)
                if field_response:
                    return {"response": field_response}
            
            # STATE MACHINE:
            # 1. If we have accounts but no selected account, look for last 4 digits
            # 2. If we have a selected account but not authenticated, look for PIN
            # 3. Otherwise, continue with normal processing
            
            # 1. Check if user message contains last 4 digits of account number
            if (self.session_context.has_accounts(session_id) and 
                not self.session_context.is_account_selected(session_id)):
                
                last_4_digits = self._extract_last_4_digits(message)
                if last_4_digits:
                    self.logger.info(f"STEP 1: Detected last 4 digits of account: {last_4_digits}")
                    account_match = await self._match_account_by_last_digits(session_id, last_4_digits)
                    if account_match:
                        return account_match
            
            # 2. Check if user message is a PIN (after we've selected an account)
            elif (self.session_context.is_account_selected(session_id) and 
                  self.session_context.is_awaiting_pin(session_id) and
                  not self.auth_manager.is_authenticated(session_id)):
                
                pin = self._extract_pin(message)
                if pin:
                    self.logger.info(f"STEP 2: Detected PIN in message: {pin}")
                    account_number = self.session_context.get_selected_account(session_id)
                    if account_number:
                        pin_response = await self._handle_pin_validation(session_id, account_number, pin)
                        if pin_response:
                            return pin_response
            
            # 3. Normal processing for other messages
            
            # Add user message to conversation
            self.conversation_manager.add_user_message(session_id, message)
            
            # Get current conversation state
            conversation = self.conversation_manager.get_conversation(session_id)
            
            # If we have accounts but no selection yet, guide the assistant to ask for last 4 digits
            if (self.session_context.has_accounts(session_id) and 
                not self.session_context.is_account_selected(session_id)):
                
                # Add explicit guidance to the assistant
                self.conversation_manager.add_system_message(
                    session_id,
                    "The user has accounts associated with their phone number. "
                    "Ask them to provide the last 4 digits of their account number to proceed. "
                    "IMPORTANT: DO NOT list or reveal any account numbers or account masks."
                )
            
            # Generate LLM response with available tools
            response = await self.llm.generate_response(
                messages=conversation,
                tools=self._get_available_tools()
            )
            
            # Process any tool calls returned by the LLM
            if response.get("tool_calls"):
                tool_calls = response["tool_calls"]
                self.logger.info(f"LLM returned {len(tool_calls)} tool calls")
                
                # Process tool calls
                await self._process_tool_calls(session_id, tool_calls)
                
                # Add reminder to include all account information when authenticated
                if self.auth_manager.is_authenticated(session_id):
                    self.conversation_manager.add_system_message(
                        session_id,
                        "Remember to include ALL available account information in your response, "
                        "including balance, currency, account status, and last transaction date if available."
                    )
                # Add security guidance if not authenticated yet
                elif self.session_context.has_accounts(session_id):
                    if self.session_context.is_account_selected(session_id):
                        self.conversation_manager.add_system_message(
                            session_id,
                            "The user has selected an account. Ask for their 4-digit PIN to authenticate."
                        )
                    else:
                        self.conversation_manager.add_system_message(
                            session_id,
                            "The user has accounts, but hasn't selected one yet. Ask them to provide the "
                            "last 4 digits of their account number. DO NOT list or reveal any account numbers."
                        )
                
                # Get updated conversation and generate final response
                updated_conversation = self.conversation_manager.get_conversation(session_id)
                response = await self.llm.generate_response(messages=updated_conversation)
            
            # Process the final text response
            content = response.get("content", "")
            if not content:
                content = "I apologize, but I'm having trouble generating a response. Please try again."
            
            if self._contains_restricted_keywords(content):
                self.logger.info("Response contains restricted keywords, overriding")
                content = (
                    "I'm sorry, but I can only provide account balance information for standard deposit accounts. "
                    "For inquiries regarding other products, please contact our customer support team."
                )
            
            # Add assistant response to conversation
            self.conversation_manager.add_assistant_message(session_id, content)
            
            return {"response": content}
        
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": "I'm sorry, but I'm having trouble processing your request right now. Please try again later."
            }
    
    async def _auto_lookup_accounts(self, session_id: str, mobile_number: str) -> None:
        """Automatically look up accounts for a mobile number
        
        Args:
            session_id: The session identifier
            mobile_number: The mobile number to look up
        """
        self.logger.info(f"Auto-looking up accounts for mobile: {mobile_number}")
        
        # Get call ID from session context
        call_id = self.session_context.get_call_id(session_id)
        
        try:
            # Execute account lookup directly
            mobile_auth_service = self.registry.get_service("mobile_auth")
            if not mobile_auth_service:
                self.logger.error("Mobile auth service not found")
                return
                
            result = mobile_auth_service.execute_tool("get_accounts_by_mobile", {
                "mobile_number": mobile_number,
                "call_id": call_id,
                "session_id": session_id
            })
            
            self.logger.info(f"Auto account lookup result: {result['status']}")
            
            if result["status"] == "success" and result["accounts"]:
                # Store accounts in session context
                self.session_context.set_retrieved_accounts(session_id, result["accounts"])
                
                # IMPORTANT: Don't add the actual result to the conversation context
                # Instead, add a sanitized version that doesn't contain account numbers
                sanitized_result = {
                    "status": "success",
                    "message": f"Found accounts associated with the phone number",
                    "accounts_found": True
                }
                
                # Add synthetic tool call to conversation for context
                tool_call = {
                    "id": "auto_accounts_lookup",
                    "type": "function",
                    "function": {
                        "name": "get_accounts_by_mobile",
                        "arguments": json.dumps({"mobile_number": mobile_number})
                    }
                }
                
                self.conversation_manager.add_tool_call(session_id, tool_call)
                self.conversation_manager.add_tool_response(
                    session_id, 
                    "auto_accounts_lookup",
                    json.dumps(sanitized_result)
                )
                
                # Add a system message to guide the assistant
                accounts = result["accounts"]
                num_accounts = len(accounts)
                
                self.conversation_manager.add_system_message(
                    session_id,
                    f"The system has found {num_accounts} account(s) associated with the caller's phone number. "
                    "Ask the user to provide the last 4 digits of their account number to confirm which account they want to access. "
                    "IMPORTANT: Do not list or reveal any account numbers to the user. This is a security measure."
                )
                
                self.logger.info(f"Retrieved {num_accounts} accounts for caller {mobile_number}")
            else:
                self.logger.warning(f"No accounts found for mobile number: {mobile_number}")
                # Add system message for no accounts found
                self.conversation_manager.add_system_message(
                    session_id,
                    "No accounts were found associated with the caller's phone number. "
                    "Inform the user that no accounts were found for their phone number."
                )
            
        except Exception as e:
            self.logger.error(f"Error during auto account lookup: {e}")
    
    def _extract_last_4_digits(self, message: str) -> Optional[str]:
        """Extract last 4 digits of account number from message
        
        Args:
            message: The user message
            
        Returns:
            Last 4 digits or None if not found
        """
        # Patterns for common ways to express last 4 digits
        patterns = [
            r'\b(\d{4})\b',                     # Simple 4 digits
            r'last\s+four\s+digits?\s+(\d{4})',  # "last four digits 1234"
            r'ending\s+in\s+(\d{4})',           # "ending in 1234"
            r'ends?\s+with\s+(\d{4})',          # "ends with 1234"
            r'account\s+\w+\s+(\d{4})'          # "account XXXX 1234"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                self.logger.debug(f"Extracted last 4 digits: {match.group(1)} using pattern: {pattern}")
                return match.group(1)
        
        return None
    
    async def _match_account_by_last_digits(
        self, 
        session_id: str, 
        last_digits: str
    ) -> Optional[Dict[str, Any]]:
        """Match account by last 4 digits
        
        Args:
            session_id: The session identifier
            last_digits: Last 4 digits of account number
            
        Returns:
            Response dict if account found, None otherwise
        """
        accounts = self.session_context.get_retrieved_accounts(session_id)
        
        for account in accounts:
            account_number = account["account_number"]
            if account_number.endswith(last_digits):
                self.logger.info(f"Matched account {account_number} by last digits {last_digits}")
                
                # Store selected account - IMPORTANT: This sets the account_selected flag to true
                self.session_context.set_selected_account(session_id, account_number)
                
                # Add validation to conversation history
                masked_number = account["masked_account"]
                
                # Add system message to guide the assistant
                self.conversation_manager.add_system_message(
                    session_id,
                    f"User confirmed account {masked_number} by providing last 4 digits {last_digits}. "
                    f"Ask for their 4-digit PIN to authenticate."
                )
                
                response = f"Thank you for confirming your account {masked_number}. For security, please provide your 4-digit PIN."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
        
        # No match found
        self.logger.warning(f"No account found ending with digits: {last_digits}")
        response = "I'm sorry, but I couldn't find an account ending with those digits. Please check the number and try again."
        self.conversation_manager.add_assistant_message(session_id, response)
        return {"response": response}
    
    async def _handle_pin_validation(
        self, 
        session_id: str, 
        account_number: str, 
        pin: str
    ) -> Optional[Dict[str, Any]]:
        """Handle PIN validation and account details retrieval
        
        Args:
            session_id: The session identifier
            account_number: The account number
            pin: The PIN to validate
            
        Returns:
            Response dict if validation succeeds, None otherwise
        """
        self.logger.info(f"Validating PIN for account {account_number}")
        
        try:
            # Get caller ID and call ID from session context
            session_ctx = self.session_context.get_session_context(session_id)
            caller_id = session_ctx.get("caller_id")
            call_id = session_ctx.get("call_id")
            
            # Validate PIN
            auth_service = self.registry.get_service("authentication")
            if not auth_service:
                self.logger.error("Authentication service not found")
                return None
                
            # Execute PIN validation
            pin_result = auth_service.execute_tool("validate_pin", {
                "account_number": account_number,
                "pin": pin,
                "mobile_number": caller_id
            })
            
            self.logger.info(f"PIN validation result: {pin_result}")
            
            # Add synthetic tool call and response for PIN validation
            pin_tool_call = {
                "id": "pin_validation_call",
                "type": "function",
                "function": {
                    "name": "validate_pin",
                    "arguments": json.dumps({
                        "account_number": account_number, 
                        "pin": "****",  # Hide actual PIN in the conversation context
                        "mobile_number": caller_id
                    })
                }
            }
            
            # Create a sanitized version of the result that doesn't include account details
            sanitized_result = {
                "valid": pin_result.get("valid", False),
                "message": pin_result.get("message", "")
            }
            
            self.conversation_manager.add_tool_call(session_id, pin_tool_call)
            self.conversation_manager.add_tool_response(
                session_id,
                "pin_validation_call",
                json.dumps(sanitized_result)
            )
            
            # If PIN is valid, get account details
            if pin_result.get("valid", False):
                # Authenticate session
                self.auth_manager.authenticate_session(session_id, account_number)
                
                # Get account details
                account_service = self.registry.get_service("account")
                if not account_service:
                    self.logger.error("Account service not found")
                    return None
                    
                details_result = account_service.execute_tool("get_account_details", {
                    "account_number": account_number,
                    "pin": pin,
                    "mobile_number": caller_id
                })
                
                self.logger.info(f"Account details retrieved successfully: {details_result['status']}")
                
                # Add synthetic tool call and response for account details
                details_tool_call = {
                    "id": "get_account_details_call",
                    "type": "function",
                    "function": {
                        "name": "get_account_details",
                        "arguments": json.dumps({
                            "account_number": account_number, 
                            "pin": "****",  # Hide actual PIN
                            "mobile_number": caller_id
                        })
                    }
                }
                
                self.conversation_manager.add_tool_call(session_id, details_tool_call)
                self.conversation_manager.add_tool_response(
                    session_id,
                    "get_account_details_call",
                    json.dumps(details_result)
                )
                
                # Return formatted response with account details
                if details_result.get("status") == "success":
                    data = details_result["data"]
                    response = (
                        f"Thank you for providing your PIN. Here are your account details:\n\n"
                        f"- **Current Balance:** {data['formatted_balance']}\n"
                        f"- **Currency:** {data['currency']}\n"
                        f"- **Account Status:** {data['account_status']}\n"
                        f"- **Last Transaction Date:** {data['last_transaction']}"
                    )
                    
                    # Add assistant response to conversation
                    self.conversation_manager.add_assistant_message(session_id, response)
                    
                    return {"response": response}
            else:
                # Invalid PIN response
                response = "Sorry, the PIN you provided is incorrect. Please try again with the correct 4-digit PIN."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
                
        except Exception as e:
            self.logger.error(f"Error during PIN validation: {e}", exc_info=True)
            
        return None
    
    def _extract_pin(self, message: str) -> Optional[str]:
        """Extract a 4-digit PIN from the message
        
        Args:
            message: The user message
            
        Returns:
            Extracted PIN or None
        """
        # Look for 4-digit sequences
        pin_pattern = r'\b\d{4}\b'
        pin_match = re.search(pin_pattern, message)
        if pin_match:
            self.logger.debug(f"Extracted PIN: {pin_match.group(0)}")
            return pin_match.group(0)
        return None
    
    async def _process_tool_calls(self, session_id: str, tool_calls: List[Dict[str, Any]]) -> None:
        """Process tool calls
        
        Args:
            session_id: The session identifier
            tool_calls: List of tool calls to process
        """
        self.logger.info(f"Processing {len(tool_calls)} tool call(s)")
        
        # Get context info for API calls
        session_ctx = self.session_context.get_session_context(session_id)
        caller_id = session_ctx.get("caller_id")
        call_id = session_ctx.get("call_id")
        
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])
            
            # Create sanitized arguments for logging to conversation
            sanitized_args = function_args.copy()
            if "pin" in sanitized_args:
                sanitized_args["pin"] = "****"  # Hide PIN
            
            # Add additional context to args if needed
            if function_name == "get_accounts_by_mobile" and "call_id" not in function_args:
                function_args["call_id"] = call_id
                function_args["session_id"] = session_id
                sanitized_args["call_id"] = call_id
                sanitized_args["session_id"] = session_id
                
            # Add mobile_number to account-related functions when caller_id is available
            if caller_id and function_name in ["validate_account", "validate_pin", "get_account_details"]:
                function_args["mobile_number"] = caller_id
                sanitized_args["mobile_number"] = caller_id
                
            self.logger.info(f"Executing tool: {function_name} with args: {sanitized_args}")
            
            try:
                # Execute the tool with the real arguments
                result = self.registry.execute_tool(function_name, function_args)
                self.logger.debug(f"Tool execution result: {result}")
                
                # Create a sanitized tool call for the conversation
                sanitized_tool_call = tool_call.copy()
                sanitized_tool_call["function"] = sanitized_tool_call["function"].copy()
                sanitized_tool_call["function"]["arguments"] = json.dumps(sanitized_args)
                
                # Add sanitized tool call to conversation
                self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                
                # Sanitize result for get_accounts_by_mobile to avoid revealing account numbers
                if function_name == "get_accounts_by_mobile":
                    sanitized_result = {
                        "status": result["status"],
                        "message": result["message"],
                        "accounts_found": len(result.get("accounts", [])) > 0
                    }
                    self.conversation_manager.add_tool_response(
                        session_id,
                        tool_call.get("id", "unknown"),
                        json.dumps(sanitized_result)
                    )
                else:
                    # Add regular tool response for other functions
                    self.conversation_manager.add_tool_response(
                        session_id,
                        tool_call.get("id", "unknown"),
                        json.dumps(result)
                    )
                
                # Special handling for specific tools
                if function_name == "get_accounts_by_mobile" and result["status"] == "success":
                    self.logger.info(f"Storing {len(result['accounts'])} accounts from get_accounts_by_mobile")
                    self.session_context.set_retrieved_accounts(session_id, result["accounts"])
                    
                    # Add a system message to instruct not to show account numbers
                    num_accounts = len(result["accounts"])
                    self.conversation_manager.add_system_message(
                        session_id,
                        f"The system has found {num_accounts} account(s) associated with the caller's phone number. "
                        "Ask the user to provide the last 4 digits of their account number to confirm which account they want to access. "
                        "IMPORTANT: Do not list or reveal any account numbers to the user. This is a security measure."
                    )
                    # Important: account is not selected yet, waiting for last 4 digits
                
                elif function_name == "validate_account" and result.get("valid", False):
                    account_number = function_args.get("account_number")
                    self.logger.info(f"Account {account_number} validated, marking as selected and awaiting PIN")
                    # Mark account as selected and awaiting PIN
                    self.session_context.set_selected_account(session_id, account_number)
                
                elif function_name == "validate_pin" and result.get("valid", False):
                    account_number = function_args.get("account_number")
                    self.logger.info(f"PIN validated for account {account_number}, marking session as authenticated")
                    self.auth_manager.authenticate_session(session_id, account_number)
                
                elif function_name == "get_account_details" and result.get("status") == "success":
                    account_number = function_args.get("account_number")
                    self.logger.info(f"Got account details for {account_number}, marking session as authenticated")
                    self.auth_manager.authenticate_session(session_id, account_number)
                
            except ValueError as e:
                self.logger.error(f"Error executing tool: {e}")
                result = {"error": str(e)}
                
                # Add error response to conversation
                self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                self.conversation_manager.add_tool_response(
                    session_id,
                    tool_call.get("id", "unknown"),
                    json.dumps(result)
                )
                
            except KeyError as e:
                self.logger.error(f"Missing required parameter: {e}")
                result = {"error": f"Missing required parameter: {e}"}
                
                # Add error response to conversation
                self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                self.conversation_manager.add_tool_response(
                    session_id,
                    tool_call.get("id", "unknown"),
                    json.dumps(result)
                )
    
    async def _handle_field_query(self, session_id: str, account_number: str, message: str) -> Optional[str]:
        """Handle field-specific queries for authenticated users
        
        Args:
            session_id: The session identifier
            account_number: The authenticated account number
            message: User message content
            
        Returns:
            Response for field query or None if not a field query
        """
        message_lower = message.lower()
        
        # Extract field name from message
        field_name = None
        if "balance" in message_lower or "how much" in message_lower:
            field_name = "balance"
        elif "last transaction" in message_lower:
            field_name = "last_transaction"
        elif "status" in message_lower:
            field_name = "account_status"
        elif "currency" in message_lower:
            field_name = "currency"
        elif "account type" in message_lower or "type of account" in message_lower:
            field_name = "account_type"
        else:
            return None
        
        # Use a flow to handle the query
        context = {
            "account_number": account_number,
            "field_name": field_name
        }
        
        try:
            # Execute account query flow
            result = await self.flow_manager.execute_flow("account_query", context)
            
            # If flow is successful, process the result
            if "get_account_field" in result.get("executed_steps", []):
                field_result = result["flow_results"]["get_account_field"]["result"]
                
                if field_result.get("status") == "success":
                    value = field_result.get("value")
                    
                    if field_name == "balance":
                        return f"Your current balance is {value}."
                    elif field_name == "last_transaction":
                        return f"Your last transaction was on {value}."
                    elif field_name == "account_status":
                        return f"Your account status is '{value}'."
                    elif field_name == "currency":
                        # Check if we have currency details
                        if "get_currency_details" in result.get("executed_steps", []):
                            currency_result = result["flow_results"]["get_currency_details"]["result"]
                            currency_name = currency_result.get("name", value)
                            return f"Your account is denominated in {currency_name} ({value})."
                        return f"Your account currency is {value}."
                    elif field_name == "account_type":
                        # Check if we have account type details
                        if "get_account_type_details" in result.get("executed_steps", []):
                            type_result = result["flow_results"]["get_account_type_details"]["result"]
                            type_name = type_result.get("name", value.capitalize())
                            return f"You have a {type_name} ({value})."
                        return f"Your account type is {value}."
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error handling field query: {e}", exc_info=True)
            return None
    
    def _contains_restricted_keywords(self, text: str) -> bool:
        """Check if text contains restricted keywords using word boundary matching
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains restricted keywords
        """
        from .keyword_utils import contains_restricted_keywords
        return contains_restricted_keywords(text, self.restricted_keywords)

    async def inject_prompt(self, session_id: str, prompt: str) -> bool:
        """Inject a custom prompt into a session
        
        Args:
            session_id: The session identifier
            prompt: Prompt to inject
            
        Returns:
            True if prompt was injected
        """
        self.conversation_manager.add_system_message(session_id, prompt)
        self.logger.info(f"Injected new prompt into session {session_id}")
        return True
    
    async def end_session(self, session_id: str) -> bool:
        """End a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session was successfully ended
        """
        self.logger.info(f"Ending session {session_id}")
        conversation_ended = self.conversation_manager.end_conversation(session_id)
        auth_ended = self.auth_manager.end_session(session_id)
        context_ended = self.session_context.end_session(session_id)
        return conversation_ended or auth_ended or context_ended
