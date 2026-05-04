"""Tools for current-user info + on-demand browser login.

`vendor_login` launches a real Chromium window for the user to solve the
reCAPTCHA; it updates the in-process token cache AND writes to .env so
subsequent MCP restarts already have valid tokens.
"""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


@mcp.tool()
def get_current_user() -> dict:
    """取得目前登入供應商使用者的資訊 (GET /v1/auth/me)."""
    return api_get("me")


@mcp.tool()
def get_my_menu(
    mock: Optional[int] = Field(default=None, description="是否為測試 (1 = 測試資料)"),
) -> dict:
    """取得供應商使用者選單 (GET /v1/auth/me/menu)."""
    params = {}
    if mock is not None:
        params["mock"] = mock
    return api_get("my_menu", params=params or None)


@mcp.tool()
def auth_status() -> dict:
    """Report whether the MCP currently has a usable vendor access token.

    Call this before other tools if you're unsure whether login is needed.
    Does NOT hit the upstream API — purely a local cache check.
    """
    from mcp_buy123_vendor.auth.vendor_login import _cache, _lock, is_authenticated

    authed = is_authenticated()
    with _lock:
        has_refresh = bool(_cache.get("refresh_token"))
    return {
        "authenticated": authed,
        "has_refresh_token": has_refresh,
        "hint": (
            None
            if authed
            else "Call vendor_login to open a browser and obtain fresh tokens."
        ),
    }


@mcp.tool()
def vendor_login() -> dict:
    """Open a real Chromium window so the user can log in to the vendor frontend.

    Use this when:
      - `auth_status` reports `authenticated=false`
      - Another tool has returned a "No vendor access token" / "token refresh
        failed" error

    Flow:
      1. A Chromium window opens at the vendor frontend.
      2. Email / password / vendor_id are best-effort prefilled from env.
      3. **The user solves the reCAPTCHA and clicks submit themselves.**
      4. This tool captures the POST /v1/auth/login response, updates the
         in-memory cache, and writes VENDOR_ACCESS_TOKEN / VENDOR_REFRESH_TOKEN
         back to .env so future MCP restarts are also authenticated.

    Blocks until the user completes the login (up to 10 minutes) or aborts.
    """
    import concurrent.futures

    from mcp_buy123_vendor.auth.browser_login import BrowserLoginError, browser_login
    from mcp_buy123_vendor.auth.vendor_login import set_tokens_from_login

    # FastMCP runs the server on an asyncio event loop, and Playwright's sync
    # API refuses to run inside one ("Please use the Async API instead"). Punt
    # the Playwright call onto a worker thread — that thread has no running
    # loop, so sync_playwright() is happy. Same pattern as
    # nrvim/garmin-givemydata's sync.
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(browser_login, write_env=True)
            result = future.result()
    except BrowserLoginError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": (
                "Ensure playwright is installed (`pip install -e '.[auth]'` "
                "and `playwright install chromium`) and VENDOR_EMAIL / "
                "VENDOR_PASSWORD / VENDOR_ID are set in .env for autofill."
            ),
        }

    set_tokens_from_login(
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token"),
    )

    return {
        "success": True,
        "vendor_id": result.get("vendor_id"),
        "has_refresh_token": "refresh_token" in result,
        "message": "Logged in. Tokens cached in memory and written to .env.",
    }
