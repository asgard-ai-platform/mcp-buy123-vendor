"""離線基本測試：不需要任何 API 憑證，預設 pytest 流程即可執行。"""

from __future__ import annotations

import importlib
import os
import sys
import threading
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

# 確保 src/ 在 sys.path 中，讓 mcp_buy123_vendor.* 可解析
import _src_bootstrap  # noqa: F401


# ---------------------------------------------------------------------------
# 輔助：重置 vendor_login 模組內的 in-process token 快取
# ---------------------------------------------------------------------------

def _reset_vendor_login_cache() -> None:
    """將 mcp_buy123_vendor.auth.vendor_login 的 _cache 重置為初始狀態，確保測試間互不干擾。"""
    import mcp_buy123_vendor.auth.vendor_login as vl  # noqa: PLC0415

    with vl._lock:
        vl._cache["access_token"] = None
        vl._cache["refresh_token"] = None
        vl._cache["seeded"] = False


# ===========================================================================
# 1. 模組匯入
# ===========================================================================

class TestModuleImports:
    """驗證核心模組可正常匯入，不需要網路或憑證。"""

    def test_import_common_tools(self) -> None:
        """mcp_buy123_vendor.tools.common_tools 模組應可匯入。"""
        mod = importlib.import_module("mcp_buy123_vendor.tools.common_tools")
        assert mod is not None

    def test_import_auth_tools(self) -> None:
        """mcp_buy123_vendor.tools.auth_tools 模組應可匯入。"""
        mod = importlib.import_module("mcp_buy123_vendor.tools.auth_tools")
        assert mod is not None

    def test_import_rest_client(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 模組應可匯入。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert mod is not None

    def test_import_vendor_login(self) -> None:
        """mcp_buy123_vendor.auth.vendor_login 模組應可匯入。"""
        mod = importlib.import_module("mcp_buy123_vendor.auth.vendor_login")
        assert mod is not None


# ===========================================================================
# 2. rest_client 錯誤處理與重試行為
# ===========================================================================

class TestRestClientErrorHandling:
    """驗證 rest_client 的錯誤處理行為，不發出真實 HTTP 請求。"""

    def test_rest_client_has_api_get(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應具備 api_get 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert callable(getattr(mod, "api_get", None)), (
            "mcp_buy123_vendor.connectors.rest_client 應有 api_get 函式"
        )

    def test_rest_client_has_api_request(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應具備 api_request 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert callable(getattr(mod, "api_request", None))

    def test_rest_client_has_service_api_error(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應匯出 ServiceAPIError 例外類別。"""
        from mcp_buy123_vendor.connectors.rest_client import ServiceAPIError  # noqa: PLC0415

        assert issubclass(ServiceAPIError, Exception)

    def test_service_api_error_attributes(self) -> None:
        """ServiceAPIError 應正確儲存 status_code、message、endpoint。"""
        from mcp_buy123_vendor.connectors.rest_client import ServiceAPIError  # noqa: PLC0415

        err = ServiceAPIError(status_code=404, message="not found", endpoint="items")
        assert err.status_code == 404
        assert err.message == "not found"
        assert err.endpoint == "items"
        assert "404" in str(err)
        assert "items" in str(err)

    def test_api_request_raises_on_4xx(self) -> None:
        """api_request 在收到 4xx 回應時應拋出 ServiceAPIError。"""
        from mcp_buy123_vendor.connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable Entity"

        # patch 目標為 mcp_buy123_vendor.connectors.rest_client 模組命名空間中已綁定的符號
        with (
            patch("requests.request", return_value=mock_response),
            patch("mcp_buy123_vendor.connectors.rest_client.get_headers", return_value={"Content-Type": "application/json"}),
            patch("mcp_buy123_vendor.connectors.rest_client.get_url", return_value="https://example.com/test"),
        ):
            with pytest.raises(ServiceAPIError) as exc_info:
                api_request("GET", "items", require_auth=False)

        assert exc_info.value.status_code == 422

    def test_api_request_returns_json_on_success(self) -> None:
        """api_request 在 2xx 回應時應回傳 response.json() 的結果。"""
        from mcp_buy123_vendor.connectors.rest_client import api_request  # noqa: PLC0415

        expected_payload: dict[str, Any] = {"items": [{"id": 1}], "total": 1}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_payload

        with (
            patch("requests.request", return_value=mock_response),
            patch("mcp_buy123_vendor.connectors.rest_client.get_headers", return_value={"Content-Type": "application/json"}),
            patch("mcp_buy123_vendor.connectors.rest_client.get_url", return_value="https://example.com/test"),
        ):
            result = api_request("GET", "items", require_auth=False)

        assert result == expected_payload

    def test_api_request_retries_on_connection_error(self) -> None:
        """api_request 在 ConnectionError 時應重試，耗盡後拋出 ServiceAPIError。"""
        from mcp_buy123_vendor.connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        sleep_calls: list[float] = []

        with (
            patch(
                "requests.request",
                side_effect=requests.exceptions.ConnectionError("offline"),
            ),
            patch("mcp_buy123_vendor.connectors.rest_client.get_headers", return_value={}),
            patch("mcp_buy123_vendor.connectors.rest_client.get_url", return_value="https://example.com/test"),
            patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)),
        ):
            with pytest.raises(ServiceAPIError) as exc_info:
                api_request("GET", "items", require_auth=False, retries=3)

        # 3 次嘗試 → 前兩次 sleep，最後一次直接拋出
        assert len(sleep_calls) == 2
        assert exc_info.value.status_code == 0
        assert "retries" in exc_info.value.message.lower()

    def test_api_request_retries_on_timeout(self) -> None:
        """api_request 在 Timeout 時應重試，耗盡後拋出 ServiceAPIError。"""
        from mcp_buy123_vendor.connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        with (
            patch(
                "requests.request",
                side_effect=requests.exceptions.Timeout("timed out"),
            ),
            patch("mcp_buy123_vendor.connectors.rest_client.get_headers", return_value={}),
            patch("mcp_buy123_vendor.connectors.rest_client.get_url", return_value="https://example.com/test"),
            patch("time.sleep"),
        ):
            with pytest.raises(ServiceAPIError) as exc_info:
                api_request("GET", "items", require_auth=False, retries=2)

        assert exc_info.value.status_code == 0

    def test_api_request_exponential_backoff_values(self) -> None:
        """重試等待時間應符合指數退避：2^0=1, 2^1=2。"""
        from mcp_buy123_vendor.connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        sleep_calls: list[float] = []

        with (
            patch(
                "requests.request",
                side_effect=requests.exceptions.ConnectionError("offline"),
            ),
            patch("mcp_buy123_vendor.connectors.rest_client.get_headers", return_value={}),
            patch("mcp_buy123_vendor.connectors.rest_client.get_url", return_value="https://example.com/test"),
            patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)),
        ):
            with pytest.raises(ServiceAPIError):
                api_request("GET", "items", require_auth=False, retries=3)

        assert sleep_calls == [1, 2]  # 2^0, 2^1

    def test_api_request_401_triggers_invalidate_and_retries(self) -> None:
        """api_request 在 401 時應：
        1. 呼叫 invalidate_access_token 一次（token 刷新合約）
        2. 重新呼叫 get_headers 取得新 token（header 刷新合約）
        3. 重試請求並以新 token 發出第二次請求
        """
        from mcp_buy123_vendor.connectors.rest_client import api_request  # noqa: PLC0415

        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.text = "Unauthorized"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"ok": True}

        # 模擬 invalidate 後 get_headers 回傳不同（已刷新）的 token
        get_headers_mock = MagicMock(side_effect=[
            {"Authorization": "Bearer old-token"},   # 第一次請求（401 前）
            {"Authorization": "Bearer new-token"},   # 重試請求（invalidate 後）
        ])
        invalidate_mock = MagicMock()

        with (
            patch("requests.request", side_effect=[resp_401, resp_200]) as req_mock,
            patch("mcp_buy123_vendor.connectors.rest_client.get_headers", get_headers_mock),
            patch("mcp_buy123_vendor.connectors.rest_client.get_url", return_value="https://example.com/test"),
            patch("mcp_buy123_vendor.auth.vendor_login.invalidate_access_token", invalidate_mock),
        ):
            result = api_request("GET", "items", require_auth=True, retries=3)

        # 驗證回傳值正確
        assert result == {"ok": True}
        # 驗證 invalidate 被呼叫恰好一次（token 刷新合約）
        invalidate_mock.assert_called_once()
        # 驗證 get_headers 被呼叫兩次：第一次取舊 token，第二次取新 token（header 刷新合約）
        assert get_headers_mock.call_count == 2
        # 驗證兩次 HTTP 請求確實使用了不同的 Authorization header（header 刷新合約）
        assert req_mock.call_count == 2
        first_headers = req_mock.call_args_list[0].kwargs.get("headers", {})
        second_headers = req_mock.call_args_list[1].kwargs.get("headers", {})
        assert first_headers.get("Authorization") != second_headers.get("Authorization"), (
            "重試請求應使用刷新後的 token，而非舊 token"
        )

    def test_missing_token_does_not_crash_import(self) -> None:
        """在無 VENDOR_ACCESS_TOKEN 的情況下，冷匯入 mcp_buy123_vendor.connectors.rest_client 不應拋出例外。

        強化版：
        - 清除 mcp_buy123_vendor.connectors.rest_client 及其直接依賴模組的快取，確保真正冷匯入
        - 在匯入期間封鎖所有網路相關函式，若匯入觸碰網路則測試失敗
        """
        # 匯入期間若觸碰網路應立即失敗
        def _network_forbidden(*args: object, **kwargs: object) -> None:
            raise AssertionError(
                "冷匯入 mcp_buy123_vendor.connectors.rest_client 不應觸發任何網路呼叫"
            )

        env_backup = os.environ.pop("VENDOR_ACCESS_TOKEN", None)

        # 清除 rest_client 及其直接依賴模組的快取，確保頂層程式碼重新執行
        _cold_import_modules = [
            "mcp_buy123_vendor.connectors.rest_client",
            "mcp_buy123_vendor.connectors",
            "mcp_buy123_vendor.config.settings",
            "mcp_buy123_vendor.config",
            "mcp_buy123_vendor.auth.vendor_login",
            "mcp_buy123_vendor.auth",
        ]
        cached_modules: dict[str, object] = {}
        for mod_name in _cold_import_modules:
            cached_modules[mod_name] = sys.modules.pop(mod_name, None)

        try:
            with (
                patch("requests.get", side_effect=_network_forbidden),
                patch("requests.post", side_effect=_network_forbidden),
                patch("requests.request", side_effect=_network_forbidden),
                patch("urllib.request.urlopen", side_effect=_network_forbidden),
            ):
                mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
            assert mod is not None
        finally:
            # 還原所有模組快取，避免影響後續測試
            for mod_name, cached in cached_modules.items():
                if cached is not None:
                    sys.modules[mod_name] = cached  # type: ignore[assignment]
                else:
                    sys.modules.pop(mod_name, None)
            if env_backup is not None:
                os.environ["VENDOR_ACCESS_TOKEN"] = env_backup


# ===========================================================================
# 3. auth token 狀態行為
# ===========================================================================

class TestAuthTokenState:
    """驗證 mcp_buy123_vendor.auth.vendor_login 的 token 快取與狀態邏輯，完全離線。"""

    def setup_method(self) -> None:
        """每個測試前重置快取，確保測試隔離。"""
        _reset_vendor_login_cache()

    def teardown_method(self) -> None:
        """每個測試後清理快取與環境變數。"""
        _reset_vendor_login_cache()
        os.environ.pop("VENDOR_ACCESS_TOKEN", None)
        os.environ.pop("VENDOR_REFRESH_TOKEN", None)

    def test_is_authenticated_false_when_no_token(self) -> None:
        """無 token 時 is_authenticated() 應回傳 False。"""
        from mcp_buy123_vendor.auth.vendor_login import is_authenticated  # noqa: PLC0415

        os.environ.pop("VENDOR_ACCESS_TOKEN", None)
        assert is_authenticated() is False

    def test_is_authenticated_true_when_env_token_set(self) -> None:
        """設定 VENDOR_ACCESS_TOKEN 環境變數後 is_authenticated() 應回傳 True。"""
        from mcp_buy123_vendor.auth.vendor_login import is_authenticated  # noqa: PLC0415

        os.environ["VENDOR_ACCESS_TOKEN"] = "test-token-abc"
        assert is_authenticated() is True

    def test_set_tokens_from_login_updates_cache(self) -> None:
        """set_tokens_from_login 應更新快取並使 is_authenticated() 回傳 True。"""
        from mcp_buy123_vendor.auth.vendor_login import is_authenticated, set_tokens_from_login  # noqa: PLC0415

        assert is_authenticated() is False
        set_tokens_from_login("new-access-token", "new-refresh-token")
        assert is_authenticated() is True

    def test_get_auth_headers_raises_when_no_token(self) -> None:
        """無 token 時 get_auth_headers() 應拋出 VendorAuthError。"""
        from mcp_buy123_vendor.auth.vendor_login import VendorAuthError, get_auth_headers  # noqa: PLC0415

        os.environ.pop("VENDOR_ACCESS_TOKEN", None)
        with pytest.raises(VendorAuthError):
            get_auth_headers()

    def test_get_auth_headers_returns_bearer_token(self) -> None:
        """有 token 時 get_auth_headers() 應回傳含 Authorization Bearer 的 dict。"""
        from mcp_buy123_vendor.auth.vendor_login import get_auth_headers, set_tokens_from_login  # noqa: PLC0415

        set_tokens_from_login("my-secret-token", None)
        headers = get_auth_headers()
        assert headers.get("Authorization") == "Bearer my-secret-token"

    def test_invalidate_access_token_raises_when_no_refresh(self) -> None:
        """無 refresh_token 時 invalidate_access_token() 應拋出 VendorAuthError。"""
        from mcp_buy123_vendor.auth.vendor_login import VendorAuthError, invalidate_access_token  # noqa: PLC0415

        # 設定 access token 但不設 refresh token
        os.environ["VENDOR_ACCESS_TOKEN"] = "some-token"
        os.environ.pop("VENDOR_REFRESH_TOKEN", None)

        with pytest.raises(VendorAuthError) as exc_info:
            invalidate_access_token()

        assert "refresh" in str(exc_info.value).lower()

    def test_invalidate_access_token_refreshes_on_success(self) -> None:
        """invalidate_access_token 在 refresh API 成功時應更新快取中的 access_token。"""
        from mcp_buy123_vendor.auth.vendor_login import (  # noqa: PLC0415
            get_auth_headers,
            invalidate_access_token,
            set_tokens_from_login,
        )

        set_tokens_from_login("old-access", "valid-refresh")

        refresh_response = MagicMock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            "success": True,
            "data": {"access_token": "new-access", "refresh_token": "new-refresh"},
        }

        with (
            patch("requests.post", return_value=refresh_response),
            patch("mcp_buy123_vendor.auth.vendor_login._persist_env"),  # 避免寫入 .env 檔案
        ):
            invalidate_access_token()

        headers = get_auth_headers()
        assert headers["Authorization"] == "Bearer new-access"

    def test_invalidate_access_token_raises_when_refresh_api_fails(self) -> None:
        """refresh API 回傳非 200 時 invalidate_access_token 應拋出 VendorAuthError。"""
        from mcp_buy123_vendor.auth.vendor_login import VendorAuthError, invalidate_access_token, set_tokens_from_login  # noqa: PLC0415

        set_tokens_from_login("old-access", "expired-refresh")

        fail_response = MagicMock()
        fail_response.status_code = 401
        fail_response.json.return_value = {"success": False}

        with patch("requests.post", return_value=fail_response):
            with pytest.raises(VendorAuthError):
                invalidate_access_token()

    def test_cache_seeded_only_once_from_env(self) -> None:
        """_seed_from_env_locked 應只執行一次（seeded flag 防止重複讀取）。"""
        import mcp_buy123_vendor.auth.vendor_login as vl  # noqa: PLC0415

        os.environ["VENDOR_ACCESS_TOKEN"] = "initial-token"
        # 第一次呼叫 is_authenticated 觸發 seed
        assert vl.is_authenticated() is True

        # 修改環境變數後，快取不應再更新（seeded=True）
        os.environ["VENDOR_ACCESS_TOKEN"] = "changed-token"
        assert vl.is_authenticated() is True
        with vl._lock:
            assert vl._cache["access_token"] == "initial-token"

    def test_thread_safety_set_tokens(self) -> None:
        """set_tokens_from_login 在多執行緒環境下不應拋出例外。"""
        from mcp_buy123_vendor.auth.vendor_login import is_authenticated, set_tokens_from_login  # noqa: PLC0415

        errors: list[Exception] = []

        def worker(token: str) -> None:
            try:
                set_tokens_from_login(token, None)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(f"tok-{i}",)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert is_authenticated() is True


# ===========================================================================
# 4. 工具函式註冊 / 核心可用性
# ===========================================================================

class TestToolRegistration:
    """驗證工具函式已正確定義於各 tools 模組中。"""

    def test_common_tools_has_list_banks(self) -> None:
        """mcp_buy123_vendor.tools.common_tools 應匯出 list_banks 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.tools.common_tools")
        assert callable(getattr(mod, "list_banks", None)), (
            "mcp_buy123_vendor.tools.common_tools.list_banks 應為可呼叫函式"
        )

    def test_common_tools_has_list_delivery_types(self) -> None:
        """mcp_buy123_vendor.tools.common_tools 應匯出 list_delivery_types 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.tools.common_tools")
        assert callable(getattr(mod, "list_delivery_types", None)), (
            "mcp_buy123_vendor.tools.common_tools.list_delivery_types 應為可呼叫函式"
        )

    def test_auth_tools_has_get_current_user(self) -> None:
        """mcp_buy123_vendor.tools.auth_tools 應匯出 get_current_user 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.tools.auth_tools")
        assert callable(getattr(mod, "get_current_user", None)), (
            "mcp_buy123_vendor.tools.auth_tools.get_current_user 應為可呼叫函式"
        )

    def test_rest_client_has_api_post(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應匯出 api_post 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert callable(getattr(mod, "api_post", None))

    def test_rest_client_has_api_put(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應匯出 api_put 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert callable(getattr(mod, "api_put", None))

    def test_rest_client_has_api_delete(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應匯出 api_delete 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert callable(getattr(mod, "api_delete", None))

    def test_rest_client_has_fetch_all_pages(self) -> None:
        """mcp_buy123_vendor.connectors.rest_client 應匯出 fetch_all_pages 函式。"""
        mod = importlib.import_module("mcp_buy123_vendor.connectors.rest_client")
        assert callable(getattr(mod, "fetch_all_pages", None))

    def test_vendor_login_exports_expected_symbols(self) -> None:
        """mcp_buy123_vendor.auth.vendor_login 應匯出所有必要的公開函式與例外。"""
        mod = importlib.import_module("mcp_buy123_vendor.auth.vendor_login")
        expected_symbols = [
            "VendorAuthError",
            "is_authenticated",
            "get_auth_headers",
            "set_tokens_from_login",
            "invalidate_access_token",
        ]
        for sym in expected_symbols:
            assert hasattr(mod, sym), f"mcp_buy123_vendor.auth.vendor_login 缺少 {sym}"


# ===========================================================================
# 5. config/settings.py 常數重新匯出與 helper 行為
# ===========================================================================

class TestConfigSettings:
    """驗證 mcp_buy123_vendor.config.settings 的常數重新匯出與 get_url / get_headers 行為，完全離線。"""

    def test_settings_re_exports_base_url(self) -> None:
        """mcp_buy123_vendor.config.settings 應重新匯出 BASE_URL 常數。"""
        from mcp_buy123_vendor.config.settings import BASE_URL  # noqa: PLC0415

        assert isinstance(BASE_URL, str)
        assert BASE_URL.startswith("https://")

    def test_settings_re_exports_api_version(self) -> None:
        """mcp_buy123_vendor.config.settings 應重新匯出 API_VERSION 常數。"""
        from mcp_buy123_vendor.config.settings import API_VERSION  # noqa: PLC0415

        assert isinstance(API_VERSION, str)
        assert len(API_VERSION) > 0

    def test_settings_re_exports_default_per_page(self) -> None:
        """mcp_buy123_vendor.config.settings 應重新匯出 DEFAULT_PER_PAGE 常數，且為正整數。"""
        from mcp_buy123_vendor.config.settings import DEFAULT_PER_PAGE  # noqa: PLC0415

        assert isinstance(DEFAULT_PER_PAGE, int)
        assert DEFAULT_PER_PAGE > 0

    def test_settings_re_exports_frontend_url(self) -> None:
        """mcp_buy123_vendor.config.settings 應重新匯出 FRONTEND_URL 常數。"""
        from mcp_buy123_vendor.config.settings import FRONTEND_URL  # noqa: PLC0415

        assert isinstance(FRONTEND_URL, str)
        assert len(FRONTEND_URL) > 0

    def test_settings_exports_endpoints_dict(self) -> None:
        """mcp_buy123_vendor.config.settings 應匯出 ENDPOINTS dict，且包含常用端點鍵。"""
        from mcp_buy123_vendor.config.settings import ENDPOINTS  # noqa: PLC0415

        assert isinstance(ENDPOINTS, dict)
        for key in ("me", "items", "products", "common_banks"):
            assert key in ENDPOINTS, f"ENDPOINTS 缺少鍵 '{key}'"

    def test_get_url_no_path_params(self) -> None:
        """get_url 在無路徑參數時應回傳完整的 BASE_URL + 版本化路徑。"""
        from mcp_buy123_vendor.config.settings import API_VERSION, BASE_URL, get_url  # noqa: PLC0415

        url = get_url("items")
        expected = f"{BASE_URL}/{API_VERSION}/items"
        assert url == expected, f"期望完整 URL '{expected}'，實際得到 '{url}'"

    def test_get_url_with_path_params(self) -> None:
        """get_url 在有路徑參數時應回傳完整展開後的 URL。"""
        from mcp_buy123_vendor.config.settings import API_VERSION, BASE_URL, get_url  # noqa: PLC0415

        url = get_url("item_detail", id=42)
        expected = f"{BASE_URL}/{API_VERSION}/items/42"
        assert url == expected, f"期望完整 URL '{expected}'，實際得到 '{url}'"
        assert "{id}" not in url

    def test_get_url_with_multiple_path_params(self) -> None:
        """get_url 應回傳完整展開多個路徑參數後的 URL。"""
        from mcp_buy123_vendor.config.settings import API_VERSION, BASE_URL, get_url  # noqa: PLC0415

        url = get_url("bundle_item_detail", bundle_id=10, item_id=99)
        expected = f"{BASE_URL}/{API_VERSION}/bundles/10/items/99"
        assert url == expected, f"期望完整 URL '{expected}'，實際得到 '{url}'"
        assert "{bundle_id}" not in url
        assert "{item_id}" not in url

    def test_get_url_unknown_key_raises(self) -> None:
        """get_url 傳入不存在的 endpoint_key 應拋出 KeyError。"""
        from mcp_buy123_vendor.config.settings import get_url  # noqa: PLC0415

        with pytest.raises(KeyError):
            get_url("__nonexistent_endpoint__")

    def test_get_url_missing_required_path_param_raises(self) -> None:
        """get_url 在格式化端點缺少必要路徑參數時應拋出 KeyError。

        bundle_item_detail 端點路徑為 /{API_VERSION}/bundles/{bundle_id}/items/{item_id}，
        僅提供 bundle_id 而缺少 item_id 時，kwargs 非空會觸發 str.format()，
        因此應拋出 KeyError。
        """
        from mcp_buy123_vendor.config.settings import get_url  # noqa: PLC0415

        with pytest.raises(KeyError):
            get_url("bundle_item_detail", bundle_id=10)  # 缺少必要的 item_id 路徑參數

    def test_get_headers_no_auth_omits_authorization(self) -> None:
        """get_headers(require_auth=False) 不應包含 Authorization 標頭。"""
        from mcp_buy123_vendor.config.settings import get_headers  # noqa: PLC0415

        headers = get_headers(require_auth=False)
        assert "Authorization" not in headers
        assert headers.get("Content-Type") == "application/json"
        assert headers.get("Accept") == "application/json"

    def test_get_headers_with_auth_merges_authorization(self) -> None:
        """get_headers(require_auth=True) 應合併 get_auth_headers() 的 Authorization 標頭。"""
        from mcp_buy123_vendor.config.settings import get_headers  # noqa: PLC0415

        fake_auth = {"Authorization": "Bearer test-token-xyz"}
        with patch("mcp_buy123_vendor.config.settings.get_auth_headers", return_value=fake_auth):
            headers = get_headers(require_auth=True)

        assert headers.get("Authorization") == "Bearer test-token-xyz"
        assert headers.get("Content-Type") == "application/json"

    def test_get_headers_default_requires_auth(self) -> None:
        """get_headers() 預設 require_auth=True，應呼叫 get_auth_headers()。"""
        from mcp_buy123_vendor.config.settings import get_headers  # noqa: PLC0415

        fake_auth = {"Authorization": "Bearer default-token"}
        with patch("mcp_buy123_vendor.config.settings.get_auth_headers", return_value=fake_auth) as mock_auth:
            headers = get_headers()

        mock_auth.assert_called_once()
        assert "Authorization" in headers

    def test_get_url_no_kwargs_returns_unresolved_placeholder(self) -> None:
        """【現行行為保護】get_url 在格式化端點（如 item_detail）未傳入 kwargs 時，
        不拋出例外，而是回傳含有未展開佔位符的字串（例如 '{id}'）。

        此測試記錄當前實作的行為：kwargs 為空時 path.format() 不被呼叫，
        因此 {id} 原樣保留在回傳的 URL 中。
        若未來決定改為拋出例外，此測試應同步更新。
        """
        from mcp_buy123_vendor.config.settings import BASE_URL, get_url  # noqa: PLC0415

        url = get_url("item_detail")  # 刻意不傳 id=...
        # 不應拋出例外
        assert isinstance(url, str)
        # 回傳值應以 BASE_URL 開頭
        assert url.startswith(BASE_URL)
        # 佔位符 {id} 應原樣保留（未展開）
        assert "{id}" in url, (
            f"現行行為：無 kwargs 時 get_url('item_detail') 應保留 '{{id}}' 佔位符，"
            f"實際得到 '{url}'"
        )


# ===========================================================================
# 6. rest_client 分頁行為
# ===========================================================================

class TestRestClientPagination:
    """驗證 rest_client 的分頁輔助函式行為，完全離線（patch api_get）。"""

    # -----------------------------------------------------------------------
    # fetch_all_pages
    # -----------------------------------------------------------------------

    def test_fetch_all_pages_stops_on_empty_page(self) -> None:
        """fetch_all_pages 在收到空 items 時應立即停止並回傳已累積的資料。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages  # noqa: PLC0415

        # 第一頁有資料，第二頁空
        pages = [
            {"items": [{"id": 1}, {"id": 2}]},
            {"items": []},
        ]
        # 每次呼叫時複製 params 快照，避免可變 dict 共用造成假陽性
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> dict:
            captured_params.append(dict(kwargs.get("params", {})))
            return pages[len(captured_params) - 1]

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=_capture_and_return),
            patch("time.sleep"),
        ):
            result = fetch_all_pages("items")

        assert result == [{"id": 1}, {"id": 2}]
        # 驗證第一次呼叫帶入 page=1（快照值，不受後續 mutation 影響）
        assert captured_params[0].get("page") == 1, "第一頁請求應帶 page=1"
        # 驗證第二次呼叫帶入 page=2（快照值）
        assert captured_params[1].get("page") == 2, "第二頁請求應帶 page=2"

    def test_fetch_all_pages_stops_on_short_page(self) -> None:
        """fetch_all_pages 在 items 數量 < per_page 時應停止（最後一頁）。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages  # noqa: PLC0415

        # per_page 預設 50，回傳 3 筆 → 短頁，應停止
        pages = [{"items": [{"id": i} for i in range(3)]}]
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> dict:
            captured_params.append(dict(kwargs.get("params", {})))
            return pages[len(captured_params) - 1]

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=_capture_and_return),
            patch("time.sleep"),
        ):
            result = fetch_all_pages("items")

        assert len(result) == 3
        # 驗證帶入了 page=1 與預設 per_page=50（快照值）
        assert captured_params[0].get("page") == 1, "應帶 page=1"
        assert captured_params[0].get("per_page") == 50, "應帶預設 per_page=50"

    def test_fetch_all_pages_accumulates_multiple_pages(self) -> None:
        """fetch_all_pages 應跨多頁累積所有 items，且每頁帶入遞增的 page 參數。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages  # noqa: PLC0415

        per_page = 2
        pages = [
            {"items": [{"id": 1}, {"id": 2}]},
            {"items": [{"id": 3}, {"id": 4}]},
            {"items": [{"id": 5}]},  # 短頁，停止
        ]
        # 每次呼叫時複製 params 快照，避免可變 dict 共用造成假陽性
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> dict:
            captured_params.append(dict(kwargs.get("params", {})))
            return pages[len(captured_params) - 1]

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=_capture_and_return),
            patch("time.sleep"),
        ):
            result = fetch_all_pages("items", params={"per_page": per_page})

        assert [item["id"] for item in result] == [1, 2, 3, 4, 5]
        # 驗證三次呼叫的 page 參數依序遞增（快照值，不受後續 mutation 影響）
        for expected_page, snap in enumerate(captured_params, start=1):
            assert snap.get("page") == expected_page, (
                f"第 {expected_page} 次呼叫應帶 page={expected_page}，"
                f"實際得到 page={snap.get('page')}"
            )
            assert snap.get("per_page") == per_page, (
                f"第 {expected_page} 次呼叫應帶 per_page={per_page}"
            )

    def test_fetch_all_pages_respects_max_pages(self) -> None:
        """fetch_all_pages 在達到 max_pages 時應停止，不繼續請求。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages  # noqa: PLC0415

        # 每頁都是滿頁（per_page=2），但 max_pages=2 → 只取 2 頁
        full_page = {"items": [{"id": 1}, {"id": 2}]}
        # 每次呼叫時複製 params 快照，避免可變 dict 共用造成假陽性
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> dict:
            captured_params.append(dict(kwargs.get("params", {})))
            return full_page

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=_capture_and_return),
            patch("time.sleep"),
        ):
            result = fetch_all_pages("items", params={"per_page": 2}, max_pages=2)

        assert len(captured_params) == 2
        assert len(result) == 4
        # 驗證兩次呼叫的 page 參數分別為 1 和 2（快照值）
        assert captured_params[0].get("page") == 1, "第一次呼叫應帶 page=1"
        assert captured_params[1].get("page") == 2, "第二次呼叫應帶 page=2"
        assert captured_params[0].get("per_page") == 2, "應帶 per_page=2"
        assert captured_params[1].get("per_page") == 2, "應帶 per_page=2"

    def test_fetch_all_pages_custom_items_key(self) -> None:
        """fetch_all_pages 應支援自訂 items_key 參數。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages  # noqa: PLC0415

        pages = [{"data": [{"id": 10}]}]
        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=pages),
            patch("time.sleep"),
        ):
            result = fetch_all_pages("items", items_key="data")

        assert result == [{"id": 10}]

    def test_fetch_all_pages_sleeps_between_pages(self) -> None:
        """fetch_all_pages 在多頁之間應呼叫 time.sleep 進行速率限制。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages  # noqa: PLC0415

        # per_page=2：第 1 頁滿頁（2 筆）→ sleep；第 2 頁短頁（1 筆）→ 停止，不 sleep
        per_page = 2
        pages = [
            {"items": [{"id": 1}, {"id": 2}]},  # 滿頁，繼續並 sleep
            {"items": [{"id": 3}]},              # 短頁，停止，不 sleep
        ]
        sleep_calls: list[float] = []

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=pages),
            patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)),
        ):
            fetch_all_pages("items", params={"per_page": per_page}, rate_limit_delay=0.5)

        # 第 1 頁後 sleep，第 2 頁是短頁（停止）不 sleep → 共 1 次
        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 0.5

    # -----------------------------------------------------------------------
    # fetch_all_pages_cursor
    # -----------------------------------------------------------------------

    def test_fetch_all_pages_cursor_follows_next_cursor(self) -> None:
        """fetch_all_pages_cursor 應依序跟隨 next_cursor 直到耗盡。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_cursor  # noqa: PLC0415

        pages = [
            {"items": [{"id": 1}], "next_cursor": "cursor-abc"},
            {"items": [{"id": 2}], "next_cursor": "cursor-def"},
            {"items": [{"id": 3}], "next_cursor": None},
        ]
        # 每次呼叫時複製 params 快照，避免可變 dict 共用造成假陽性
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> dict:
            captured_params.append(dict(kwargs.get("params", {})))
            return pages[len(captured_params) - 1]

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=_capture_and_return),
            patch("time.sleep"),
        ):
            result = fetch_all_pages_cursor("items")

        assert [item["id"] for item in result] == [1, 2, 3]
        # 驗證第一次呼叫不帶 cursor（快照值）
        assert "cursor" not in captured_params[0], "第一次呼叫不應帶 cursor 參數"
        # 驗證第二次呼叫帶入了第一頁回傳的 cursor（快照值，不受後續 mutation 影響）
        assert captured_params[1].get("cursor") == "cursor-abc", (
            "第二次呼叫應帶 cursor=cursor-abc"
        )
        # 驗證第三次呼叫帶入了第二頁回傳的 cursor（快照值）
        assert captured_params[2].get("cursor") == "cursor-def", (
            "第三次呼叫應帶 cursor=cursor-def"
        )

    def test_fetch_all_pages_cursor_stops_when_no_cursor(self) -> None:
        """fetch_all_pages_cursor 在 next_cursor 為 None/空時應停止。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_cursor  # noqa: PLC0415

        pages = [
            {"items": [{"id": 1}, {"id": 2}], "next_cursor": None},
        ]
        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=pages),
            patch("time.sleep"),
        ):
            result = fetch_all_pages_cursor("items")

        assert len(result) == 2

    def test_fetch_all_pages_cursor_stops_when_items_empty(self) -> None:
        """fetch_all_pages_cursor 在 items 為空時應停止，即使有 next_cursor。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_cursor  # noqa: PLC0415

        pages = [
            {"items": [], "next_cursor": "some-cursor"},
        ]
        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=pages),
            patch("time.sleep"),
        ):
            result = fetch_all_pages_cursor("items")

        assert result == []

    def test_fetch_all_pages_cursor_custom_keys(self) -> None:
        """fetch_all_pages_cursor 應支援自訂 cursor_key 與 cursor_param。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_cursor  # noqa: PLC0415

        pages = [
            {"records": [{"id": 7}], "page_token": "tok-1"},
            {"records": [{"id": 8}], "page_token": None},
        ]
        # 每次呼叫時複製 params 快照，避免可變 dict 共用造成假陽性
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> dict:
            captured_params.append(dict(kwargs.get("params", {})))
            return pages[len(captured_params) - 1]

        with (
            patch("mcp_buy123_vendor.connectors.rest_client.api_get", side_effect=_capture_and_return),
            patch("time.sleep"),
        ):
            result = fetch_all_pages_cursor(
                "items",
                items_key="records",
                cursor_key="page_token",
                cursor_param="page_token",
            )

        assert [item["id"] for item in result] == [7, 8]
        # 驗證第二次呼叫帶入了自訂 cursor_param（快照值，不受後續 mutation 影響）
        assert captured_params[1].get("page_token") == "tok-1", (
            "第二次呼叫應帶 page_token=tok-1"
        )

    # -----------------------------------------------------------------------
    # fetch_all_pages_by_date_segments
    # -----------------------------------------------------------------------

    def test_fetch_all_pages_by_date_segments_splits_range(self) -> None:
        """fetch_all_pages_by_date_segments 應依 segment_days 切分日期範圍並委派給 fetch_all_pages。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_by_date_segments  # noqa: PLC0415

        # 60 天範圍，segment_days=30 → 應呼叫 fetch_all_pages 兩次
        # 實作會 mutate 同一個 params dict，因此用 side_effect 在呼叫時複製快照
        segment_results = [
            [{"id": 1}, {"id": 2}],
            [{"id": 3}],
        ]
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> list:
            captured_params.append(dict(kwargs.get("params", {})))
            return segment_results[len(captured_params) - 1]

        with patch("mcp_buy123_vendor.connectors.rest_client.fetch_all_pages", side_effect=_capture_and_return):
            result = fetch_all_pages_by_date_segments(
                "items",
                start_date="2024-01-01",
                end_date="2024-03-01",
                segment_days=30,
            )

        assert len(captured_params) == 2
        assert [item["id"] for item in result] == [1, 2, 3]
        # 第一段：2024-01-01 → 2024-01-31
        assert captured_params[0].get("created_after") == "2024-01-01"
        assert captured_params[0].get("created_before") == "2024-01-31"
        # 第二段：2024-01-31 → 2024-03-01
        assert captured_params[1].get("created_after") == "2024-01-31"
        assert captured_params[1].get("created_before") == "2024-03-01"

    def test_fetch_all_pages_by_date_segments_passes_date_params(self) -> None:
        """fetch_all_pages_by_date_segments 應將正確的日期區間傳入 fetch_all_pages。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_by_date_segments  # noqa: PLC0415

        # 實作會 mutate 同一個 params dict，因此用 side_effect 在呼叫時複製快照
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> list:
            captured_params.append(dict(kwargs.get("params", {})))
            return []

        with patch("mcp_buy123_vendor.connectors.rest_client.fetch_all_pages", side_effect=_capture_and_return):
            fetch_all_pages_by_date_segments(
                "items",
                start_date="2024-01-01",
                end_date="2024-02-01",
                segment_days=31,
            )

        # 只有一個區間（31 天 >= 31 天範圍）
        assert len(captured_params) == 1
        # 快照值確保不受後續 mutation 影響
        assert captured_params[0].get("created_after") == "2024-01-01"
        assert captured_params[0].get("created_before") == "2024-02-01"

    def test_fetch_all_pages_by_date_segments_custom_date_params(self) -> None:
        """fetch_all_pages_by_date_segments 應支援自訂 date_start_param / date_end_param。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_by_date_segments  # noqa: PLC0415

        # 實作會 mutate 同一個 params dict，因此用 side_effect 在呼叫時複製快照
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> list:
            captured_params.append(dict(kwargs.get("params", {})))
            return [{"id": 99}]

        with patch("mcp_buy123_vendor.connectors.rest_client.fetch_all_pages", side_effect=_capture_and_return):
            result = fetch_all_pages_by_date_segments(
                "items",
                start_date="2024-06-01",
                end_date="2024-07-01",
                segment_days=30,
                date_start_param="from_date",
                date_end_param="to_date",
            )

        assert len(captured_params) == 1
        # 快照值確保不受後續 mutation 影響
        assert captured_params[0].get("from_date") == "2024-06-01"
        assert captured_params[0].get("to_date") == "2024-07-01"
        assert "created_after" not in captured_params[0], "不應使用預設 created_after 鍵"
        assert "created_before" not in captured_params[0], "不應使用預設 created_before 鍵"
        assert result == [{"id": 99}]

    def test_fetch_all_pages_by_date_segments_accumulates_all_segments(self) -> None:
        """fetch_all_pages_by_date_segments 應累積所有區間的結果，且每段日期邊界正確。"""
        from mcp_buy123_vendor.connectors.rest_client import fetch_all_pages_by_date_segments  # noqa: PLC0415

        # 2024-01-01 到 2024-04-01，每 30 天一段 → 實際產生 4 段：
        #   2024-01-01 → 2024-01-31
        #   2024-01-31 → 2024-03-01
        #   2024-03-01 → 2024-03-31
        #   2024-03-31 → 2024-04-01
        # 實作會 mutate 同一個 params dict，因此用 side_effect 在呼叫時複製快照
        segment_results = [
            [{"id": 1}],
            [{"id": 2}],
            [{"id": 3}],
            [{"id": 4}],
        ]
        captured_params: list[dict] = []

        def _capture_and_return(*args: object, **kwargs: object) -> list:
            captured_params.append(dict(kwargs.get("params", {})))
            return segment_results[len(captured_params) - 1]

        with patch("mcp_buy123_vendor.connectors.rest_client.fetch_all_pages", side_effect=_capture_and_return):
            result = fetch_all_pages_by_date_segments(
                "items",
                start_date="2024-01-01",
                end_date="2024-04-01",
                segment_days=30,
            )

        assert len(captured_params) == 4
        assert [item["id"] for item in result] == [1, 2, 3, 4]
        # 驗證每段的精確日期邊界（快照值，不受後續 mutation 影響）
        assert captured_params[0].get("created_after") == "2024-01-01"
        assert captured_params[0].get("created_before") == "2024-01-31"
        assert captured_params[1].get("created_after") == "2024-01-31"
        assert captured_params[1].get("created_before") == "2024-03-01"
        assert captured_params[2].get("created_after") == "2024-03-01"
        assert captured_params[2].get("created_before") == "2024-03-31"
        assert captured_params[3].get("created_after") == "2024-03-31"
        assert captured_params[3].get("created_before") == "2024-04-01"
