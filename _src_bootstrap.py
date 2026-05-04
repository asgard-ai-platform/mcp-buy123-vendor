"""src layout bootstrap — 確保 <repo>/src 在 sys.path 上。

在任何 mcp_buy123_vendor.* 匯入之前呼叫此模組，
讓根層的相容性包裝器能夠找到 src 套件。
"""

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
