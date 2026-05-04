"""根層相容性包裝器：將所有符號轉發至 mcp_buy123_vendor.connectors.rest_client。

保留 `from connectors.rest_client import api_get, ServiceAPIError` 等根層匯入名稱。
"""

import _src_bootstrap  # noqa: F401

from mcp_buy123_vendor.connectors.rest_client import (  # noqa: F401
    ServiceAPIError,
    api_delete,
    api_get,
    api_post,
    api_put,
    api_request,
    fetch_all_pages,
    fetch_all_pages_by_date_segments,
    fetch_all_pages_cursor,
)

__all__ = [
    "ServiceAPIError",
    "api_delete",
    "api_get",
    "api_post",
    "api_put",
    "api_request",
    "fetch_all_pages",
    "fetch_all_pages_by_date_segments",
    "fetch_all_pages_cursor",
]
