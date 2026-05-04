"""根層相容性包裝器：將所有符號轉發至 mcp_buy123_vendor.auth.browser_login。

保留 `from auth.browser_login import browser_login, BrowserLoginError` 等根層匯入名稱。
"""

import _src_bootstrap  # noqa: F401

from mcp_buy123_vendor.auth.browser_login import (  # noqa: F401
    BrowserLoginError,
    ENV_PATH,
    LOGIN_API_PATH,
    LOGIN_WAIT_TIMEOUT_MS,
    LoginResult,
    PROJECT_ROOT,
    browser_login,
)

__all__ = [
    "BrowserLoginError",
    "ENV_PATH",
    "LOGIN_API_PATH",
    "LOGIN_WAIT_TIMEOUT_MS",
    "LoginResult",
    "PROJECT_ROOT",
    "browser_login",
]
