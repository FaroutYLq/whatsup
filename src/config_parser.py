"""
Configuration parser for loading and validating YAML config
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List


class ConfigParser:
    """Parse and validate the configuration file."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the config parser.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}"
            )
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _validate_config(self) -> None:
        """Validate the required configuration fields."""
        required_sections = [
            'email', 'arxiv', 'anthropic', 'zotero', 'interests'
        ]
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(
                    f"Missing required section: {section}"
                )
        
        # Validate email section
        email_fields = [
            'smtp_server', 'smtp_port', 
            'from_email', 'password', 'to_email'
        ]
        for field in email_fields:
            if field not in self.config['email']:
                raise ValueError(
                    f"Missing email field: {field}"
                )
        
        # Validate arxiv section
        if 'categories' not in self.config['arxiv']:
            raise ValueError(
                "Missing arxiv.categories"
            )
        
        # Validate Anthropic section
        if 'api_key' not in self.config['anthropic']:
            raise ValueError(
                "Missing anthropic.api_key"
            )
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration."""
        return self.config['email']
    
    def get_arxiv_config(self) -> Dict[str, Any]:
        """Get arxiv configuration."""
        return self.config['arxiv']
    
    def get_anthropic_config(self) -> Dict[str, Any]:
        """Get Anthropic configuration."""
        return self.config['anthropic']
    
    def get_zotero_config(self) -> Dict[str, Any]:
        """Get Zotero configuration."""
        return self.config['zotero']
    
    def get_interests(self) -> Dict[str, Any]:
        """Get user interests."""
        return self.config['interests']

