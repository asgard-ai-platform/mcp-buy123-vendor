#!/usr/bin/env python3
"""E2E 整合測試：對 live API 呼叫每個已註冊的 MCP tool 一次。

/common/* 工具不需要 auth；其餘工具需要環境變數中有效的
VENDOR_ACCESS_TOKEN。

這是 opt-in 整合測試，預設不會在 pytest 中執行。
若要啟用，請設定環境變數：BUY123_RUN_LIVE_TESTS=1

直接執行（非 pytest）：
    BUY123_RUN_LIVE_TESTS=1 python tests/test_all_tools.py
"""

import asyncio
import os
import sys
import traceback

import pytest

# ── opt-in 標記：未設定 BUY123_RUN_LIVE_TESTS=1 時跳過整個模組 ──────────────
# 使用 pytestmark 而非模組層級 pytest.skip()，避免在 pytest 外執行時崩潰。
pytestmark = pytest.mark.skipif(
    os.environ.get("BUY123_RUN_LIVE_TESTS") != "1",
    reason="Live integration tests are opt-in. Set BUY123_RUN_LIVE_TESTS=1 to enable.",
)

# 確保專案根目錄在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools.abnormal_order_tools as abnormal_order_tools  # noqa: E402
import tools.auth_tools as auth_tools  # noqa: E402
import tools.bundle_tools as bundle_tools  # noqa: E402
import tools.channel_tools as channel_tools  # noqa: E402
import tools.common_tools as common_tools  # noqa: E402
import tools.inventory_tools as inventory_tools  # noqa: E402
import tools.return_tools as return_tools  # noqa: E402
import tools.shipment_tools as shipment_tools  # noqa: E402

from app import mcp  # noqa: E402


# ── 輔助函式 ──────────────────────────────────────────────────────────────────

def _call_tool(name: str, fn, **kwargs) -> None:
    """呼叫單一 tool 函式，失敗時印出 traceback 並重新拋出。"""
    print(f"\n{'=' * 60}\nTEST: {name}\n{'=' * 60}")
    result = fn(**kwargs)
    print("  PASS")
    if isinstance(result, dict):
        for key, value in result.items():
            preview = str(value)
            if len(preview) > 120:
                preview = preview[:120] + "..."
            print(f"    {key}: {preview}")


def _has_auth() -> bool:
    """回傳是否已設定 VENDOR_ACCESS_TOKEN。"""
    return bool(os.environ.get("VENDOR_ACCESS_TOKEN"))


# ── 無需 auth 的 common/* 測試 ────────────────────────────────────────────────

class TestCommonToolsLive:
    """不需要 auth 的 common/* tool 整合測試。"""

    def test_list_banks(self) -> None:
        _call_tool("list_banks", common_tools.list_banks)

    def test_list_bundle_types(self) -> None:
        _call_tool("list_bundle_types", common_tools.list_bundle_types)

    def test_list_delivery_types(self) -> None:
        _call_tool("list_delivery_types", common_tools.list_delivery_types)

    def test_list_invoice_types(self) -> None:
        _call_tool("list_invoice_types", common_tools.list_invoice_types)

    def test_list_product_statuses(self) -> None:
        _call_tool("list_product_statuses", common_tools.list_product_statuses)


# ── 需要 auth 的測試 ───────────────────────────────────────────────────────────

_requires_auth = pytest.mark.skipif(
    not _has_auth(),
    reason="Auth-required tests skipped: set VENDOR_ACCESS_TOKEN to enable.",
)


@_requires_auth
class TestAuthToolsLive:
    """需要 VENDOR_ACCESS_TOKEN 的 auth tool 整合測試。"""

    def test_get_current_user(self) -> None:
        _call_tool("get_current_user", auth_tools.get_current_user)

    def test_get_my_menu(self) -> None:
        _call_tool("get_my_menu", auth_tools.get_my_menu)


@_requires_auth
class TestAbnormalOrderToolsLive:
    """需要 auth 的異常訂單 tool 整合測試。"""

    def test_list_abnormal_orders(self) -> None:
        _call_tool(
            "list_abnormal_orders",
            abnormal_order_tools.list_abnormal_orders,
            page=1,
            size=5,
        )


@_requires_auth
class TestBundleToolsLive:
    """需要 auth 的組合商品 tool 整合測試。"""

    def test_list_bundles(self) -> None:
        _call_tool("list_bundles", bundle_tools.list_bundles, page=1, page_size=5)

    def test_list_pricing_channels(self) -> None:
        _call_tool("list_pricing_channels", bundle_tools.list_pricing_channels)


@_requires_auth
class TestChannelToolsLive:
    """需要 auth 的通路 tool 整合測試。"""

    def test_list_channels(self) -> None:
        _call_tool("list_channels", channel_tools.list_channels, page=1, size=5)

    def test_list_channel_products(self) -> None:
        _call_tool(
            "list_channel_products",
            channel_tools.list_channel_products,
            page=1,
            size=5,
        )


@_requires_auth
class TestInventoryToolsLive:
    """需要 auth 的庫存 tool 整合測試。"""

    def test_list_item_option_inventories(self) -> None:
        _call_tool(
            "list_item_option_inventories",
            inventory_tools.list_item_option_inventories,
            page=1,
            limit=5,
        )


