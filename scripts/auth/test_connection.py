#!/usr/bin/env python3
"""Validate env, probe /common/banks (no auth), then call /v1/auth/me.

Usage:
    VENDOR_ACCESS_TOKEN=... VENDOR_REFRESH_TOKEN=... \
      python scripts/auth/test_connection.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Auto-load .env so this script behaves consistently with mcp_server.py
# and scripts/auth/playwright_login.py.
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv is a base dep; absence means broken install, not fatal here

REQUIRED_VARS = [
    "VENDOR_ACCESS_TOKEN",
]


def check_env_vars() -> bool:
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
    """/common/banks needs no auth — proves base URL + network."""
    import requests

    from config.settings import BASE_URL

    print(f"\nProbing public endpoint {BASE_URL}/v1/common/banks ...")
    try:
        r = requests.get(f"{BASE_URL}/v1/common/banks", timeout=15)
    except Exception as e:
        print(f"  FAIL: {e}")
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
    print("\nLogging in + calling /v1/auth/me ...")
    try:
        from connectors.rest_client import api_get

        result = api_get("me")
    except Exception as e:
        print(f"  FAIL: {e}")
        return False
    data = result.get("data") if isinstance(result, dict) else None
    print(f"  OK: me.data = {data}")
    return bool(result.get("success"))


def main():
    print("=" * 50)
    print("mcp-core123-vendor-api — Connection Test")
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
