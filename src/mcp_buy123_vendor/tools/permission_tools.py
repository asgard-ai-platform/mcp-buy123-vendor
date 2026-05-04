"""Tools for vendor permission management (權限管理)."""

from typing import Optional

from pydantic import Field

from mcp_buy123_vendor.app import mcp
from mcp_buy123_vendor.connectors.rest_client import api_get


@mcp.tool()
def list_vendor_actions() -> dict:
    """取得廠商權限列表 (GET /v1/vendors/actions)."""
    return api_get("vendor_actions")


@mcp.tool()
def list_vendor_roles(
    page: int = Field(default=1, description="頁碼 (1-based)"),
    limit: int = Field(default=20, description="每頁筆數"),
) -> dict:
    """取得廠商角色列表 (GET /v1/vendors/roles)."""
    return api_get("vendor_roles", params={"page": page, "limit": limit})


@mcp.tool()
def list_vendor_role_actions(
    role_id: str = Field(description="角色 ID"),
) -> dict:
    """取得廠商角色權限 (GET /v1/vendors/roles/actions)."""
    return api_get("vendor_role_actions", params={"role_id": role_id})