@_requires_auth
class TestShipmentToolsLive:
    """需要 auth 的出貨 tool 整合測試。"""

    def test_list_shipments(self) -> None:
        # delivery_type 選一個常見值做 smoke check；若 API 回 400 屬預期範圍
        _call_tool(
            "list_shipments",
            shipment_tools.list_shipments,
            delivery_type="home-delivery",
            page=1,
            size=5,
        )

    def test_list_cvs_shipment_details(self) -> None:
        _call_tool(
            "list_cvs_shipment_details",
            shipment_tools.list_cvs_shipment_details,
            delivery_type="711-b2c",
            page=1,
            limit=5,
        )

    def test_list_home_delivery_shipment_details(self) -> None:
        _call_tool(
            "list_home_delivery_shipment_details",
            shipment_tools.list_home_delivery_shipment_details,
            page=1,
            size=5,
        )


@_requires_auth
class TestReturnToolsLive:
    """需要 auth 的退貨 tool 整合測試。"""

    def test_list_returns(self) -> None:
        _call_tool("list_returns", return_tools.list_returns, page=1, size=5)

    def test_list_uncollected_cvs_returns(self) -> None:
        _call_tool(
            "list_uncollected_cvs_returns",
            return_tools.list_uncollected_cvs_returns,
            page=1,
            size=5,
        )


# ── MCP tool 清單驗證 ─────────────────────────────────────────────────────────

class TestMcpToolRegistrationLive:
    """驗證 MCP server 已正確註冊所有工具（需要 live import）。"""

    def test_registered_tools_count(self) -> None:
        """已註冊的 tool 數量應大於 0。"""
        tools_list = asyncio.run(mcp.list_tools())
        assert len(tools_list) > 0, "MCP server 應至少有一個已註冊的 tool"
        print(f"\nRegistered tools: {len(tools_list)}")
        for tool in tools_list:
            desc = (tool.description or "")[:70]
            print(f"  - {tool.name}: {desc}")


# ── 直接執行（非 pytest）入口 ─────────────────────────────────────────────────

def _main() -> None:
    """直接以 python 執行時的 smoke-test 入口（保留向下相容）。"""
    if not os.environ.get("BUY123_RUN_LIVE_TESTS") == "1":
        print(
            "Live integration tests are opt-in.\n"
            "Set BUY123_RUN_LIVE_TESTS=1 to enable."
        )
        sys.exit(0)

    results: list[tuple[str, str]] = []

    def run(name: str, fn, **kwargs) -> None:
        try:
            _call_tool(name, fn, **kwargs)
            results.append(("PASS", name))
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL: {exc}")
            traceback.print_exc()
            results.append(("FAIL", name))

    tools_list = asyncio.run(mcp.list_tools())
    print(f"Registered tools: {len(tools_list)}")

    print(f"\n{'#' * 60}\nNO-AUTH TESTS (common/*)\n{'#' * 60}")
    run("list_banks", common_tools.list_banks)
    run("list_bundle_types", common_tools.list_bundle_types)
    run("list_delivery_types", common_tools.list_delivery_types)
    run("list_invoice_types", common_tools.list_invoice_types)
    run("list_product_statuses", common_tools.list_product_statuses)

    if not _has_auth():
        print(
            "\nSKIPPING auth-required tests: "
            "set VENDOR_ACCESS_TOKEN (and optionally VENDOR_REFRESH_TOKEN)."
        )
    else:
        print(f"\n{'#' * 60}\nAUTH-REQUIRED TESTS\n{'#' * 60}")
        run("get_current_user", auth_tools.get_current_user)
        run("get_my_menu", auth_tools.get_my_menu)
        run("list_abnormal_orders", abnormal_order_tools.list_abnormal_orders, page=1, size=5)
        run("list_bundles", bundle_tools.list_bundles, page=1, page_size=5)
        run("list_pricing_channels", bundle_tools.list_pricing_channels)
        run("list_channels", channel_tools.list_channels, page=1, size=5)
        run("list_channel_products", channel_tools.list_channel_products, page=1, size=5)
        run("list_item_option_inventories", inventory_tools.list_item_option_inventories, page=1, limit=5)
        run("list_shipments", shipment_tools.list_shipments, delivery_type="home-delivery", page=1, size=5)
        run("list_cvs_shipment_details", shipment_tools.list_cvs_shipment_details, delivery_type="711-b2c", page=1, limit=5)
        run("list_home_delivery_shipment_details", shipment_tools.list_home_delivery_shipment_details, page=1, size=5)
        run("list_returns", return_tools.list_returns, page=1, size=5)
        run("list_uncollected_cvs_returns", return_tools.list_uncollected_cvs_returns, page=1, size=5)

    print(f"\n{'#' * 60}\nSUMMARY\n{'#' * 60}")
    passed = sum(1 for s, _ in results if s == "PASS")
    failed = sum(1 for s, _ in results if s == "FAIL")
    for status, name in results:
        icon = "+" if status == "PASS" else "X"
        print(f"  [{icon}] {name}")
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    _main()
