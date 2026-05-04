"""Tools for vendor abnormal (return) order queries."""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


@mcp.tool()
def list_abnormal_orders(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    size: int = Field(default=20, description="每頁筆數"),
    type: Optional[str] = Field(default=None, description="異常類型"),
    is_processed: Optional[bool] = Field(default=None, description="是否已處理"),
    order_id: Optional[str] = Field(default=None, description="訂單 ID"),
    product_id: Optional[str] = Field(default=None, description="商品 ID"),
    product_name: Optional[str] = Field(default=None, description="商品名稱 (模糊搜尋)"),
) -> dict:
    """列出異常訂單 (GET /v1/abnormal-orders)."""
    params: dict = {"page": page, "size": size}
    if type is not None:
        params["type"] = type
    if is_processed is not None:
        params["is_processed"] = is_processed
    if order_id is not None:
        params["order_id"] = order_id
    if product_id is not None:
        params["product_id"] = product_id
    if product_name is not None:
        params["product_name"] = product_name
    return api_get("abnormal_orders", params=params)
