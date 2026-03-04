"""Configuration and file paths for tron-twitter."""

import json
from pathlib import Path

TRON_TWITTER_DIR = Path.home() / ".tron" / "mods" / "twitter"
COOKIES_PATH = TRON_TWITTER_DIR / "cookies.json"
CONFIG_PATH = TRON_TWITTER_DIR / "config.json"

DEFAULT_CONFIG = {
    "format": "json",
    "trending_category": "trending",
    "search_product": "Top",
}


def ensure_dirs():
    TRON_TWITTER_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    ensure_dirs()
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
