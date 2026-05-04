"""根層相容性包裝器：將所有符號轉發至 mcp_buy123_vendor.auth.vendor_login。

保留 `from auth.vendor_login import get_auth_headers` 等根層匯入名稱。
"""

import _src_bootstrap  # noqa: F401

from mcp_buy123_vendor.auth.vendor_login import (  # noqa: F401
    ACCESS_TOKEN_VAR,
    REFRESH_TOKEN_VAR,
    VendorAuthError,
    _cache,
    _lock,
    get_auth_headers,
    invalidate_access_token,
    is_authenticated,
    set_tokens_from_login,
)

__all__ = [
    "ACCESS_TOKEN_VAR",
    "REFRESH_TOKEN_VAR",
    "VendorAuthError",
    "get_auth_headers",
    "invalidate_access_token",
    "is_authenticated",
    "set_tokens_from_login",
]
