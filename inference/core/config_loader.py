"""Configuration loader for the inference workflow."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv


class ConfigLoader:
    """Loads and validates configuration from YAML and environment variables."""
    
    def __init__(
        self, 
        config_path: Optional[str] = None,
        env_path: Optional[str] = None
    ):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to config.yaml. Defaults to inference/config.yaml.
            env_path: Path to .env.local. Defaults to project root .env.local.
        """
        # Resolve paths relative to inference package
        inference_dir = Path(__file__).parent.parent
        project_root = inference_dir.parent
        
        self.config_path = Path(config_path) if config_path else inference_dir / "config.yaml"
        self.env_path = Path(env_path) if env_path else project_root / ".env.local"
        
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from files and environment.
        
        Returns:
            Merged configuration dictionary.
        """
        # Load environment variables first
        if self.env_path.exists():
            load_dotenv(self.env_path)
        
        # Load YAML configuration
        if self.config_path.exists():
            with open(self.config_path) as f:
                self._config = yaml.safe_load(f) or {}
        
        # Validate required sections
        self._validate()
        
        # Merge with environment overrides
        self._apply_env_overrides()
        
        self._loaded = True
        return self._config
    
    def _validate(self) -> None:
        """Validate that required configuration sections exist."""
        # These sections have defaults, so we just ensure the structure
        if "routing" not in self._config:
            self._config["routing"] = {"tiers": {}}
        if "chunking" not in self._config:
            self._config["chunking"] = {}
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Classifier settings from environment
        self._config.setdefault("classifier", {})
        
        if os.getenv("CLASSIFIER_ENDPOINT"):
            self._config["classifier"]["endpoint"] = os.getenv("CLASSIFIER_ENDPOINT")
        if os.getenv("CLASSIFIER_MODEL"):
            self._config["classifier"]["model"] = os.getenv("CLASSIFIER_MODEL")
        if os.getenv("CLASSIFIER_TEMPERATURE"):
            self._config["classifier"]["temperature"] = float(os.getenv("CLASSIFIER_TEMPERATURE"))
        
        # Chunking settings from environment
        if os.getenv("CHUNKING_STRATEGY"):
            self._config["chunking"]["strategy"] = os.getenv("CHUNKING_STRATEGY")
        if os.getenv("CHUNKING_MAX_SIZE"):
            self._config["chunking"]["max_chunk_size"] = int(os.getenv("CHUNKING_MAX_SIZE"))
        if os.getenv("CHUNKING_OVERLAP"):
            self._config["chunking"]["overlap"] = int(os.getenv("CHUNKING_OVERLAP"))
        if os.getenv("CHUNKING_THRESHOLD"):
            self._config["chunking"]["threshold_tokens"] = int(os.getenv("CHUNKING_THRESHOLD"))
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Dot-separated key path (e.g., 'classifier.endpoint').
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        if not self._loaded:
            self.load()
        
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name (e.g., 'classifier', 'routing').
            
        Returns:
            Section configuration dictionary.
        """
        if not self._loaded:
            self.load()
        return self._config.get(section, {})
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        if not self._loaded:
            self.load()
        return self._config
