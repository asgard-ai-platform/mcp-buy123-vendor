"""Tools for vendor channel (渠道) and channel-product queries."""

from typing import Optional

from pydantic import Field

from app import mcp
from connectors.rest_client import api_get


@mcp.tool()
def list_channels(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁數量"),
    sort_field: Optional[str] = Field(default=None, description="排序欄位"),
    sort_order: Optional[str] = Field(default=None, description="排序方向 (asc / desc)"),
    status: Optional[str] = Field(default=None, description="狀態"),
    business_type: Optional[str] = Field(default=None, description="業務類型 (B2B / B2C)"),
) -> dict:
    """渠道列表 (GET /v1/channels)."""
    params: dict = {"page": page, "size": size}
    for key, value in {
        "sort_field": sort_field,
        "sort_order": sort_order,
        "status": status,
        "business_type": business_type,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("channels", params=params)


@mcp.tool()
def list_channel_products(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁數量"),
    sort_field: Optional[str] = Field(default=None, description="排序欄位"),
    sort_order: Optional[str] = Field(default=None, description="排序方向 (asc / desc)"),
    channel_id: Optional[int] = Field(default=None, description="渠道 ID"),
    keyword: Optional[str] = Field(default=None, description="關鍵字 (名稱等)"),
    channel_product_status: Optional[str] = Field(default=None, description="渠道商品狀態"),
    inventory_status: Optional[str] = Field(default=None, description="庫存狀態"),
) -> dict:
    """渠道商品列表 (GET /v1/channel-products)."""
    params: dict = {"page": page, "size": size}
    for key, value in {
        "sort_field": sort_field,
        "sort_order": sort_order,
        "channel_id": channel_id,
        "keyword": keyword,
        "channel_product_status": channel_product_status,
        "inventory_status": inventory_status,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("channel_products", params=params)
