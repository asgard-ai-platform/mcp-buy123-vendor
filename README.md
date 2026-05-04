# mcp-core123-vendor-api

透過 [Model Context Protocol](https://modelcontextprotocol.io/) 將 Core123 **Vendor 前台** API（`/v1/`*，非 `/admin/`）包裝成 AI 可呼叫工具的 MCP server。基於 [Asgard MCP template](https://github.com/asgard-ai-platform/mcp-template) 建置。

## 範圍 (Phase 1：唯讀)

- 61 個工具：2 個 auth 管理（`auth_status` / `vendor_login`）+ 59 個 GET 查詢。
- 涵蓋：auth/me、方案、渠道、庫存、出貨、異常訂單、退貨、權限管理、供應商管理、商品管理、14 個 `/common/`* 列舉。
- 不提供寫入 (POST/PUT/DELETE)，延至 Phase 2。
- 不提供附件預覽/下載、Excel 或其他二進位下載（`/shipments/cvs-shipment-list`、`/shipments/home-delivery-order`、`/shipments/home-delivery-reply`、`/shipments/labels`、`/settlement-orders/excel/*`、`/vendors/attachment/{id}`、`/vendors/preview-item-attachment/*`），延至 Phase 2。

## 認證（on-demand 登入）

Swagger 宣告 `APIKeyAuth`，header 為 `Authorization: Bearer <token>`。`POST /v1/auth/login` 要 reCAPTCHA v2 Invisible，只有真人可以解，所以 MCP **本身不會背景登入**——但提供了一個 `vendor_login` MCP tool，可以從 Claude 對話中觸發。

### 一次性安裝

```bash
./.venv/bin/pip install -e '.[auth]'
./.venv/bin/playwright install chromium

# 立刻做 sanity check，避免拖到 Claude 對話中才炸
./.venv/bin/python scripts/auth/verify_playwright.py
```

`verify_playwright.py` 預期輸出 `OK: Chromium <版號> launched headless and served about:blank.`；任何失敗都會印對應修復指令（詳見下方 Troubleshooting）。

把 `VENDOR_EMAIL` / `VENDOR_PASSWORD` / `VENDOR_ID` 填進 `.env`（這些只給 Playwright 自動填表用；MCP server runtime 用不到）。

### Troubleshooting（`playwright install chromium` 常見失敗）

| Exit code | 症狀 | 修復 |
|---|---|---|
| 1 | `playwright` Python 套件沒裝 | `./.venv/bin/pip install -e '.[auth]'` |
| 2 | 下載了 Python 套件但 Chromium 二進位不在 / 版本不合 | `./.venv/bin/playwright install chromium`（用 **venv 內** 的 `playwright`，不是系統 PATH 那個） |
| 3 (Linux) | 系統缺 `libnss3` / `libatk` / `libgtk-3` 等 | `./.venv/bin/playwright install --with-deps chromium`（需 sudo） |

其他場景：

- **公司 VPN / proxy 擋 `cdn.playwright.dev`**：改用 Microsoft 官方 fallback mirror
  ```bash
  PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.download.prss.microsoft.com \
    ./.venv/bin/playwright install chromium
  ```
- **磁碟空間不足**（要 ~450 MB）：指定其他目錄
  ```bash
  PLAYWRIGHT_BROWSERS_PATH=/big/disk/ms-playwright \
    ./.venv/bin/playwright install chromium
  # 注意：以後啟動 MCP / 跑 verify 也要帶同一個 PLAYWRIGHT_BROWSERS_PATH
  ```
- **macOS Gatekeeper 擋 Chromium**：`xattr -dr com.apple.quarantine ~/Library/Caches/ms-playwright`
- **WSL / 純無頭環境**：我們的 `vendor_login` 用 headed 模式，需要 WSLg 或有 X server；WSL1 不行

### 方式 1：Claude 對話中觸發（推薦）

當 token 沒設 / 過期時，跟 Claude 說：

> 幫我用 core123-vendor 看方案列表

Claude 呼叫 `list_bundles` → 得到 `VendorAuthError: No vendor access token available. Run the vendor_login MCP tool...` → Claude 接著呼叫 `vendor_login` → Chromium 視窗從你的桌面彈出 → **你親自解 captcha 並按登入** → tool 回報成功 → Claude 重跑 `list_bundles`。

之後的 tool 呼叫直接使用記憶體 cache，不會再開瀏覽器；401 時會自動 refresh（記憶體 + `.env` 都更新）。

也可以直接讓 Claude 先呼叫 `auth_status`（不打 API，純本地檢查）確認登入狀態。

### 方式 2：命令列腳本（不想在 Claude 裡開瀏覽器時）

```bash
./.venv/bin/python scripts/auth/playwright_login.py
```

流程與方式 1 相同，只是在 terminal 啟動。寫入 `.env` 後重啟 MCP server（Claude）讓新 token 生效。

### 方式 3：手動從 DevTools 複製

直接在瀏覽器登入供應商前台，DevTools → Network → 找到 `POST /v1/auth/login` response，把 `data.access_token` / `data.refresh_token` 貼進 `.env`。

### 執行期行為

- **啟動**：`mcp_server.py` 會 `load_dotenv`；若 `.env` 有 token 則進記憶體 cache。沒有也不會爆，只是第一個需要 auth 的 tool 會要求先登入。
- **401 自動續命**：`rest_client` 呼叫 `invalidate_access_token()` → `POST /v1/auth/refresh-token` → 成功就更新 cache（及 `.env`，讓下次 restart 也有新 token）、失敗就丟錯要求呼叫 `vendor_login`。
- **重啟持久化**：refresh 成功的 token 會寫回 `.env`，Claude 重開也不用再登入，直到 `refresh_token` 本身過期。

## 工具清單

### `/common/`*（免登入，14 個工具）

`list_banks`, `list_bundle_types`, `list_bundle_delivery_notes`, `list_bundle_delivery_statuses`, `list_delivery_types`, `list_packaging_types`, `list_invoice_types`, `list_product_statuses`, `list_event_product_statuses`, `list_gross_profit_statuses`, `list_review_statuses`, `list_announcement_notify_levels`, `list_announcement_notify_scopes`, `list_announcement_notify_types`

### Auth 管理（2 個工具）

`auth_status`（本地檢查目前是否有可用 token，不打 API）、`vendor_login`（開瀏覽器讓使用者登入；更新 cache 與 `.env`）

### Auth 使用者資訊（需登入，2 個工具）

`get_current_user`, `get_my_menu`

### 異常訂單（1 個工具）

`list_abnormal_orders`（異常訂單列表）

### 退貨（2 個工具）

`list_returns`（退貨大表）、`list_uncollected_cvs_returns`（超商未取退回大表）

### 方案 (Bundles)（5 個工具）

`list_bundles`, `get_bundle`, `list_bundle_items`, `get_bundle_item`, `list_pricing_channels`

### 渠道 (Channels)（2 個工具）

`list_channels`, `list_channel_products`

### 庫存 (Inventory)（1 個工具）

`list_item_option_inventories`（商品選項庫存）

### 出貨 (Shipments)（3 個工具）

`list_shipments`（廠商出貨列表）、`list_cvs_shipment_details`（超取出貨明細）、`list_home_delivery_shipment_details`（宅配出貨明細）

### 權限管理 (Permission)（3 個工具）

`list_vendor_actions`（廠商權限列表）、`list_vendor_roles`（廠商角色列表）、`list_vendor_role_actions`（廠商角色權限）

### 供應商管理 (Vendor)（12 個工具）

基本資料：`get_vendor`、`get_vendor_profile`、`list_vendor_attachments`、`list_vendor_categories`、`check_vendor_tax_number`、`get_vendor_return_address`
超商取貨設定：`list_vendor_store_pickup_return_dc`、`list_vendor_store_pickup_return_mode`、`list_vendor_store_pickups`、`get_vendor_store_pickup`
使用者：`list_vendor_users`、`check_vendor_user_email`

### 商品管理 (Product)（14 個工具）

Items（選項導向）：`list_item_selection`、`list_items`、`get_item`、`list_item_history`、`list_item_options`、`list_item_options_selection`
Products（主檔導向）：`list_products`、`get_product`、`list_product_annotation_logs`、`list_product_bundle_prices`、`list_product_bundles`、`list_product_versions`
分類：`list_commodity_categories`、`get_template_category_form`

所有工具都會原封不動回傳上游 API 的 response envelope：`{success, msg, data, pagination?}`。

## 快速開始

```bash
python3 -m venv .venv
./.venv/bin/pip install -e .

cp .env.example .env
# 編輯 .env 填入真實憑證 (參考上面的認證章節取得 token)

# 1) 驗證連線與認證
./.venv/bin/python scripts/auth/test_connection.py

# 2) 跑所有工具的 smoke test
./.venv/bin/python tests/test_all_tools.py

# 3) 啟動 MCP server (stdio)
./.venv/bin/python mcp_server.py
```

## 在 Claude 中啟用

MCP server 啟動時會自動載入專案根目錄的 `.env`（由 `scripts/auth/playwright_login.py` 維護），因此 Claude 的設定檔**只需要指定執行路徑**，不用重複放 token / credentials。Token 刷新完只要重啟 Claude 就生效。

### Claude Desktop

編輯 `~/Library/Application Support/Claude/claude_desktop_config.json`：

把下面 `<PROJECT_DIR>` 換成本專案在你電腦上的絕對路徑（例：`/Users/you/code/mcp-core123-vendor-api`）：

```json
{
  "mcpServers": {
    "core123-vendor": {
      "command": "<PROJECT_DIR>/.venv/bin/python",
      "args": ["<PROJECT_DIR>/mcp_server.py"]
    }
  }
}
```

重啟 Claude Desktop → Settings → Developer 應能看到 `core123-vendor` 為 running，工具列會多出 61 個 `core123-vendor.*`。

### Claude Code CLI

專案根已附 `.mcp.json`；在此目錄下 `claude` CLI 會自動讀到。或透過 `claude mcp add` 手動加到全域設定。

所有憑證 / token 一律寫在專案的 `.env`，Playwright 腳本會自動維護：

- `VENDOR_ACCESS_TOKEN` / `VENDOR_REFRESH_TOKEN` — 由 Playwright 寫入，MCP server 使用
- `VENDOR_EMAIL` / `VENDOR_PASSWORD` / `VENDOR_ID` — 由 Playwright 使用（MCP server 用不到）

