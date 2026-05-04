"""根層相容性包裝器：將 `mcp` 轉發至正式 src 套件。

保留 `from app import mcp` 的根層匯入名稱，
實作來源已移至 mcp_buy123_vendor.app。
"""

import _src_bootstrap  # noqa: F401 — 確保 src/ 在 sys.path 上

from mcp_buy123_vendor.app import mcp  # noqa: F401 — 重新匯出

__all__ = ["mcp"]
