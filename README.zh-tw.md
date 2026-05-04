# mcp-buy123-vendor

`mcp-buy123-vendor` 將 buy123 供應商後台 API 包裝為 [MCP](https://modelcontextprotocol.io/) 伺服器，讓 AI 客戶端能夠查詢供應商資料——訂單、出貨、商品、庫存等——無需手動操作後台介面。

> **法律前提**：本工具需要在 buy123 平台上擁有合法的供應商帳號。您必須持有有效的供應商身份，並遵守平台服務條款。不支援未經授權的存取。

英文文件請參閱 [README.md](README.md)。

## 提供的工具

所有查詢工具均回傳上游 API 的回應封包：`{ success, msg, data, pagination? }`。

### 通用列舉（無需登入 — 14 個工具）

`list_banks`、`list_bundle_types`、`list_bundle_delivery_notes`、`list_bundle_delivery_statuses`、`list_delivery_types`、`list_packaging_types`、`list_invoice_types`、`list_product_statuses`、`list_event_product_statuses`、`list_gross_profit_statuses`、`list_review_statuses`、`list_announcement_notify_levels`、`list_announcement_notify_scopes`、`list_announcement_notify_types`

### 查詢工具（需登入 — 45 個工具）

| 類別 | 工具 |
|------|------|
| 使用者資訊 | `get_current_user`、`get_my_menu` |
| 異常訂單 | `list_abnormal_orders` |
| 退貨 | `list_returns`、`list_uncollected_cvs_returns` |
| 組合商品 | `list_bundles`、`get_bundle`、`list_bundle_items`、`get_bundle_item`、`list_pricing_channels` |
| 通路 | `list_channels`、`list_channel_products` |
| 庫存 | `list_item_option_inventories` |
| 出貨 | `list_shipments`、`list_cvs_shipment_details`、`list_home_delivery_shipment_details` |
| 供應商管理 | `get_vendor`、`get_vendor_profile`、`list_vendor_attachments`、`list_vendor_categories`、`check_vendor_tax_number`、`get_vendor_return_address`、`list_vendor_store_pickup_return_dc`、`list_vendor_store_pickup_return_mode`、`list_vendor_store_pickups`、`get_vendor_store_pickup`、`list_vendor_users`、`check_vendor_user_email` |
| 商品管理 | `list_item_selection`、`list_items`、`get_item`、`list_item_history`、`list_item_options`、`list_item_options_selection`、`list_products`、`get_product`、`list_product_annotation_logs`、`list_product_bundle_prices`、`list_product_bundles`、`list_product_versions`、`list_commodity_categories`、`get_template_category_form` |
| 權限管理 | `list_vendor_actions`、`list_vendor_roles`、`list_vendor_role_actions` |

### 不支援的功能

- 寫入操作（POST / PUT / DELETE）
- 附件預覽或下載
- Excel 或其他二進位檔案下載
- 出貨標籤列印

## 使用方式

### 環境需求

- Python 3.10+
- buy123 平台上的合法供應商帳號

### 安裝

```bash
git clone https://github.com/your-org/mcp-buy123-vendor.git
cd mcp-buy123-vendor

python3 -m venv .venv
./.venv/bin/pip install -e .

cp .env.example .env
# 編輯 .env 並填入您的供應商憑證
```

### 啟動 MCP 伺服器

```bash
./.venv/bin/python mcp_server.py
```

### Claude Desktop 設定

編輯 `~/Library/Application Support/Claude/claude_desktop_config.json`，將 `<PROJECT_DIR>` 替換為本專案的絕對路徑：

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

重新啟動 Claude Desktop 後，`buy123-vendor` 伺服器應出現在「設定 → 開發者」中並顯示為執行中。

### Claude Code CLI

專案根目錄已包含 `.mcp.json`。在此目錄執行 `claude` 時會自動載入設定。

### 驗證機制

伺服器採用按需登入方式。當查詢需要驗證且尚無有效的快取 token 時，MCP 客戶端會提示使用者完成互動式登入流程。登入步驟需要桌面環境（視窗顯示）。

## 開發

### 安裝開發依賴

```bash
./.venv/bin/pip install -e '.[dev]'
```

### 執行測試

測試可離線執行，不需要真實的 API 連線：

```bash
./.venv/bin/python -m pytest tests/
```

需要真實 API 連線的整合測試為選擇性執行，必須在 `.env` 中設定有效憑證後手動觸發。

### 環境變數

所有可設定欄位請參閱 `.env.example`。驗證 token 由登入流程自動管理，無需手動設定。

## 授權

請參閱 [LICENSE](LICENSE)。
