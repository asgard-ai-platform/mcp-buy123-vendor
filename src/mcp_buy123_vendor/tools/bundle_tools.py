"""Tools for vendor bundle (方案) queries."""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


@mcp.tool()
def list_bundles(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    page_size: int = Field(default=20, description="每頁筆數"),
    sort_field: Optional[str] = Field(default=None, description="排序欄位"),
    sort_order: Optional[str] = Field(default=None, description="排序方式 (asc / desc)"),
    name: Optional[str] = Field(default=None, description="商品名稱 (模糊搜尋)"),
    category_id: Optional[str] = Field(default=None, description="商品類別 ID"),
) -> dict:
    """取得商品方案列表 (GET /v1/bundles)."""
    params: dict = {"page": page, "page_size": page_size}
    for key, value in {
        "sort_field": sort_field,
        "sort_order": sort_order,
        "name": name,
        "category_id": category_id,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("bundles", params=params)


@mcp.tool()
def get_bundle(
    bundle_id: str = Field(description="方案 ID"),
) -> dict:
    """檢視指定方案 (GET /v1/bundles/{bundle_id})."""
    return api_get("bundle_detail", path_params={"bundle_id": bundle_id})


@mcp.tool()
def list_bundle_items(
    bundle_id: str = Field(description="方案 ID"),
    bundle_version: Optional[int] = Field(default=None, description="方案版本"),
) -> dict:
    """取得方案商品選項列表 (GET /v1/bundles/{bundle_id}/items)."""
    params = {}
    if bundle_version is not None:
        params["bundle_version"] = bundle_version
    return api_get(
        "bundle_items",
        path_params={"bundle_id": bundle_id},
        params=params or None,
    )


@mcp.tool()
def get_bundle_item(
    bundle_id: str = Field(description="方案 ID"),
    item_id: str = Field(description="方案商品選項 ID"),
    bundle_version: Optional[int] = Field(default=None, description="方案版本"),
    item_version: Optional[int] = Field(default=None, description="選項版本"),
) -> dict:
    """取得單一方案商品選項 (GET /v1/bundles/{bundle_id}/items/{item_id})."""
    params = {}
    if bundle_version is not None:
        params["bundle_version"] = bundle_version
    if item_version is not None:
        params["item_version"] = item_version
    return api_get(
        "bundle_item_detail",
        path_params={"bundle_id": bundle_id, "item_id": item_id},
        params=params or None,
    )


@mcp.tool()
def list_pricing_channels() -> dict:
    """取得方案價格渠道列表 (GET /v1/bundles/pricing-channels)."""
    return api_get("pricing_channels")
