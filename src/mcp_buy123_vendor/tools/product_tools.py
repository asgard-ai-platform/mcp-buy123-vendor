"""Tools for vendor product / item management (商品管理).

Naming:
  - `items`   endpoints → /v1/items/*   (商品，包含選項)
  - `products` endpoints → /v1/products/* (商品主檔，含版本/方案/註解)
  - commodity categories → /v1/vendors/commodities/*
"""

from typing import List, Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


# -------------------------------------------------------------------------
# Items
# -------------------------------------------------------------------------

@mcp.tool()
def list_item_selection(
    keyword: Optional[str] = Field(
        default=None, description="關鍵字 (商品名稱 / 廠商商品 SKU)"
    ),
    is_gift: Optional[bool] = Field(default=None, description="是否為贈品"),
    item_ids: Optional[str] = Field(
        default=None, description="商品 ID 列表 (逗號分隔)"
    ),
) -> dict:
    """取得商品選擇列表 (GET /v1/item-selection) — 只包含審核通過的商品，供方案選擇商品用。"""
    params = {}
    for key, value in {"keyword": keyword, "is_gift": is_gift, "item_ids": item_ids}.items():
        if value is not None:
            params[key] = value
    return api_get("item_selection", params=params or None)


@mcp.tool()
def list_items(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    sort: Optional[str] = Field(default=None, description="排序欄位"),
    order: Optional[str] = Field(default=None, description="排序方式"),
    keyword: Optional[str] = Field(
        default=None, description="關鍵字 (商品名稱 / 廠商商品 SKU)"
    ),
    item_status: Optional[str] = Field(default=None, description="商品狀態"),
    upc: Optional[str] = Field(
        default=None, description="Universal Product Code (UPC)"
    ),
    is_gift: Optional[bool] = Field(default=None, description="是否為贈品"),
) -> dict:
    """取得商品列表 (GET /v1/items)."""
    params: dict = {"page": page, "limit": limit}
    for key, value in {
        "sort": sort,
        "order": order,
        "keyword": keyword,
        "item_status": item_status,
        "upc": upc,
        "is_gift": is_gift,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("items", params=params)


@mcp.tool()
def get_item(
    id: str = Field(description="商品 ID"),
) -> dict:
    """取得商品詳細資訊 (GET /v1/items/{id})."""
    return api_get("item_detail", path_params={"id": id})


@mcp.tool()
def list_item_history(
    id: str = Field(description="商品 ID"),
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    sort_field: Optional[str] = Field(default=None, description="排序欄位"),
    sort_order: Optional[str] = Field(default=None, description="排序方式"),
) -> dict:
    """取得商品歷史紀錄 (GET /v1/items/{id}/history)."""
    params: dict = {"page": page, "limit": limit}
    for key, value in {"sort_field": sort_field, "sort_order": sort_order}.items():
        if value is not None:
            params[key] = value
    return api_get("item_history", path_params={"id": id}, params=params)


@mcp.tool()
def list_item_options(
    id: str = Field(description="商品 ID"),
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    sort_field: Optional[str] = Field(default=None, description="排序欄位"),
    sort_order: Optional[str] = Field(default=None, description="排序方式"),
) -> dict:
    """取得商品選項列表 (GET /v1/items/{id}/options)."""
    params: dict = {"page": page, "limit": limit}
    for key, value in {"sort_field": sort_field, "sort_order": sort_order}.items():
        if value is not None:
            params[key] = value
    return api_get("item_options", path_params={"id": id}, params=params)


@mcp.tool()
def list_item_options_selection(
    id: str = Field(description="商品 ID"),
    keyword: Optional[str] = Field(
        default=None, description="關鍵字 (商品名稱 / 廠商商品 SKU)"
    ),
) -> dict:
    """取得商品選項選擇列表 (GET /v1/items/{id}/options-selection)."""
    params = {}
    if keyword is not None:
        params["keyword"] = keyword
    return api_get(
        "item_options_selection", path_params={"id": id}, params=params or None
    )


# -------------------------------------------------------------------------
# Products
# -------------------------------------------------------------------------

@mcp.tool()
def list_products(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    sort: Optional[str] = Field(default=None, description="排序欄位"),
    order: Optional[str] = Field(default=None, description="排序方式"),
    display_name: Optional[str] = Field(default=None, description="搜尋商品名稱"),
    vendor_sku: Optional[str] = Field(default=None, description="廠商商品 SKU"),
    status: Optional[str] = Field(default=None, description="商品狀態"),
    category_id: Optional[str] = Field(default=None, description="商品分類 ID"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
) -> dict:
    """取得商品列表 (GET /v1/products)."""
    params: dict = {"page": page, "limit": limit}
    for key, value in {
        "sort": sort,
        "order": order,
        "display_name": display_name,
        "vendor_sku": vendor_sku,
        "status": status,
        "category_id": category_id,
        "product_id": product_id,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("products", params=params)


@mcp.tool()
def get_product(
    product_id: str = Field(description="商品 ID"),
    version: Optional[int] = Field(default=None, description="版本號"),
) -> dict:
    """取得商品 (GET /v1/products/{product_id})."""
    params = {}
    if version is not None:
        params["version"] = version
    return api_get(
        "product_detail", path_params={"product_id": product_id}, params=params or None
    )


@mcp.tool()
def list_product_annotation_logs(
    product_id: str = Field(description="商品 ID"),
    product_version: int = Field(description="商品版本 (required)"),
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    sort: Optional[str] = Field(default=None, description="排序欄位"),
    order: Optional[str] = Field(default=None, description="排序方式"),
) -> dict:
    """取得商品註解紀錄列表 (GET /v1/products/{product_id}/annotation-logs)."""
    params: dict = {
        "product_version": product_version,
        "page": page,
        "limit": limit,
    }
    for key, value in {"sort": sort, "order": order}.items():
        if value is not None:
            params[key] = value
    return api_get(
        "product_annotation_logs",
        path_params={"product_id": product_id},
        params=params,
    )


@mcp.tool()
def list_product_bundle_prices(
    product_id: str = Field(description="商品 ID"),
    channel_id: int = Field(description="渠道 ID (required)"),
    product_version: Optional[int] = Field(default=None, description="商品版本"),
    bundle_pricing_ids: Optional[List[str]] = Field(
        default=None, description="方案定價 ID 列表"
    ),
) -> dict:
    """取得商品方案渠道價錢列表 (GET /v1/products/{product_id}/bundle-prices)."""
    params: dict = {"channel_id": channel_id}
    if product_version is not None:
        params["product_version"] = product_version
    if bundle_pricing_ids is not None:
        params["bundle_pricing_ids"] = bundle_pricing_ids
    return api_get(
        "product_bundle_prices",
        path_params={"product_id": product_id},
        params=params,
    )


@mcp.tool()
def list_product_bundles(
    product_id: str = Field(description="商品 ID"),
    product_version: Optional[int] = Field(default=None, description="商品版本"),
) -> dict:
    """取得商品方案列表 (GET /v1/products/{product_id}/bundles)."""
    params = {}
    if product_version is not None:
        params["product_version"] = product_version
    return api_get(
        "product_bundles",
        path_params={"product_id": product_id},
        params=params or None,
    )


@mcp.tool()
def list_product_versions(
    product_id: str = Field(description="商品 ID"),
) -> dict:
    """取得商品版本列表 (GET /v1/products/{product_id}/versions)."""
    return api_get("product_versions", path_params={"product_id": product_id})


# -------------------------------------------------------------------------
# Commodity category forms
# -------------------------------------------------------------------------

@mcp.tool()
def list_commodity_categories(
    layer: Optional[int] = Field(default=None, description="層級"),
    parent_id: Optional[str] = Field(default=None, description="父類別 ID"),
    limit: Optional[int] = Field(default=None, description="查詢數量"),
) -> dict:
    """取得商品類別選單 (GET /v1/vendors/commodities/categories)."""
    params = {}
    for key, value in {
        "layer": layer,
        "parent_id": parent_id,
        "limit": limit,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("commodity_categories", params=params or None)


@mcp.tool()
def get_template_category_form(
    category_id: str = Field(description="分類 ID"),
) -> dict:
    """取得最新版的分類題組表單 (GET /v1/vendors/commodities/template-category-form/{category_id})."""
    return api_get(
        "commodity_template_category_form",
        path_params={"category_id": category_id},
    )
