"""Tools for the vendor frontend /common/* enumeration endpoints (no auth)."""

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


def _list(endpoint_key: str) -> dict:
    return api_get(endpoint_key, require_auth=False)


@mcp.tool()
def list_banks() -> dict:
    """獲取銀行列表 (GET /v1/common/banks)."""
    return _list("common_banks")


@mcp.tool()
def list_bundle_types() -> dict:
    """獲取方案類型列表 (GET /v1/common/bundle-type)."""
    return _list("common_bundle_type")


@mcp.tool()
def list_bundle_delivery_notes() -> dict:
    """獲取方案出貨備註列表 (GET /v1/common/bundle-delivery-note)."""
    return _list("common_bundle_delivery_note")


@mcp.tool()
def list_bundle_delivery_statuses() -> dict:
    """獲取方案出貨狀態列表 (GET /v1/common/bundle-delivery-status)."""
    return _list("common_bundle_delivery_status")


@mcp.tool()
def list_delivery_types() -> dict:
    """獲取出貨方式列表 (GET /v1/common/delivery-type)."""
    return _list("common_delivery_type")


@mcp.tool()
def list_packaging_types() -> dict:
    """獲取包材類型列表 (GET /v1/common/packaging-type)."""
    return _list("common_packaging_type")


@mcp.tool()
def list_invoice_types() -> dict:
    """獲取發票類型列表 (GET /v1/common/invoice-type)."""
    return _list("common_invoice_type")


@mcp.tool()
def list_product_statuses() -> dict:
    """獲取商品狀態列表 (GET /v1/common/product-status)."""
    return _list("common_product_status")


@mcp.tool()
def list_event_product_statuses() -> dict:
    """獲取活動商品狀態列表 (GET /v1/common/event-product-status)."""
    return _list("common_event_product_status")


@mcp.tool()
def list_gross_profit_statuses() -> dict:
    """獲取毛利狀態列表 (GET /v1/common/gross-profit-status)."""
    return _list("common_gross_profit_status")


@mcp.tool()
def list_review_statuses() -> dict:
    """獲取審核狀態列表 (GET /v1/common/review-status)."""
    return _list("common_review_status")


@mcp.tool()
def list_announcement_notify_levels() -> dict:
    """獲取公告通知等級列表 (GET /v1/common/announcement-notify-level)."""
    return _list("common_ann_notify_level")


@mcp.tool()
def list_announcement_notify_scopes() -> dict:
    """獲取公告通知範圍列表 (GET /v1/common/announcement-notify-scope)."""
    return _list("common_ann_notify_scope")


@mcp.tool()
def list_announcement_notify_types() -> dict:
    """獲取公告通知類型列表 (GET /v1/common/announcement-notify-type)."""
    return _list("common_ann_notify_type")
