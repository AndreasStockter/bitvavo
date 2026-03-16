"""Configuration loading from YAML and .env files."""

from __future__ import annotations

from pathlib import Path

import yaml

from .schema import AppConfig, SecretsConfig


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    """Load application config from YAML file and environment variables."""
    path = Path(config_path)

    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    secrets = SecretsConfig()
    data["secrets"] = secrets.model_dump()

    # Override telegram chat_id from env if set
    if secrets.telegram_chat_id and "telegram" in data:
        data["telegram"]["chat_id"] = secrets.telegram_chat_id

    return AppConfig(**data)
