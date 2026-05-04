#!/usr/bin/env python3
"""Canonical Playwright 登入腳本（src-layout）。

Usage:
    pip install -e '.[auth]'
    playwright install chromium
    VENDOR_EMAIL=... VENDOR_PASSWORD=... VENDOR_ID=... \
      python -m mcp_buy123_vendor.scripts.playwright_login

此模組為實作的真實來源（source of truth）；
scripts/auth/playwright_login.py 僅作為向後相容的薄包裝，委派至此處。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    """執行 Playwright 瀏覽器登入流程，將 token 寫入 .env。"""
    # 找到專案根目錄（src/mcp_buy123_vendor/scripts/ 往上三層）
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    # 載入 .env，讓使用者不需手動在命令列前置環境變數
    try:
        from dotenv import load_dotenv

        load_dotenv(project_root / ".env")
    except ImportError:
        print(
            "ERROR: python-dotenv not installed. Run: pip install -e '.'",
            file=sys.stderr,
        )
        return 2

    from mcp_buy123_vendor.auth.browser_login import BrowserLoginError, browser_login
    from mcp_buy123_vendor.config.settings import BASE_URL, FRONTEND_URL

    for var in ("VENDOR_EMAIL", "VENDOR_PASSWORD", "VENDOR_ID"):
        if not os.environ.get(var):
            print(
                f"[warn] {var} not set — you'll need to type it in the browser yourself.",
                file=sys.stderr,
            )

    print(f"[info] frontend={FRONTEND_URL}  api_base={BASE_URL}")
    print("[info] Opening Chromium. Solve the captcha and click submit.")
    print("[info] Timeout: 10 minutes. Press Ctrl+C to abort.\n")

    try:
        result = browser_login(write_env=True)
    except BrowserLoginError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    env_path = project_root / ".env"
    print(f"\n[ok] Wrote tokens to {env_path}")
    print(f"\nVENDOR_ACCESS_TOKEN={result['access_token']}")
    if "refresh_token" in result:
        print(f"VENDOR_REFRESH_TOKEN={result['refresh_token']}")
    if "vendor_id" in result:
        print(f"# (vendor_id from response: {result['vendor_id']})")
    print("\nNext: restart the MCP server so it picks up the new env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
