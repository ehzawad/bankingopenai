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
from ..utils.text_extraction import extract_pin, extract_last_4_digits, contains_restricted_keywords
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
            if contains_restricted_keywords(message, self.restricted_keywords):
                self.logger.info(f"Message contains restricted keywords: {message}")
                return {
                    "response": (
                        "I'm sorry, but I can only provide account balance information for standard deposit accounts. "
                        "For inquiries regarding other products like loans, credit cards, or investments, "
                        "please contact our customer support team."
                    )
                }
            
            # <<< AUTOMATIC ACCOUNT LOOKUP BLOCK REMOVED >>>
            # We no longer auto lookup accounts based solely on caller_id.
            
            # If already authenticated, try handling field-specific queries
            if self.auth_manager.is_authenticated(session_id):
                account_number = self.auth_manager.get_authenticated_account(session_id)
                self.logger.info(f"User is already authenticated for account: {account_number}")
                field_response = await self._handle_field_query(session_id, account_number, message)
                if field_response:
                    return {"response": field_response}
            
            # If user is asking about account balance, just ask for last 4 digits
            if "account balance" in message.lower() or "balance" in message.lower():
                response = "To assist you with your account balance, I'll need to verify your account. Please provide the last 4 digits of your account number."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
            
            response = await self._process_authentication_state(session_id, message)
            if response:
                return response
            
            # Add user message to conversation
            self.conversation_manager.add_user_message(session_id, message)
            
            # Get current conversation state
            conversation = self.conversation_manager.get_conversation(session_id)
            
            # Add contextual guidance for the assistant based on session state
            self._add_contextual_guidance(session_id)
            
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
                
                # Add security guidance based on authentication state
                self._add_security_guidance(session_id)
                
                # Get updated conversation and generate final response
                updated_conversation = self.conversation_manager.get_conversation(session_id)
                response = await self.llm.generate_response(messages=updated_conversation)
            
            # Process the final text response
            content = response.get("content", "")
            if not content:
                content = "I apologize, but I'm having trouble generating a response. Please try again."
            
            if contains_restricted_keywords(content, self.restricted_keywords):
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
    
    async def _process_authentication_state(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Process authentication state based on the message content
        
        Args:
            session_id: The session identifier
            message: User message content
            
        Returns:
            Response dictionary if authentication state changes, None otherwise
        """
        # IMPORTANT: Check for awaiting PIN state FIRST - this prevents PIN from being interpreted as account digits
        if (self.session_context.is_account_selected(session_id) and 
            self.session_context.is_awaiting_pin(session_id) and 
            not self.auth_manager.is_authenticated(session_id)):
            
            # PIN state has higher priority when we've already selected an account
            # Assume any 4-digit number here is a PIN
            if message.strip().isdigit() and len(message.strip()) == 4:
                pin = message.strip()
                self.logger.info(f"Detected PIN in message: {pin} (simple 4-digit message)")
            else:
                # Try to extract PIN using other methods
                pin = extract_pin(message)
                
            if pin:
                # Get the selected account
                account_number = self.session_context.get_selected_account(session_id)
                self.logger.info(f"Handling PIN: '{pin}' for account: {account_number}")
                self.logger.debug(f"Account number type: {type(account_number)}, length: {len(account_number) if account_number else 0}")
                
                if not account_number:
                    self.logger.error("No account selected but awaiting PIN")
                    response = "There was an error with your session. Please start over with your account number."
                    self.conversation_manager.add_assistant_message(session_id, response)
                    return {"response": response}
                    
                # Validate PIN
                self.logger.info(f"Validating PIN: '{pin}' for account: {account_number}")
                pin_response = await self._handle_pin_validation(session_id, account_number, pin)
                if pin_response:
                    self.logger.info(f"PIN validation successful")
                    return pin_response
                
                # If we didn't return above, the PIN validation failed
                self.logger.warning(f"PIN validation failed or response not handled for account {account_number} with PIN {pin}")
                pin_check_str = await self._simple_pin_check(session_id, account_number, pin)
                response = pin_check_str or "The PIN you entered is incorrect. Please try again with the correct 4-digit PIN."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
                
            # No PIN found in message
            response = "I need your 4-digit PIN to authenticate your account. Please enter only your PIN."
            self.conversation_manager.add_assistant_message(session_id, response)
            return {"response": response}
            
        # STEP 1: Not awaiting PIN, so extract last 4 digits from message
        last_4_digits = extract_last_4_digits(message)
        if last_4_digits:
            self.logger.info(f"STEP 1: Detected last 4 digits of account: {last_4_digits}")
            
            # Get caller ID for account lookup
            caller_id = self.session_context.get_caller_id(session_id)
            if not caller_id:
                self.logger.warning("No caller ID available for account lookup")
                response = "I need your mobile number to proceed. Please contact customer support."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
                
            # STEP 2: Retrieve accounts for this caller to check against
            self.logger.info(f"Retrieving accounts for caller: {caller_id}")
            try:
                mobile_auth_service = self.registry.get_service("mobile_auth")
                if not mobile_auth_service:
                    self.logger.error("Mobile auth service not available")
                    response = "Sorry, the account verification service is currently unavailable."
                    self.conversation_manager.add_assistant_message(session_id, response)
                    return {"response": response}
                    
                result = mobile_auth_service.execute_tool("get_accounts_by_mobile", {
                    "mobile_number": caller_id,
                    "call_id": self.session_context.get_call_id(session_id)
                })
                
                if not result.get("status") == "success" or not result.get("accounts"):
                    self.logger.warning(f"No accounts found for caller {caller_id}")
                    response = "I'm sorry, but I couldn't find any accounts associated with your phone number."
                    self.conversation_manager.add_assistant_message(session_id, response)
                    return {"response": response}
                    
                # STEP 3: Update session with retrieved accounts
                accounts = result["accounts"]
                self.logger.info(f"Found {len(accounts)} accounts for {caller_id}")
                self.session_context.set_retrieved_accounts(session_id, accounts)
                
                # STEP 4: Match the last 4 digits against retrieved accounts
                match_found = False
                for account in accounts:
                    if account["account_number"].endswith(last_4_digits):
                        match_found = True
                        account_number = account["account_number"]
                        masked_account = account["masked_account"]
                        self.logger.info(f"Matched account {account_number} with last 4 digits {last_4_digits}")
                        
                        # STEP 5: Set selected account and ask for PIN
                        self.session_context.set_selected_account(session_id, account_number)
                        self.logger.info(f"Set selected account {account_number} for session {session_id}")
                        
                        # Add system instruction
                        self.conversation_manager.add_system_message(
                            session_id,
                            f"User confirmed account {masked_account}. Now ask for 4-digit PIN to authenticate."
                        )
                        
                        # Ask user for PIN
                        response = f"Thank you for confirming your account {masked_account}. For security, please provide your 4-digit PIN."
                        self.conversation_manager.add_assistant_message(session_id, response)
                        return {"response": response}
                
                # No matching account found
                if not match_found:
                    self.logger.warning(f"No account found with last 4 digits: {last_4_digits}")
                    response = f"I'm sorry, but I couldn't find an account ending with {last_4_digits} for this phone number. Please check and try again."
                    self.conversation_manager.add_assistant_message(session_id, response)
                    return {"response": response}
                
            except Exception as e:
                self.logger.error(f"Error during account lookup: {e}", exc_info=True)
                response = "Sorry, I'm having trouble retrieving your account information. Please try again later."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
    
    def _add_contextual_guidance(self, session_id: str) -> None:
        """Add contextual guidance for the assistant based on session state
        
        Args:
            session_id: The session identifier
        """
        if self.session_context.has_accounts(session_id) and not self.session_context.is_account_selected(session_id):
            self.conversation_manager.add_system_message(
                session_id,
                "The user has accounts associated with their phone number. "
                "Ask them to provide the last 4 digits of their account number to proceed. "
                "IMPORTANT: DO NOT list or reveal any account numbers or account masks."
            )
    
    def _add_security_guidance(self, session_id: str) -> None:
        """Add security guidance based on authentication state
        
        Args:
            session_id: The session identifier
        """
        if self.auth_manager.is_authenticated(session_id):
            self.conversation_manager.add_system_message(
                session_id,
                "Remember to include ALL available account information in your response, "
                "including balance, currency, account status, and last transaction date if available."
            )
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
        caller_id = self.session_context.get_caller_id(session_id)
        self.logger.info(f"Matching last 4 digits {last_digits} for caller {caller_id} with {len(accounts)} accounts")
        
        # Check if the provided last digits match any account in the system
        valid_account = False
        for account in accounts:
            if account["account_number"].endswith(last_digits):
                valid_account = True
                break
                
        if not valid_account:
            self.logger.warning(f"No account found ending with digits: {last_digits}")
            response = f"I'm sorry, but I couldn't find an account ending with {last_digits} for this mobile number. Please check the number and try again."
            self.conversation_manager.add_assistant_message(session_id, response)
            return {"response": response}
        
        # Log all available accounts for debugging
        for account in accounts:
            self.logger.info(f"Available account: {account['account_number']} ends with {account['account_number'][-4:]}")
        
        found_match = False
        for account in accounts:
            account_number = account["account_number"]
            if account_number.endswith(last_digits):
                found_match = True
                self.logger.info(f"Matched account {account_number} by last digits {last_digits}")
                
                # If validation succeeded, continue with the flow
                self.session_context.set_selected_account(session_id, account_number)
                stored_account = self.session_context.get_selected_account(session_id)
                self.logger.info(f"CRITICAL DEBUG: Stored full account number: {stored_account}")
                masked_number = account["masked_account"]
                self.conversation_manager.add_system_message(
                    session_id,
                    f"User confirmed account {masked_number} by providing last 4 digits {last_digits}. "
                    "Ask for their 4-digit PIN to authenticate."
                )
                response = f"Thank you for confirming your account {masked_number}. For security, please provide your 4-digit PIN."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
        
        if not found_match:
            # Get the correct last 4 digits of available accounts
            available_last_digits = [account["account_number"][-4:] for account in accounts]
            self.logger.warning(f"No account found ending with digits: {last_digits}. Available last digits: {available_last_digits}")
            
            response = f"I'm sorry, but I couldn't find an account ending with {last_digits} for this mobile number. Please check the number and try again."
            self.conversation_manager.add_assistant_message(session_id, response)
            return {"response": response}
    
    async def _simple_pin_check(self, session_id: str, account_number: str, pin: str) -> Optional[str]:
        """Simple PIN check for debugging purposes
        
        Args:
            session_id: Session ID
            account_number: Account number
            pin: PIN to check
            
        Returns:
            Debug message if available
        """
        accounts = self.session_context.get_retrieved_accounts(session_id)
        for account in accounts:
            if account["account_number"] == account_number:
                self.logger.info(f"Found account {account_number} with PIN {account.get('pin', 'unknown')}")
                expected_pin = account.get("pin")
                if expected_pin == pin:
                    return f"DEBUG: PIN should be valid! Expected: {expected_pin}, got: {pin}"
                else:
                    return f"DEBUG: PIN incorrect. Expected: {expected_pin}, got: {pin}"
        return None
        
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
        if not account_number or len(account_number) < 10:
            self.logger.error(f"Invalid account number format for PIN validation: {account_number}")
            response = "I'm sorry, but there was an issue with your account identification. Please try again by providing the last 4 digits of your account."
            self.conversation_manager.add_assistant_message(session_id, response)
            self.session_context.update_session_context(session_id, {
                "account_selected": False,
                "selected_account": None,
                "awaiting_pin": False
            })
            return {"response": response}
        
        self.logger.info(f"Validating PIN for account {account_number}")
        try:
            session_ctx = self.session_context.get_session_context(session_id)
            caller_id = session_ctx.get("caller_id")
            auth_service = self.registry.get_service("authentication")
            if not auth_service:
                self.logger.error("Authentication service not found")
                return None
            pin_result = auth_service.execute_tool("validate_pin", {
                "account_number": account_number,
                "pin": pin,
                "mobile_number": caller_id
            })
            self.logger.info(f"PIN validation result: {pin_result}")
            is_valid = pin_result.get("valid", False)
            self.logger.info(f"PIN validation success: {is_valid}")
            
            pin_tool_call = {
                "id": "pin_validation_call",
                "type": "function",
                "function": {
                    "name": "validate_pin",
                    "arguments": json.dumps({
                        "account_number": account_number, 
                        "pin": "****",
                        "mobile_number": caller_id
                    })
                }
            }
            sanitized_result = {
                "valid": is_valid,
                "message": pin_result.get("message", "")
            }
            self.conversation_manager.add_tool_call(session_id, pin_tool_call)
            self.conversation_manager.add_tool_response(
                session_id,
                "pin_validation_call",
                json.dumps(sanitized_result)
            )
            if pin_result.get("valid", False):
                self.auth_manager.authenticate_session(session_id, account_number)
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
                details_tool_call = {
                    "id": "get_account_details_call",
                    "type": "function",
                    "function": {
                        "name": "get_account_details",
                        "arguments": json.dumps({
                            "account_number": account_number, 
                            "pin": "****",
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
                if details_result.get("status") == "success":
                    data = details_result["data"]
                    response = (
                        f"Thank you for providing your PIN. Here are your account details:\n\n"
                        f"- **Current Balance:** {data['formatted_balance']}\n"
                        f"- **Currency:** {data['currency']}\n"
                        f"- **Account Status:** {data['account_status']}\n"
                        f"- **Last Transaction Date:** {data['last_transaction']}"
                    )
                    self.conversation_manager.add_assistant_message(session_id, response)
                    return {"response": response}
            else:
                response = "Sorry, the PIN you provided is incorrect. Please try again with the correct 4-digit PIN."
                self.conversation_manager.add_assistant_message(session_id, response)
                return {"response": response}
                    
        except Exception as e:
            self.logger.error(f"Error during PIN validation: {e}", exc_info=True)
        return None
    
    async def _process_tool_calls(self, session_id: str, tool_calls: List[Dict[str, Any]]) -> None:
        """Process tool calls
        
        Args:
            session_id: The session identifier
            tool_calls: List of tool calls to process
        """
        self.logger.info(f"Processing {len(tool_calls)} tool call(s)")
        session_ctx = self.session_context.get_session_context(session_id)
        caller_id = session_ctx.get("caller_id")
        call_id = session_ctx.get("call_id")
        
        # First process validate_account calls if present
        account_validation_result = None
        account_validation_tool_id = None
        
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            if function_name == "validate_account":
                function_args = json.loads(tool_call["function"]["arguments"])
                sanitized_args = function_args.copy()
                if caller_id:
                    function_args["mobile_number"] = caller_id
                    sanitized_args["mobile_number"] = caller_id
                
                self.logger.info(f"Executing account validation first: {function_name} with args: {sanitized_args}")
                
                try:
                    result = self.registry.execute_tool(function_name, function_args)
                    self.logger.debug(f"Account validation result: {result}")
                    sanitized_tool_call = tool_call.copy()
                    sanitized_tool_call["function"] = sanitized_tool_call["function"].copy()
                    sanitized_tool_call["function"]["arguments"] = json.dumps(sanitized_args)
                    self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                    
                    # Store the validation result
                    account_validation_result = result
                    account_validation_tool_id = tool_call.get("id", "unknown")
                    
                    # Add the tool response
                    self.conversation_manager.add_tool_response(
                        session_id,
                        account_validation_tool_id,
                        json.dumps(result)
                    )
                    
                    # Process the account validation result
                    if not result.get("valid", False):
                        self.logger.warning(f"Account validation failed: {result.get('message')}")
                        
                        # Add a message to inform user about invalid account
                        last_digits = function_args.get("account_number")
                        if len(last_digits) <= 4:
                            response = f"I'm sorry, but I couldn't find an account ending with {last_digits} associated with your phone number. Please check the last 4 digits of your account number and try again."
                            self.conversation_manager.add_assistant_message(session_id, response)
                            
                            # Skip processing remaining tool calls
                            return
                except Exception as e:
                    self.logger.error(f"Error during account validation: {e}")
                    result = {"error": str(e), "valid": False}
                    self.conversation_manager.add_tool_response(
                        session_id,
                        tool_call.get("id", "unknown"),
                        json.dumps(result)
                    )
                
                # Don't process this tool call again in the main loop
                break
        
        # Now process the remaining tool calls
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            # Skip the validate_account call we already processed
            if function_name == "validate_account" and tool_call.get("id") == account_validation_tool_id:
                continue
                
            # Skip validate_pin if account validation failed
            if function_name == "validate_pin" and account_validation_result and not account_validation_result.get("valid", False):
                self.logger.info(f"Skipping PIN validation because account validation failed")
                continue
                
            function_args = json.loads(tool_call["function"]["arguments"])
            sanitized_args = function_args.copy()
            if "pin" in sanitized_args:
                sanitized_args["pin"] = "****"
            if function_name == "get_accounts_by_mobile" and "call_id" not in function_args:
                function_args["call_id"] = call_id
                function_args["session_id"] = session_id
                sanitized_args["call_id"] = call_id
                sanitized_args["session_id"] = session_id
            if caller_id and function_name in ["validate_account", "validate_pin", "get_account_details"]:
                function_args["mobile_number"] = caller_id
                sanitized_args["mobile_number"] = caller_id
                
            self.logger.info(f"Executing tool: {function_name} with args: {sanitized_args}")
            
            try:
                result = self.registry.execute_tool(function_name, function_args)
                self.logger.debug(f"Tool execution result: {result}")
                sanitized_tool_call = tool_call.copy()
                sanitized_tool_call["function"] = sanitized_tool_call["function"].copy()
                sanitized_tool_call["function"]["arguments"] = json.dumps(sanitized_args)
                self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                await self._process_tool_result(
                    session_id, 
                    function_name, 
                    function_args, 
                    result, 
                    tool_call.get("id", "unknown")
                )
            except ValueError as e:
                self.logger.error(f"Error executing tool: {e}")
                result = {"error": str(e)}
                self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                self.conversation_manager.add_tool_response(
                    session_id,
                    tool_call.get("id", "unknown"),
                    json.dumps(result)
                )
            except KeyError as e:
                self.logger.error(f"Missing required parameter: {e}")
                result = {"error": f"Missing required parameter: {e}"}
                self.conversation_manager.add_tool_call(session_id, sanitized_tool_call)
                self.conversation_manager.add_tool_response(
                    session_id,
                    tool_call.get("id", "unknown"),
                    json.dumps(result)
                )



    async def _process_tool_result(
        self, 
        session_id: str, 
        function_name: str, 
        function_args: Dict[str, Any],
        result: Dict[str, Any],
        tool_call_id: str
    ) -> None:
        """Process tool execution result and update session state
        
        Args:
            session_id: The session identifier
            function_name: The name of the executed tool
            function_args: The arguments passed to the tool
            result: The tool execution result
            tool_call_id: The ID of the tool call
        """
        # Sanitize result for get_accounts_by_mobile to avoid revealing account numbers
        if function_name == "get_accounts_by_mobile":
            sanitized_result = {
                "status": result["status"],
                "message": result["message"],
                "accounts_found": len(result.get("accounts", [])) > 0
            }
            self.conversation_manager.add_tool_response(
                session_id,
                tool_call_id,
                json.dumps(sanitized_result)
            )
            
            # Update session state if accounts were found
            if result["status"] == "success":
                self.logger.info(f"Storing {len(result['accounts'])} accounts from get_accounts_by_mobile")
                
                # Log the actual account numbers being stored for debugging
                for account in result["accounts"]:
                    self.logger.info(f"Found account: {account['account_number']} (masked: {account['masked_account']})")
                    
                self.session_context.set_retrieved_accounts(session_id, result["accounts"])
                
                # Add a system message to instruct not to show account numbers
                num_accounts = len(result["accounts"])
                self.conversation_manager.add_system_message(
                    session_id,
                    f"The system has found {num_accounts} account(s) associated with the caller's phone number. "
                    "Ask the user to provide the last 4 digits of their account number to confirm which account they want to access. "
                    "IMPORTANT: Do not list or reveal any account numbers to the user. This is a security measure."
                )
        else:
            # Add regular tool response for other functions
            self.conversation_manager.add_tool_response(
                session_id,
                tool_call_id,
                json.dumps(result)
            )
            
            # Update session state based on tool result
            if function_name == "validate_account" and result.get("valid", False):
                # CRITICAL FIX: For validate_account, try to extract the full account number
                # from the API response if available
                short_account_number = function_args.get("account_number")
                
                # Check if this is a short account number
                if len(short_account_number) <= 4:
                    # Get the mobile number from session
                    session_ctx = self.session_context.get_session_context(session_id)
                    mobile_number = session_ctx.get("caller_id")
                    
                    # Try to find the full account number
                    full_account_number = None
                    
                    # First check if we have accounts in the session
                    if self.session_context.has_accounts(session_id):
                        accounts = self.session_context.get_retrieved_accounts(session_id)
                        for account in accounts:
                            if account["account_number"].endswith(short_account_number):
                                full_account_number = account["account_number"]
                                self.logger.info(f"Using full account number {full_account_number} found in session")
                                break
                    
                    # If we still don't have a full account number, try to get accounts by mobile
                    if not full_account_number and mobile_number:
                        try:
                            # Get the mobile auth service
                            mobile_auth_service = self.registry.get_service("mobile_auth")
                            if mobile_auth_service:
                                # Get accounts by mobile
                                accounts_result = mobile_auth_service.execute_tool("get_accounts_by_mobile", {
                                    "mobile_number": mobile_number
                                })
                                
                                if accounts_result["status"] == "success":
                                    for account in accounts_result["accounts"]:
                                        if account["account_number"].endswith(short_account_number):
                                            full_account_number = account["account_number"]
                                            self.logger.info(f"Using full account number {full_account_number} from mobile lookup")
                                            break
                        except Exception as e:
                            self.logger.error(f"Error trying to find full account number: {e}")
                    
                    # Use the full account number if we found one
                    if full_account_number:
                        account_number = full_account_number
                        self.logger.info(f"Setting full account number: {account_number} instead of short: {short_account_number}")
                    else:
                        self.logger.warning(f"Could not find full account number for {short_account_number}")
                        account_number = short_account_number
                else:
                    # We already have a full account number
                    account_number = short_account_number
                    
                # Now set the selected account
                self.logger.info(f"Account {account_number} validated, marking as selected and awaiting PIN")
                
                # Try to set the selected account, handle validation errors
                try:
                    # Mark account as selected and awaiting PIN
                    self.session_context.set_selected_account(session_id, account_number)
                except ValueError as e:
                    self.logger.error(f"Error setting selected account: {e}")
                    # Add guidance for the assistant
                    self.conversation_manager.add_system_message(
                        session_id,
                        "There was an error with the account number validation. Ask the user to try again with the correct account number."
                    )
            

# This is a patch to fix the last issue in the _process_tool_result method

            elif function_name == "validate_pin" and result.get("valid", False):
                account_number = function_args.get("account_number")
                
                # FINAL FIX: Check if this is a short account number
                if len(account_number) <= 4:
                    # Get the mobile number from session
                    session_ctx = self.session_context.get_session_context(session_id)
                    mobile_number = session_ctx.get("caller_id")
                    
                    # Try to find the full account number
                    full_account_number = None
                    
                    # First check if we have an already selected account in the session
                    selected_account = self.session_context.get_selected_account(session_id)
                    if selected_account and len(selected_account) > 4:
                        full_account_number = selected_account
                        self.logger.info(f"Using previously selected full account number: {full_account_number}")
                        
                    # If not found, check accounts in the session
                    if not full_account_number and self.session_context.has_accounts(session_id):
                        accounts = self.session_context.get_retrieved_accounts(session_id)
                        for account in accounts:
                            if account["account_number"].endswith(account_number):
                                full_account_number = account["account_number"]
                                self.logger.info(f"Using full account number {full_account_number} found in session")
                                break
                                
                    # Use the full account number if we found one
                    if full_account_number:
                        account_number = full_account_number
                        self.logger.info(f"Using full account number: {account_number} for authentication")
                
                self.logger.info(f"PIN validated for account {account_number}, marking session as authenticated")
                self.auth_manager.authenticate_session(session_id, account_number)
            
                # account_number = function_args.get("account_number")
                # self.logger.info(f"PIN validated for account {account_number}, marking session as authenticated")
                # self.auth_manager.authenticate_session(session_id, account_number)
            
            elif function_name == "get_account_details" and result.get("status") == "success":
                account_number = function_args.get("account_number")
                self.logger.info(f"Got account details for {account_number}, marking session as authenticated")
                self.auth_manager.authenticate_session(session_id, account_number)
        
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
        
        context = {
            "account_number": account_number,
            "field_name": field_name
        }
        
        try:
            result = await self.flow_manager.execute_flow("account_query", context)
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
                        if "get_currency_details" in result.get("executed_steps", []):
                            currency_result = result["flow_results"]["get_currency_details"]["result"]
                            currency_name = currency_result.get("name", value)
                            return f"Your account is denominated in {currency_name} ({value})."
                        return f"Your account currency is {value}."
                    elif field_name == "account_type":
                        if "get_account_type_details" in result.get("executed_steps", []):
                            type_result = result["flow_results"]["get_account_type_details"]["result"]
                            type_name = type_result.get("name", value.capitalize())
                            return f"You have a {type_name} ({value})."
                        return f"Your account type is {value}."
            return None
        except Exception as e:
            self.logger.error(f"Error handling field query: {e}", exc_info=True)
            return None

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
