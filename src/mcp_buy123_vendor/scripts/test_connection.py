#!/usr/bin/env python3
"""Canonical 連線測試腳本（src-layout）。

驗證環境變數、探測 /common/banks（無需驗證），再呼叫 /v1/auth/me。

Usage:
    VENDOR_ACCESS_TOKEN=... VENDOR_REFRESH_TOKEN=... \
      python -m mcp_buy123_vendor.scripts.test_connection

此模組為實作的真實來源（source of truth）；
scripts/auth/test_connection.py 僅作為向後相容的薄包裝，委派至此處。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 找到專案根目錄（src/mcp_buy123_vendor/scripts/ 往上三層）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# 自動載入 .env，行為與 mcp_server.py 及 playwright_login.py 一致
try:
    from dotenv import load_dotenv

    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv 為基礎相依；缺少代表安裝損壞，此處不視為致命錯誤

REQUIRED_VARS = [
    "VENDOR_ACCESS_TOKEN",
]


def check_env_vars() -> bool:
    """確認必要環境變數均已設定。"""
    print("Checking environment variables...")
    missing = [var for var in REQUIRED_VARS if not os.environ.get(var)]
    if missing:
        print("  FAIL: Missing environment variables:")
        for var in missing:
            print(f"    - {var}")
        return False
    print("  OK: all required vars set.")
    return True


def check_public_endpoint() -> bool:
    """/common/banks 不需驗證 — 驗證 base URL 與網路連線。"""
    import requests

    from mcp_buy123_vendor.config.settings import BASE_URL

    print(f"\nProbing public endpoint {BASE_URL}/v1/common/banks ...")
    try:
        r = requests.get(f"{BASE_URL}/v1/common/banks", timeout=15)
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  FAIL: body={r.text[:200]}")
        return False
    body = r.json()
    banks = body.get("data") or []
    print(f"  OK: got {len(banks)} banks (first: {banks[0] if banks else 'n/a'}).")
    return True


def check_login_and_me() -> bool:
    """登入並呼叫 /v1/auth/me 驗證 token 有效性。"""
    print("\nLogging in + calling /v1/auth/me ...")
    try:
        from mcp_buy123_vendor.connectors.rest_client import api_get

        result = api_get("me")
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False
    data = result.get("data") if isinstance(result, dict) else None
    print(f"  OK: me.data = {data}")
    return bool(result.get("success"))


def main() -> None:
    """執行所有連線檢查，任一失敗即以非零狀態碼結束。"""
    print("=" * 50)
    print("mcp-buy123-vendor — Connection Test")
    print("=" * 50)

    if not check_env_vars():
        sys.exit(1)
    if not check_public_endpoint():
        sys.exit(1)
    if not check_login_and_me():
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
