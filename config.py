"""Small JSON-backed application settings."""

from __future__ import annotations

import json
from pathlib import Path


def config_path() -> Path:
    return Path.home() / ".config" / "lyriclook" / "settings.json"


def load_settings() -> dict[str, str]:
    path = config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(settings: dict[str, str]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")