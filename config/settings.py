"""根層相容性包裝器：將所有符號轉發至 mcp_buy123_vendor.config.settings。

保留 `from config.settings import get_headers, get_url, ENDPOINTS` 等根層匯入名稱。
"""

import _src_bootstrap  # noqa: F401

from mcp_buy123_vendor.config.settings import (  # noqa: F401
    API_VERSION,
    BASE_URL,
    DEFAULT_PER_PAGE,
    ENDPOINTS,
    FRONTEND_URL,
    get_headers,
    get_url,
)

__all__ = [
    "API_VERSION",
    "BASE_URL",
    "DEFAULT_PER_PAGE",
    "FRONTEND_URL",
    "ENDPOINTS",
    "get_headers",
    "get_url",
]
