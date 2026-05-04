"""MCP server settings: base URL, endpoint map, header builder."""

from auth.vendor_login import get_auth_headers

BASE_URL = "https://api-vendor.xxtechec.com"
FRONTEND_URL = "https://vendor.xxtechec.com/"
API_VERSION = "v1"

DEFAULT_PER_PAGE = 50

ENDPOINTS = {
    # --- auth (current user info) ---
    "me": f"/{API_VERSION}/auth/me",
    "my_menu": f"/{API_VERSION}/auth/me/menu",
    # --- abnormal orders ---
    "abnormal_orders": f"/{API_VERSION}/abnormal-orders",
    # --- bundles ---
    "bundles": f"/{API_VERSION}/bundles",
    "bundle_detail": f"/{API_VERSION}/bundles/{{bundle_id}}",
    "bundle_items": f"/{API_VERSION}/bundles/{{bundle_id}}/items",
    "bundle_item_detail": f"/{API_VERSION}/bundles/{{bundle_id}}/items/{{item_id}}",
    "pricing_channels": f"/{API_VERSION}/bundles/pricing-channels",
    # --- channels ---
    "channels": f"/{API_VERSION}/channels",
    "channel_products": f"/{API_VERSION}/channel-products",
    # --- inventory ---
    "item_option_inventories": f"/{API_VERSION}/item-option-inventories",
    # --- shipments ---
    "shipments": f"/{API_VERSION}/shipments",
    "shipments_cvs_details": f"/{API_VERSION}/shipments/cvs/details",
    "shipments_home_delivery_details": f"/{API_VERSION}/shipments/home-delivery/details",
    # --- returns (退貨大表) ---
    "returns": f"/{API_VERSION}/returns",
    "uncollected_cvs_returns": f"/{API_VERSION}/uncollected-cvs-returns",
    # --- permission (vendor-scoped) ---
    "vendor_actions": f"/{API_VERSION}/vendors/actions",
    "vendor_roles": f"/{API_VERSION}/vendors/roles",
    "vendor_role_actions": f"/{API_VERSION}/vendors/roles/actions",
    # --- vendor management ---
    "vendor": f"/{API_VERSION}/vendors",
    "vendor_profile": f"/{API_VERSION}/vendors/profile",
    "vendor_attachments": f"/{API_VERSION}/vendors/attachments",
    "vendor_categories": f"/{API_VERSION}/vendors/categories",
    "vendor_check_tax_number": f"/{API_VERSION}/vendors/check-tax-number/{{tax_number}}",
    "vendor_return_address": f"/{API_VERSION}/vendors/return-address",
    "vendor_store_pickup_return_dc": f"/{API_VERSION}/vendors/store-pickup-return-dc",
    "vendor_store_pickup_return_mode": f"/{API_VERSION}/vendors/store-pickup-return-mode",
    "vendor_store_pickups": f"/{API_VERSION}/vendors/store-pickups",
    "vendor_store_pickup_detail": f"/{API_VERSION}/vendors/store-pickups/{{store_type}}",
    # --- vendor users ---
    "vendor_users": f"/{API_VERSION}/vendors/users",
    "vendor_check_user_email": f"/{API_VERSION}/vendors/check-vendor-user-email/{{email}}",
    # --- products & items ---
    "item_selection": f"/{API_VERSION}/item-selection",
    "items": f"/{API_VERSION}/items",
    "item_detail": f"/{API_VERSION}/items/{{id}}",
    "item_history": f"/{API_VERSION}/items/{{id}}/history",
    "item_options": f"/{API_VERSION}/items/{{id}}/options",
    "item_options_selection": f"/{API_VERSION}/items/{{id}}/options-selection",
    "products": f"/{API_VERSION}/products",
    "product_detail": f"/{API_VERSION}/products/{{product_id}}",
    "product_annotation_logs": f"/{API_VERSION}/products/{{product_id}}/annotation-logs",
    "product_bundle_prices": f"/{API_VERSION}/products/{{product_id}}/bundle-prices",
    "product_bundles": f"/{API_VERSION}/products/{{product_id}}/bundles",
    "product_versions": f"/{API_VERSION}/products/{{product_id}}/versions",
    "commodity_categories": f"/{API_VERSION}/vendors/commodities/categories",
    "commodity_template_category_form": (
        f"/{API_VERSION}/vendors/commodities/template-category-form/{{category_id}}"
    ),
    # --- common enumerations (no auth required) ---
    "common_banks": f"/{API_VERSION}/common/banks",
    "common_bundle_type": f"/{API_VERSION}/common/bundle-type",
    "common_bundle_delivery_note": f"/{API_VERSION}/common/bundle-delivery-note",
    "common_bundle_delivery_status": f"/{API_VERSION}/common/bundle-delivery-status",
    "common_delivery_type": f"/{API_VERSION}/common/delivery-type",
    "common_packaging_type": f"/{API_VERSION}/common/packaging-type",
    "common_invoice_type": f"/{API_VERSION}/common/invoice-type",
    "common_product_status": f"/{API_VERSION}/common/product-status",
    "common_event_product_status": f"/{API_VERSION}/common/event-product-status",
    "common_gross_profit_status": f"/{API_VERSION}/common/gross-profit-status",
    "common_review_status": f"/{API_VERSION}/common/review-status",
    "common_ann_notify_level": f"/{API_VERSION}/common/announcement-notify-level",
    "common_ann_notify_scope": f"/{API_VERSION}/common/announcement-notify-scope",
    "common_ann_notify_type": f"/{API_VERSION}/common/announcement-notify-type",
}


def get_headers(require_auth: bool = True) -> dict:
    """Build request headers. Pass require_auth=False for /common/* endpoints."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if require_auth:
        headers.update(get_auth_headers())
    return headers


def get_url(endpoint_key: str, **kwargs) -> str:
    path = ENDPOINTS[endpoint_key]
    if kwargs:
        path = path.format(**kwargs)
    return f"{BASE_URL}{path}"
