"""Vendor API auth: seed access/refresh tokens from env, auto-refresh on 401.

Design (on-demand login, inspired by github.com/nrvim/garmin-givemydata):
  - Tokens live in an in-process cache, persisted to .env by the login tool.
  - On MCP startup, mcp_server.py calls load_dotenv; if VENDOR_ACCESS_TOKEN
    is present it's picked up on first use.
  - If the cache is empty when a tool calls get_auth_headers(), we raise
    a VendorAuthError instructing the caller to run the `vendor_login`
    MCP tool. No credentials are read inside this module.
  - On 401 from upstream, rest_client calls invalidate_access_token(),
    which tries POST /v1/auth/refresh-token. On refresh failure the same
    error is raised — user re-runs vendor_login to open a browser.

Env vars:
  VENDOR_ACCESS_TOKEN   (optional) — seed for Bearer token; may be empty
                         if the user intends to log in via the tool.
  VENDOR_REFRESH_TOKEN  (optional) — seed for refresh_token.
"""

from __future__ import annotations

import os
import threading

import requests

ACCESS_TOKEN_VAR = "VENDOR_ACCESS_TOKEN"
REFRESH_TOKEN_VAR = "VENDOR_REFRESH_TOKEN"

_cache: dict[str, str | bool | None] = {
    "access_token": None,
    "refresh_token": None,
    "seeded": False,
}
_lock = threading.Lock()

_NEED_LOGIN_HINT = (
    "Run the `vendor_login` MCP tool (preferred) or the "
    "scripts/auth/playwright_login.py script to obtain fresh tokens."
)


class VendorAuthError(RuntimeError):
    pass


def _base_url() -> str:
    from config.settings import BASE_URL

    return BASE_URL


def _seed_from_env_locked() -> None:
    """Populate cache from env once per process. Caller must hold _lock."""
    if _cache["seeded"]:
        return
    _cache["access_token"] = os.environ.get(ACCESS_TOKEN_VAR) or None
    _cache["refresh_token"] = os.environ.get(REFRESH_TOKEN_VAR) or None
    _cache["seeded"] = True


def _do_refresh_locked() -> bool:
    refresh_token = _cache.get("refresh_token")
    if not refresh_token:
        return False

    try:
        response = requests.post(
            f"{_base_url()}/v1/auth/refresh-token",
            json={"refresh_token": refresh_token},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
    except requests.RequestException:
        return False

    if response.status_code != 200:
        return False

    body = response.json()
    if not body.get("success"):
        return False

    data = body.get("data") or {}
    new_access = data.get("access_token")
    if not new_access:
        return False

    _cache["access_token"] = new_access
    new_refresh = data.get("refresh_token")
    if new_refresh:
        _cache["refresh_token"] = new_refresh

    # Best-effort: also push refreshed tokens back to .env so a future MCP
    # restart picks them up without needing another browser login.
    _persist_env(new_access, new_refresh)
    return True


def _persist_env(access_token: str, refresh_token: str | None) -> None:
    """Write updated tokens to the project .env; ignored on any error."""
    try:
        from pathlib import Path

        from dotenv import set_key
    except Exception:
        return
    try:
        # .env co-located with the project root (parent of the auth/ dir).
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if not env_path.exists():
            env_path.touch()
        set_key(str(env_path), ACCESS_TOKEN_VAR, access_token, quote_mode="never")
        if refresh_token:
            set_key(str(env_path), REFRESH_TOKEN_VAR, refresh_token, quote_mode="never")
        os.environ[ACCESS_TOKEN_VAR] = access_token
        if refresh_token:
            os.environ[REFRESH_TOKEN_VAR] = refresh_token
    except Exception:
        pass


def set_tokens_from_login(access_token: str, refresh_token: str | None) -> None:
    """Called by the vendor_login tool after a successful browser login."""
    with _lock:
        _cache["access_token"] = access_token
        _cache["refresh_token"] = refresh_token
        _cache["seeded"] = True


def is_authenticated() -> bool:
    with _lock:
        _seed_from_env_locked()
        return bool(_cache["access_token"])


def _ensure_access_token() -> str:
    with _lock:
        _seed_from_env_locked()
        token = _cache["access_token"]
        if not token:
            raise VendorAuthError(
                "No vendor access token available. " + _NEED_LOGIN_HINT
            )
        return token  # type: ignore[return-value]


def invalidate_access_token() -> None:
    """Called by rest_client on 401. Refresh only — no captcha-gated re-login."""
    with _lock:
        _cache["access_token"] = None
        if _do_refresh_locked():
            return
        raise VendorAuthError(
            "Vendor token refresh failed (refresh_token missing or expired). "
            + _NEED_LOGIN_HINT
        )


def get_auth_headers() -> dict:
    return {"Authorization": f"Bearer {_ensure_access_token()}"}
