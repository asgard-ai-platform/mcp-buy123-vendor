"""Tools for vendor return (退貨) bulk queries.

Distinct from tools/abnormal_order_tools.py:
  - abnormal_orders  → GET /v1/abnormal-orders     (異常訂單)
  - returns          → GET /v1/returns             (退貨大表)
  - uncollected cvs  → GET /v1/uncollected-cvs-returns (超商未取退回大表)
"""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


@mcp.tool()
def list_returns(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁筆數"),
    return_type: Optional[str] = Field(
        default=None,
        description="退貨單類型: pre-shipment / vendor-assigned / cancelled / abnormal",
    ),
    delivery_type: Optional[str] = Field(
        default=None,
        description="配送方式: fme / 711 / home-delivery / fme-cold",
    ),
    order_id: Optional[str] = Field(default=None, description="訂單 ID"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    product_name: Optional[str] = Field(default=None, description="商品名稱 (模糊搜尋)"),
) -> dict:
    """退貨大表 (GET /v1/returns)."""
    params: dict = {"page": page, "size": size}
    for key, value in {
        "return_type": return_type,
        "delivery_type": delivery_type,
        "order_id": order_id,
        "product_id": product_id,
        "product_name": product_name,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("returns", params=params)


@mcp.tool()
def list_uncollected_cvs_returns(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁筆數"),
    cvs_type: Optional[str] = Field(
        default=None,
        description=(
            "CVS 類型: 711-b2c / 711-c2c / 711-c2c-vendor-uncollected / "
            "fme-b2c / fme-b2c-cold / fme-c2c / fme-c2c-vendor-uncollected"
        ),
    ),
    start_date: Optional[str] = Field(default=None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Field(default=None, description="結束日期 YYYY-MM-DD"),
    order_id: Optional[str] = Field(default=None, description="訂單 ID"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    product_name: Optional[str] = Field(default=None, description="商品名稱 (模糊搜尋)"),
) -> dict:
    """超商未取退回大表 (GET /v1/uncollected-cvs-returns)."""
    params: dict = {"page": page, "size": size}
    for key, value in {
        "cvs_type": cvs_type,
        "start_date": start_date,
        "end_date": end_date,
        "order_id": order_id,
        "product_id": product_id,
        "product_name": product_name,
    }.items():
        if value is not None:
            params[key] = value
    return api_get("uncollected_cvs_returns", params=params)
