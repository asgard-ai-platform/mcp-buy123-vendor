#!/usr/bin/env python3
"""向後相容入口包裝（scripts/auth layout）。

實作已移至 src/mcp_buy123_vendor/scripts/test_connection.py。
此檔案僅作為薄包裝，確保舊有執行方式仍可運作。

Usage:
    VENDOR_ACCESS_TOKEN=... VENDOR_REFRESH_TOKEN=... \
      python scripts/auth/test_connection.py
"""

import sys
from pathlib import Path

# 確保 src/ 在 sys.path 中，讓未安裝套件時也能找到 mcp_buy123_vendor
_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from mcp_buy123_vendor.scripts.test_connection import main  # noqa: E402

if __name__ == "__main__":
    main()
