"""Tools for vendor management + vendor user management (供應商 / 供應商使用者)."""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


# -------------------------------------------------------------------------
# Vendor info
# -------------------------------------------------------------------------

@mcp.tool()
def get_vendor() -> dict:
    """取得廠商資訊 (GET /v1/vendors)."""
    return api_get("vendor")


@mcp.tool()
def get_vendor_profile() -> dict:
    """取得廠商基本資料 (GET /v1/vendors/profile)."""
    return api_get("vendor_profile")


@mcp.tool()
def list_vendor_attachments() -> dict:
    """取得廠商上傳文件列表 (GET /v1/vendors/attachments).

    檔案本體下載屬於 binary endpoint，Phase 1 未實作。
    """
    return api_get("vendor_attachments")


@mcp.tool()
def list_vendor_categories() -> dict:
    """取得廠商分類列表 (GET /v1/vendors/categories)."""
    return api_get("vendor_categories")


@mcp.tool()
def check_vendor_tax_number(
    tax_number: str = Field(description="統一編號"),
) -> dict:
    """檢查統編是否存在 (GET /v1/vendors/check-tax-number/{tax_number})."""
    return api_get("vendor_check_tax_number", path_params={"tax_number": tax_number})


@mcp.tool()
def get_vendor_return_address() -> dict:
    """取得廠商退貨地址 (GET /v1/vendors/return-address)."""
    return api_get("vendor_return_address")


# -------------------------------------------------------------------------
# Store-pickup settings
# -------------------------------------------------------------------------

@mcp.tool()
def list_vendor_store_pickup_return_dc() -> dict:
    """獲取供應商超商退貨 DC (GET /v1/vendors/store-pickup-return-dc)."""
    return api_get("vendor_store_pickup_return_dc")


@mcp.tool()
def list_vendor_store_pickup_return_mode(
    store_type: Optional[str] = Field(
        default=None, description="超商取貨類型 (可選): 711 / fme"
    ),
) -> dict:
    """獲取供應商超商取貨退貨方式 (GET /v1/vendors/store-pickup-return-mode)."""
    params = {}
    if store_type is not None:
        params["store_type"] = store_type
    return api_get("vendor_store_pickup_return_mode", params=params or None)


@mcp.tool()
def list_vendor_store_pickups(
    store_type: str = Field(description="超商取貨類型: 711 / fme"),
    type: str = Field(description="商業類型: B2C / C2C / B2C-COLD"),
) -> dict:
    """獲取超商取貨申請資料 (GET /v1/vendors/store-pickups)."""
    return api_get(
        "vendor_store_pickups",
        params={"store_type": store_type, "type": type},
    )


@mcp.tool()
def get_vendor_store_pickup(
    store_type: str = Field(description="超商取貨類型: 711 / fme"),
) -> dict:
    """獲取供應商超商取貨申請 (GET /v1/vendors/store-pickups/{store_type})."""
    return api_get("vendor_store_pickup_detail", path_params={"store_type": store_type})


# -------------------------------------------------------------------------
# Vendor users (供應商使用者管理)
# -------------------------------------------------------------------------

@mcp.tool()
def list_vendor_users(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    name: Optional[str] = Field(default=None, description="使用者名稱 (模糊搜尋)"),
    sort: Optional[str] = Field(default=None, description="排序欄位"),
    order: Optional[str] = Field(default=None, description="排序方式 (asc / desc)"),
) -> dict:
    """取得廠商使用者列表 (GET /v1/vendors/users)."""
    params: dict = {"page": page, "limit": limit}
    for key, value in {"name": name, "sort": sort, "order": order}.items():
        if value is not None:
            params[key] = value
    return api_get("vendor_users", params=params)


@mcp.tool()
def check_vendor_user_email(
    email: str = Field(description="使用者 Email"),
) -> dict:
    """檢查使用者 Email 是否存在 (GET /v1/vendors/check-vendor-user-email/{email})."""
    return api_get("vendor_check_user_email", path_params={"email": email})
