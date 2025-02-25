# File: banking-assistant/config/prompts/prompt_manager.py
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

class PromptManager:
    """Manages domain-specific prompts for the chatbot"""
    
    def __init__(self, config_dir: str = "config/prompts"):
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger("banking_assistant.prompts")
        self.domain_prompts: Dict[str, str] = {}
        self._load_domain_prompts()
    
    def _load_domain_prompts(self) -> None:
        """Load all domain prompts from the config directory"""
        self.logger.info(f"Loading domain prompts from {self.config_dir}")
        
        if not self.config_dir.exists():
            self.logger.warning(f"Config directory not found: {self.config_dir}")
            return
        
        for file_path in self.config_dir.glob("*.json"):
            if file_path.stem == "__init__":
                continue
                
            domain = file_path.stem.split("_")[0]  # Extract domain from filename
            try:
                with open(file_path, "r") as f:
                    config = json.load(f)
                    
                    # Try to get prompt from "content" field first, then fall back to "system_prompt"
                    prompt = config.get("content", config.get("system_prompt", ""))
                    
                    if prompt:
                        self.domain_prompts[domain] = prompt
                        self.logger.info(f"Loaded prompt for domain: {domain}")
                    else:
                        self.logger.warning(f"No prompt content found in {file_path}")
            except Exception as e:
                self.logger.error(f"Error loading prompt from {file_path}: {e}")
    
    def get_domain_prompt(self, domain: str) -> Optional[str]:
        """Get the prompt for a specific domain
        
        Args:
            domain: The domain identifier
            
        Returns:
            The domain-specific prompt or None if not found
        """
        prompt = self.domain_prompts.get(domain)
        if not prompt:
            self.logger.warning(f"No prompt found for domain: {domain}")
        return prompt
    
    def compose_prompt(self, domains: List[str]) -> str:
        """Compose a system prompt from multiple domains
        
        Args:
            domains: List of domain identifiers
            
        Returns:
            Combined prompt from all specified domains or default fallback prompt
        """
        prompts = []
        
        for domain in domains:
            domain_prompt = self.get_domain_prompt(domain)
            if domain_prompt:
                prompts.append(domain_prompt)
        
        if not prompts:
            self.logger.warning("No domain prompts found, using fallback prompt")
            return self._get_fallback_prompt()
        
        combined = "\n\n".join(prompts)
        self.logger.info(f"Composed prompt from domains: {', '.join(domains)}")
        return combined
    
    def _get_fallback_prompt(self) -> str:
        """Get a fallback prompt to use when no domain prompts are available
        
        Returns:
            Default fallback prompt
        """
        return (
            "You are a banking assistant that helps users check their account balance information.\n"
            "Follow a strict flow:\n"
            "1. Ask for account number first\n"
            "2. Immediately validate that the account number exists before asking for the PIN\n"
          "3. Only after validating the account number, ask for the PIN\n"
          "4. Then provide detailed account balance information including current balance, currency, account status, and last transaction date.\n\n"
          "IMPORTANT: Always validate account number existence using the validate_account tool before asking for the PIN.\n"
          "IMPORTANT: If an account number is not found, immediately inform the user and ask for a valid account number.\n"
          "IMPORTANT: Always provide ALL information that is available in the account details, including last transaction date.\n\n"
          "Be professional and friendly. Remember: your focus is on providing complete and accurate account information for standard deposit accounts."
      )