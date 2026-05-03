import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "management_token": "",
    "master_key": "",
}


def get_default_config_path() -> Path:
    return Path.home() / ".botgateway" / "config.json"


def load_config(config_path: str | None = None) -> dict:
    if config_path:
        path = Path(config_path)
    else:
        path = get_default_config_path()

    if not path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
        merged = {**DEFAULT_CONFIG, **config}

        master_key = merged.get("master_key", "")
        if master_key:
            os.environ["BOTGATEWAY_MASTER_KEY"] = master_key

        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict, config_path: str | None = None) -> None:
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
