#!/usr/bin/env python3
"""Sanity-check that Playwright is installed and Chromium can launch.

Run this right after:
    ./.venv/bin/pip install -e '.[auth]'
    ./.venv/bin/playwright install chromium

If this script exits 0 and prints a Chromium version, the `vendor_login`
MCP tool and scripts/auth/playwright_login.py should both work.

Exit codes:
    0  OK (Chromium launched headless and reported a version)
    1  playwright Python package missing → run: pip install -e '.[auth]'
    2  Chromium binary missing or wrong version → run: playwright install chromium
    3  Chromium launched but crashed (usually missing system libs on Linux)
"""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    # 1. Python package present?
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "FAIL: playwright Python package not installed.\n"
            "  Run: ./.venv/bin/pip install -e '.[auth]'",
            file=sys.stderr,
        )
        return 1

    # 2. Browser binary present + launch succeeds?
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg or "browserType.launch" in msg:
                    print(
                        f"FAIL: Chromium binary not installed or path mismatch.\n"
                        f"  Run: ./.venv/bin/playwright install chromium\n"
                        f"  Underlying: {msg.splitlines()[0]}",
                        file=sys.stderr,
                    )
                    return 2
                if (
                    "missing dependencies" in msg.lower()
                    or "libnss" in msg
                    or "libatk" in msg
                ):
                    print(
                        f"FAIL: System libraries missing (typical on Linux).\n"
                        f"  Run: ./.venv/bin/playwright install --with-deps chromium\n"
                        f"  Underlying: {msg.splitlines()[0]}",
                        file=sys.stderr,
                    )
                    return 3
                print(f"FAIL: Chromium launch failed.\n  {msg}", file=sys.stderr)
                traceback.print_exc()
                return 3

            try:
                version = browser.version
                context = browser.new_context()
                page = context.new_page()
                page.goto("about:blank", timeout=5000)
                page.close()
                context.close()
            finally:
                browser.close()
    except Exception:
        traceback.print_exc()
        return 3

    print(f"OK: Chromium {version} launched headless and served about:blank.")
    print("    vendor_login MCP tool and scripts/auth/playwright_login.py are ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
