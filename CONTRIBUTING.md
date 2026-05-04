# Contributing

感謝你對本專案的興趣。以下說明如何在本地開發、執行測試，以及提交 Pull Request 的基本規範。

## 本地開發環境設定

**需求：** Python 3.10+、[uv](https://github.com/astral-sh/uv)

```bash
# 複製倉庫
git clone https://github.com/<your-fork>/mcp-buy123-vendor.git
cd mcp-buy123-vendor

# 建立虛擬環境並安裝依賴
uv sync --dev
```

## 執行測試

預設測試為**離線**模式，不需要任何 API 憑證：

```bash
pytest tests/test_basic.py -v
```

若需執行需要真實 API 連線的整合測試，請先設定環境變數後再以 opt-in 方式執行：

```bash
# 需要有效的 vendor portal 帳號憑證
pytest tests/test_all_tools.py -v
```

整合測試不在 CI 預設流程中執行。

## Pull Request 規範

- 每個 PR 應聚焦於單一功能或修正
- 提交前請確認離線測試全數通過
- 請在 PR 描述中說明變更動機與影響範圍
- 若涉及新功能，請同步更新相關文件

## ⚠️ 安全與隱私警告

**提交前請務必確認以下事項：**

- **不得**提交任何 API token、密碼、session cookie 或其他憑證
- **不得**提交 `.env` 檔案或任何包含真實憑證的設定檔
- **不得**包含私有廠商 API 文件、內部端點規格或非公開的商業資訊
- **不得**在程式碼、測試或文件中硬編碼任何帳號資訊

若不確定某項資訊是否可公開，請先在 Issue 中討論，再提交 PR。

## 回報問題

請透過 GitHub Issues 回報 bug 或提出功能建議。回報時請提供：

- 重現步驟
- 預期行為與實際行為
- 相關的錯誤訊息（請移除所有憑證資訊）

## 授權

提交貢獻即表示你同意你的貢獻將依本專案的 [LICENSE](LICENSE) 授權條款釋出。
