"""Tools for vendor shipment queries (廠商出貨 / 超取 / 宅配)."""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


@mcp.tool()
def list_shipments(
    delivery_type: str = Field(
        description="出貨方式 (required; 值參考 list_delivery_types tool)"
    ),
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁筆數"),
    product_name: Optional[str] = Field(default=None, description="商品名稱 (模糊搜尋)"),
    vendor_sku: Optional[str] = Field(default=None, description="供應商 SKU"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    start_date: Optional[str] = Field(default=None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Field(default=None, description="結束日期 YYYY-MM-DD"),
    shipping_type: Optional[str] = Field(
        default=None, description="出貨類型: normal / express / preorder"
    ),
) -> dict:
    """廠商出貨列表 (GET /v1/shipments)."""
    params: dict = {"page": page, "size": size, "delivery_type": delivery_type}
    for key, value in {
        "product_name": product_name,
        "vendor_sku": vendor_sku,
        "product_id": product_id,
        "start_date": start_date,
        "end_date": end_date,
        "shipping_type": shipping_type,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("shipments", params=params)


@mcp.tool()
def list_cvs_shipment_details(
    delivery_type: str = Field(
        description="超取方式 (required): 711-b2c / fme-b2c / fme-b2c-cold / 711-c2c / fme-c2c"
    ),
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    product_name: Optional[str] = Field(default=None, description="商品名稱"),
    is_shipped: Optional[str] = Field(
        default=None, description="是否已出貨: 'true' / 'false'"
    ),
    start_date: Optional[str] = Field(default=None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Field(default=None, description="結束日期 YYYY-MM-DD"),
    shipping_type: Optional[str] = Field(
        default=None, description="出貨類型: normal / express / preorder"
    ),
) -> dict:
    """超取出貨明細列表 (GET /v1/shipments/cvs/details)."""
    params: dict = {"page": page, "limit": limit, "delivery_type": delivery_type}
    for key, value in {
        "product_id": product_id,
        "product_name": product_name,
        "is_shipped": is_shipped,
        "start_date": start_date,
        "end_date": end_date,
        "shipping_type": shipping_type,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("shipments_cvs_details", params=params)


@mcp.tool()
def list_home_delivery_shipment_details(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁筆數"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    product_name: Optional[str] = Field(default=None, description="商品名稱"),
    is_shipped: Optional[str] = Field(
        default=None, description="是否已出貨: 'true' / 'false'"
    ),
) -> dict:
    """宅配出貨明細列表 (GET /v1/shipments/home-delivery/details)."""
    params: dict = {"page": page, "size": size}
    for key, value in {
        "product_id": product_id,
        "product_name": product_name,
        "is_shipped": is_shipped,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("shipments_home_delivery_details", params=params)
