"""Reusable Playwright-driven vendor login.

Opens a headed Chromium at the vendor frontend, best-effort prefills
email / password / vendor_id from env, waits for the user to solve the
reCAPTCHA and submit, then captures tokens from the POST /v1/auth/login
response.

Called from two places:
  - scripts/auth/playwright_login.py  (standalone CLI)
  - tools/auth_tools.py :: vendor_login  (MCP tool, on-demand)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

LOGIN_API_PATH = "/v1/auth/login"

# 10 minutes — user needs time for captcha.
LOGIN_WAIT_TIMEOUT_MS = 10 * 60 * 1000


class LoginResult(TypedDict, total=False):
    access_token: str
    refresh_token: str
    vendor_id: str


class BrowserLoginError(RuntimeError):
    """Raised when Playwright-based login cannot complete."""


def _best_effort_fill(page, value: str, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            locator = page.locator(sel).first
            if locator.count() == 0:
                continue
            locator.fill(value, timeout=2000)
            return True
        except Exception:
            continue
    return False


def browser_login(*, write_env: bool = True) -> LoginResult:
    """Launch a headed Chromium, await user-assisted login, return tokens.

    Args:
        write_env: if True, persist the tokens to the project .env via
            python-dotenv's set_key. In-memory cache updating is the
            caller's responsibility (the MCP tool needs that too).

    Returns:
        LoginResult with access_token, refresh_token, (optionally) vendor_id.

    Raises:
        BrowserLoginError: dependency missing, browser didn't reach login,
            upstream returned non-200, or response body lacked access_token.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise BrowserLoginError(
            "playwright not installed. Run: pip install -e '.[auth]' && "
            "playwright install chromium"
        ) from e

    if write_env:
        try:
            from dotenv import set_key  # noqa: F401 — early check
        except ImportError as e:
            raise BrowserLoginError(
                "python-dotenv not installed. Run: pip install -e '.'"
            ) from e

    # Late import so auth/vendor_login.py (which imports browser_login.py
    # transitively via tools/auth_tools.py) doesn't cause a circular
    # settings -> auth -> settings loop.
    from config.settings import BASE_URL, FRONTEND_URL

    email = os.environ.get("VENDOR_EMAIL", "")
    password = os.environ.get("VENDOR_PASSWORD", "")
    vendor_id = os.environ.get("VENDOR_ID", "")

    login_api_url_prefix = f"{BASE_URL}{LOGIN_API_PATH}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(FRONTEND_URL, wait_until="domcontentloaded")

        if email:
            _best_effort_fill(
                page,
                email,
                [
                    'input[type="email"]',
                    'input[name="email"]',
                    'input[id*="email" i]',
                    'input[placeholder*="email" i]',
                    'input[placeholder*="信箱"]',
                ],
            )
        if password:
            _best_effort_fill(
                page,
                password,
                [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[placeholder*="password" i]',
                    'input[placeholder*="密碼"]',
                ],
            )
        if vendor_id:
            _best_effort_fill(
                page,
                vendor_id,
                [
                    'input[name="vendor_id"]',
                    'input[id*="vendor" i]',
                    'input[placeholder*="vendor" i]',
                    'input[placeholder*="供應商"]',
                    'input[placeholder*="廠商"]',
                ],
            )

        try:
            with page.expect_response(
                lambda r: r.url.startswith(login_api_url_prefix) and r.request.method == "POST",
                timeout=LOGIN_WAIT_TIMEOUT_MS,
            ) as response_info:
                pass
            response = response_info.value
        except Exception as e:
            browser.close()
            raise BrowserLoginError(
                f"Did not observe POST {login_api_url_prefix} within timeout. "
                f"Underlying: {e}"
            ) from e

        status = response.status
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text()[:500]}

        browser.close()

    if status != 200 or not body.get("success"):
        raise BrowserLoginError(
            f"Login returned status={status}, body={body}. "
            f"check email/password/vendor_id and captcha."
        )

    data = body.get("data") or {}
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    returned_vendor_id = data.get("vendor_id")

    if not access_token:
        raise BrowserLoginError(f"Login response missing access_token: {body}")

    if write_env:
        from dotenv import set_key

        if not ENV_PATH.exists():
            ENV_PATH.touch()
        set_key(str(ENV_PATH), "VENDOR_ACCESS_TOKEN", access_token, quote_mode="never")
        if refresh_token:
            set_key(
                str(ENV_PATH), "VENDOR_REFRESH_TOKEN", refresh_token, quote_mode="never"
            )

    # Also seed os.environ so in-process readers pick up immediately.
    os.environ["VENDOR_ACCESS_TOKEN"] = access_token
    if refresh_token:
        os.environ["VENDOR_REFRESH_TOKEN"] = refresh_token

    result: LoginResult = {"access_token": access_token}
    if refresh_token:
        result["refresh_token"] = refresh_token
    if returned_vendor_id:
        result["vendor_id"] = returned_vendor_id
    return result
