"""Configuration for tron-twitter.

`tron-twitter` is stateless: credentials and state are read from the
environment, and nothing is written to disk. This module is just the
thin adapter that parses and validates those env vars.
"""

import json
import os


DEFAULT_CONFIG = {
    "format": "json",
    "trending_category": "trending",
    "search_product": "Top",
}


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


def load_cookies() -> dict:
    """Read cookies from the `TRON_TWITTER_COOKIES` env var.

    Expected format: a JSON object containing at least `auth_token` and
    `ct0`, e.g. `{"auth_token": "...", "ct0": "..."}`.
    """
    raw = os.environ.get("TRON_TWITTER_COOKIES")
    if not raw:
        raise ConfigError(
            "TRON_TWITTER_COOKIES is not set. Supply cookies as a JSON "
            "object, e.g.:\n"
            "  TRON_TWITTER_COOKIES='{\"auth_token\":\"...\",\"ct0\":\"...\"}' "
            "tron-twitter ..."
        )
    try:
        cookies = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f"TRON_TWITTER_COOKIES is not valid JSON: {e}") from e
    if not isinstance(cookies, dict):
        raise ConfigError("TRON_TWITTER_COOKIES must be a JSON object")
    missing = [k for k in ("auth_token", "ct0") if not cookies.get(k)]
    if missing:
        raise ConfigError(
            f"TRON_TWITTER_COOKIES missing required keys: {', '.join(missing)}"
        )
    return cookies


def load_state() -> dict:
    """Read state from the `TRON_TWITTER_STATE` env var, or return `{}`.

    State is only meaningful for `check-mentions` and `check-dms`. When
    unset, those commands treat the bookmark as zero and return everything
    available.
    """
    raw = os.environ.get("TRON_TWITTER_STATE")
    if not raw:
        return {}
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f"TRON_TWITTER_STATE is not valid JSON: {e}") from e
    if not isinstance(state, dict):
        raise ConfigError("TRON_TWITTER_STATE must be a JSON object")
    return state
