#!/usr/bin/env python3
"""CLI wrapper around auth.browser_login.

Usage:
    pip install -e '.[auth]'
    playwright install chromium
    VENDOR_EMAIL=... VENDOR_PASSWORD=... VENDOR_ID=... \
      python scripts/auth/playwright_login.py

Most of the logic lives in auth/browser_login.py so the same flow can
also be invoked from Claude via the `vendor_login` MCP tool.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    # Load .env so user doesn't need to prepend env vars manually.
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        print(
            "ERROR: python-dotenv not installed. Run: pip install -e '.'",
            file=sys.stderr,
        )
        return 2

    from auth.browser_login import BrowserLoginError, browser_login
    from config.settings import BASE_URL, FRONTEND_URL

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
    except BrowserLoginError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1

    env_path = PROJECT_ROOT / ".env"
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
