"""
Configuration Loader

Loads and validates configuration from YAML file.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from src.models import (
    AIProviderConfig,
    MQMConfig,
    QualityThresholds,
    ErrorCategory,
    ErrorSeverity,
)


class ConfigLoader:
    """
    Loads and parses configuration from YAML file.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize config loader.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        self.load()

    def load(self):
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.yaml.example to config.yaml and configure it."
            )

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {self.config_path}")

    def get_memoq_config(self) -> Dict[str, Any]:
        """Get MemoQ configuration."""
        return self.config.get("memoq", {})

    def get_ai_provider_config(self) -> AIProviderConfig:
        """Get AI provider configuration."""
        aiqe_config = self.config.get("aiqe", {})

        return AIProviderConfig(
            provider=aiqe_config.get("ai_provider", "anthropic"),
            api_key=aiqe_config.get("api_key", ""),
            model=aiqe_config.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=aiqe_config.get("max_tokens", 4096),
            temperature=aiqe_config.get("temperature", 0.1),
        )

    def get_mqm_config(self) -> MQMConfig:
        """Get MQM framework configuration."""
        mqm_config = self.config.get("mqm", {})

        # Parse enabled categories
        categories_config = mqm_config.get("categories", {})
        enabled_categories = [
            ErrorCategory(cat)
            for cat, enabled in categories_config.items()
            if enabled
        ]

        # Parse severity weights
        weights_config = mqm_config.get("severity_weights", {})
        severity_weights = {
            ErrorSeverity(sev): weight
            for sev, weight in weights_config.items()
        }

        return MQMConfig(
            enabled_categories=enabled_categories,
            severity_weights=severity_weights,
            base_score=mqm_config.get("base_score", 100),
        )

    def get_quality_thresholds(self) -> QualityThresholds:
        """Get quality thresholds."""
        aiqe_config = self.config.get("aiqe", {})

        return QualityThresholds(
            auto_approve_threshold=aiqe_config.get("auto_approve_threshold", 95.0),
            flag_for_review_threshold=aiqe_config.get("flag_for_review_threshold", 70.0),
            block_threshold=aiqe_config.get("min_confidence_score", 50.0),
        )

    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        return self.config.get("workflow", {})

    def get_termbase_config(self) -> Dict[str, Any]:
        """Get term base configuration."""
        return self.config.get("termbase", {})

    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting configuration."""
        return self.config.get("reporting", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get("logging", {})

    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration."""
        return self.config.get("api", {})

    def get_batch_size(self) -> int:
        """Get batch processing size."""
        aiqe_config = self.config.get("aiqe", {})
        return aiqe_config.get("batch_size", 10)
