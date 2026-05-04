"""根層相容性包裝器：將所有符號轉發至 mcp_buy123_vendor.config.constants。

保留 `from config.constants import BASE_URL` 等根層匯入名稱。
"""

import _src_bootstrap  # noqa: F401

from mcp_buy123_vendor.config.constants import (  # noqa: F401
    API_VERSION,
    BASE_URL,
    DEFAULT_PER_PAGE,
    FRONTEND_URL,
)

__all__ = ["BASE_URL", "FRONTEND_URL", "API_VERSION", "DEFAULT_PER_PAGE"]
