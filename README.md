# mcp-buy123-vendor

`mcp-buy123-vendor` is an open-source [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for the buy123 vendor portal. It gives AI clients such as Claude Desktop, Claude Code, and other MCP-compatible agents read-only tools for querying vendor operations data, including orders, returns, shipments, products, bundles, channels, inventory, permissions, and vendor profile records.

This project is useful when you want an AI assistant to inspect buy123 vendor data through structured MCP tools instead of manually browsing the vendor portal.

> **Legal prerequisite**: This tool requires a legitimate vendor account on the buy123 platform. You must hold a valid vendor identity and comply with the platform's terms of service. Unauthorized access is not supported.
>
> **Unofficial project**: This repository is community-maintained and is not an official product of, or endorsed by, buy123.

Traditional Chinese documentation is available in [README.zh-TW.md](README.zh-TW.md).

## Highlights

- MCP server for buy123 vendor portal data access
- Read-only query tools for vendor operations workflows
- Claude Desktop and Claude Code compatible local MCP configuration
- Interactive on-demand login flow with local token storage
- Offline unit test suite for safe local development

## Provided Tools

**59 AI-callable tools** — all query-only. Every tool returns the upstream API response envelope: `{ success, msg, data, pagination? }`.

### General Enumerations (no login required — 14 tools)

`list_banks`, `list_bundle_types`, `list_bundle_delivery_notes`, `list_bundle_delivery_statuses`, `list_delivery_types`, `list_packaging_types`, `list_invoice_types`, `list_product_statuses`, `list_event_product_statuses`, `list_gross_profit_statuses`, `list_review_statuses`, `list_announcement_notify_levels`, `list_announcement_notify_scopes`, `list_announcement_notify_types`

### Query Tools (login required — 45 tools)

| Category | Tools |
|----------|-------|
| User info | `get_current_user`, `get_my_menu` |
| Abnormal orders | `list_abnormal_orders` |
| Returns | `list_returns`, `list_uncollected_cvs_returns` |
| Bundles | `list_bundles`, `get_bundle`, `list_bundle_items`, `get_bundle_item`, `list_pricing_channels` |
| Channels | `list_channels`, `list_channel_products` |
| Inventory | `list_item_option_inventories` |
| Shipments | `list_shipments`, `list_cvs_shipment_details`, `list_home_delivery_shipment_details` |
| Permission management | `list_vendor_actions`, `list_vendor_roles`, `list_vendor_role_actions` |
| Vendor management | `get_vendor`, `get_vendor_profile`, `list_vendor_attachments`, `list_vendor_categories`, `check_vendor_tax_number`, `get_vendor_return_address`, `list_vendor_store_pickup_return_dc`, `list_vendor_store_pickup_return_mode`, `list_vendor_store_pickups`, `get_vendor_store_pickup`, `list_vendor_users`, `check_vendor_user_email` |
| Product management | `list_item_selection`, `list_items`, `get_item`, `list_item_history`, `list_item_options`, `list_item_options_selection`, `list_products`, `get_product`, `list_product_annotation_logs`, `list_product_bundle_prices`, `list_product_bundles`, `list_product_versions`, `list_commodity_categories`, `get_template_category_form` |

### Not Supported

- Write operations (POST / PUT / DELETE)
- Attachment preview or download
- Excel or other binary file downloads
- Shipping label printing

## Usage

### Requirements

- Python 3.10+
- A legitimate vendor account on the buy123 platform

### Install

```bash
git clone https://github.com/asgard-ai-platform/mcp-buy123-vendor.git
cd mcp-buy123-vendor

python3 -m venv .venv
./.venv/bin/pip install -e .

cp .env.example .env
# Edit .env and fill in your vendor credentials
```

### Run as an MCP Server

```bash
./.venv/bin/python mcp_server.py
```

### Claude Desktop Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and replace `<PROJECT_DIR>` with the absolute path to this project:

```json
{
  "mcpServers": {
    "buy123-vendor": {
      "command": "<PROJECT_DIR>/.venv/bin/python",
      "args": ["<PROJECT_DIR>/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop. The `buy123-vendor` server should appear as running under Settings → Developer.

### Claude Code CLI

A `.mcp.json` is included at the project root. Running `claude` from this directory will pick it up automatically.

### Authentication

The server uses on-demand login. When a query requires authentication and no valid token is cached, the MCP client will be prompted to complete the login flow interactively. A desktop environment (windowed display) is required for the login step.

## Development

### Install Dev Dependencies

```bash
./.venv/bin/pip install -e '.[dev]'
```

### Run Tests

Tests run offline and do not require a real API connection:

```bash
./.venv/bin/python -m pytest tests/
```

Integration tests that require a live API connection are opt-in and must be triggered manually after configuring valid credentials in `.env`.

### Environment Variables

See `.env.example` for all configurable fields. The authentication token is managed automatically by the login flow and does not need to be set manually.

## License

See [LICENSE](LICENSE).
