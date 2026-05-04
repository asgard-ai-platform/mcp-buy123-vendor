#!/usr/bin/env python3
"""Entry point — side-effect imports register @mcp.tool() decorators.

Loads .env (co-located with this file) before importing any module that
reads environment variables, so the MCP process picks up tokens written
by scripts/auth/playwright_login.py regardless of the cwd Claude Desktop
or any other MCP client launches it from.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import tools.abnormal_order_tools  # noqa: E402,F401
import tools.auth_tools  # noqa: E402,F401
import tools.bundle_tools  # noqa: E402,F401
import tools.channel_tools  # noqa: E402,F401
import tools.common_tools  # noqa: E402,F401
import tools.inventory_tools  # noqa: E402,F401
import tools.permission_tools  # noqa: E402,F401
import tools.product_tools  # noqa: E402,F401
import tools.return_tools  # noqa: E402,F401
import tools.shipment_tools  # noqa: E402,F401
import tools.vendor_tools  # noqa: E402,F401

from app import mcp  # noqa: E402


def main():
    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()
