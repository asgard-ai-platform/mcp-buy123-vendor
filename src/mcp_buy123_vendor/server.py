#!/usr/bin/env python3
"""Canonical MCP server entry point (src-layout).

載入 .env 後匯入所有 tool 模組（side-effect 註冊 @mcp.tool() 裝飾器），
再啟動 MCP stdio transport。

此模組為實作的真實來源（source of truth）；
根目錄的 mcp_server.py 僅作為向後相容的薄包裝，委派至此處。
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# 以此檔案所在的 src/mcp_buy123_vendor/ 往上兩層找到專案根目錄的 .env
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# side-effect imports — 每個模組在匯入時向 mcp 實例註冊工具
import mcp_buy123_vendor.tools.abnormal_order_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.auth_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.bundle_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.channel_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.common_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.inventory_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.permission_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.product_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.return_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.shipment_tools  # noqa: E402,F401
import mcp_buy123_vendor.tools.vendor_tools  # noqa: E402,F401

from mcp_buy123_vendor.app import mcp  # noqa: E402


def main() -> None:
    """啟動 MCP server（stdio transport）。"""
    mcp.run()


if __name__ == "__main__":
    main()
