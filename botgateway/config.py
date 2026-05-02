import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "management_token": "",
}


def get_default_config_path() -> Path:
    return Path.home() / ".botgateway" / "config.json"


def load_config(config_path: Optional[str] = None) -> dict:
    if config_path:
        path = Path(config_path)
    else:
        path = get_default_config_path()
    
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return {**DEFAULT_CONFIG, **config}
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict, config_path: Optional[str] = None) -> None:
    if config_path:
        path = Path(config_path)
    else:
        path = get_default_config_path()
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def generate_token(length: int = 32) -> str:
    import secrets
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))