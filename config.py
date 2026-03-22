"""
Config - Loads and validates config.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Any


class Config:
    """
    Loads configuration from config.yaml.
    Falls back to environment variables for sensitive values like API keys.
    """

    DEFAULTS = {
        "anthropic_api_key": "",
        "headless": False,
        "slow_mo_ms": 50,
        "apply_delay_seconds": 30,
        "job_sources": ["indeed", "Linkedin"],
        "screenshots_dir": "screenshots",
        "db_path": "applications.db",
        "profile": {
            "zip_code": "532201",
            "state": "Andhra Pradesh",
            "country": "India",
            "work_authorization": "Yes",
            "requires_sponsorship": "No",
            "desired_salary": "",
            "notice_period": "2 weeks",
            "years_of_experience": "",
            "education_level": "Master's Degree",
            "veteran_status": "I am not a veteran",
            "disability_status": "I don't wish to answer",
            "pronouns": "",
        }
    }

    def __init__(self, config_path: str = "config.yaml"):
        self._data = dict(self.DEFAULTS)
        self._load(config_path)
        self._apply_env_overrides()

    def _load(self, path: str):
        """Load YAML config file if it exists."""
        p = Path(path)
        if p.exists():
            with open(p) as f:
                loaded = yaml.safe_load(f) or {}
            self._deep_merge(self._data, loaded)

    def _apply_env_overrides(self):
        """Override sensitive config from environment variables."""
        if api_key := os.environ.get("ANTHROPIC_API_KEY"):
            self._data["anthropic_api_key"] = api_key

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def _deep_merge(self, base: dict, override: dict):
        """Recursively merge override into base dict."""
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v
