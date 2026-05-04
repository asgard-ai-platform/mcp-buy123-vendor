"""Tools for vendor item-option inventory queries."""

from typing import Optional

from pydantic import Field

from app import mcp
from connectors.rest_client import api_get


@mcp.tool()
def list_item_option_inventories(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    sort: Optional[str] = Field(default=None, description="排序欄位"),
    order: Optional[str] = Field(default=None, description="排序方式 (asc / desc)"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    item_name: Optional[str] = Field(default=None, description="商品名稱 (模糊搜尋)"),
    vendor_sku: Optional[str] = Field(default=None, description="供應商商品料號"),
    item_status: Optional[str] = Field(default=None, description="商品狀態"),
    is_gift: Optional[bool] = Field(default=None, description="是否為贈品"),
    inventory_status: Optional[str] = Field(default=None, description="庫存狀態"),
) -> dict:
    """取得商品選項庫存列表 (GET /v1/item-option-inventories)."""
    params: dict = {"page": page, "limit": limit}
    for key, value in {
        "sort": sort,
        "order": order,
        "product_id": product_id,
        "item_name": item_name,
        "vendor_sku": vendor_sku,
        "item_status": item_status,
        "is_gift": is_gift,
        "inventory_status": inventory_status,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("item_option_inventories", params=params)
