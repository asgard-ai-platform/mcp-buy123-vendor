#!/usr/bin/env python3
"""E2E runner: call each registered MCP tool once against the live API.

The /common/* tools need no auth; the rest require valid
VENDOR_EMAIL/PASSWORD/ID/CAPTCHA_TOKEN in env.
"""

import asyncio
import os
import sys
import traceback

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


results: list[tuple[str, str]] = []


def run_test(name: str, fn, **kwargs) -> None:
    print(f"\n{'=' * 60}\nTEST: {name}\n{'=' * 60}")
    try:
        result = fn(**kwargs)
        print("  PASS")
        if isinstance(result, dict):
            for key, value in result.items():
                preview = str(value)
                if len(preview) > 120:
                    preview = preview[:120] + "..."
                print(f"    {key}: {preview}")
        results.append(("PASS", name))
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        results.append(("FAIL", name))


def main() -> None:
    tools_list = asyncio.run(mcp.list_tools())
    print(f"Registered tools: {len(tools_list)}")
    for tool in tools_list:
        desc = (tool.description or "")[:70]
        print(f"  - {tool.name}: {desc}")

    print(f"\n{'#' * 60}\nNO-AUTH TESTS (common/*)\n{'#' * 60}")
    run_test("list_banks", common_tools.list_banks)
    run_test("list_bundle_types", common_tools.list_bundle_types)
    run_test("list_delivery_types", common_tools.list_delivery_types)
    run_test("list_invoice_types", common_tools.list_invoice_types)
    run_test("list_product_statuses", common_tools.list_product_statuses)

    has_creds = bool(os.environ.get("VENDOR_ACCESS_TOKEN"))
    if not has_creds:
        print(
            "\nSKIPPING auth-required tests: "
            "set VENDOR_ACCESS_TOKEN (and optionally VENDOR_REFRESH_TOKEN)."
        )
    else:
        print(f"\n{'#' * 60}\nAUTH-REQUIRED TESTS\n{'#' * 60}")
        run_test("get_current_user", auth_tools.get_current_user)
        run_test("get_my_menu", auth_tools.get_my_menu)
        run_test(
            "list_abnormal_orders",
            abnormal_order_tools.list_abnormal_orders,
            page=1,
            size=5,
        )
        run_test("list_bundles", bundle_tools.list_bundles, page=1, page_size=5)
        run_test("list_pricing_channels", bundle_tools.list_pricing_channels)
        run_test("list_channels", channel_tools.list_channels, page=1, size=5)
        run_test(
            "list_channel_products",
            channel_tools.list_channel_products,
            page=1,
            size=5,
        )
        run_test(
            "list_item_option_inventories",
            inventory_tools.list_item_option_inventories,
            page=1,
            limit=5,
        )
        # /shipments requires delivery_type; pick one likely to exist per API.
        # If it errors 400, adjust or skip — this is a smoke check, not assertion.
        run_test(
            "list_shipments",
            shipment_tools.list_shipments,
            delivery_type="home-delivery",
            page=1,
            size=5,
        )
        run_test(
            "list_cvs_shipment_details",
            shipment_tools.list_cvs_shipment_details,
            delivery_type="711-b2c",
            page=1,
            limit=5,
        )
        run_test(
            "list_home_delivery_shipment_details",
            shipment_tools.list_home_delivery_shipment_details,
            page=1,
            size=5,
        )
        run_test("list_returns", return_tools.list_returns, page=1, size=5)
        run_test(
            "list_uncollected_cvs_returns",
            return_tools.list_uncollected_cvs_returns,
            page=1,
            size=5,
        )

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
    main()
