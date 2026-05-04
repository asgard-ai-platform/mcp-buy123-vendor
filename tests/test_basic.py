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

# 確保專案根目錄在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# 輔助：重置 vendor_login 模組內的 in-process token 快取
# ---------------------------------------------------------------------------

def _reset_vendor_login_cache() -> None:
    """將 auth.vendor_login 的 _cache 重置為初始狀態，確保測試間互不干擾。"""
    import auth.vendor_login as vl  # noqa: PLC0415

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
        """common_tools 模組應可匯入。"""
        mod = importlib.import_module("tools.common_tools")
        assert mod is not None

    def test_import_auth_tools(self) -> None:
        """auth_tools 模組應可匯入。"""
        mod = importlib.import_module("tools.auth_tools")
        assert mod is not None

    def test_import_rest_client(self) -> None:
        """rest_client 模組應可匯入。"""
        mod = importlib.import_module("connectors.rest_client")
        assert mod is not None

    def test_import_vendor_login(self) -> None:
        """auth.vendor_login 模組應可匯入。"""
        mod = importlib.import_module("auth.vendor_login")
        assert mod is not None


# ===========================================================================
# 2. rest_client 錯誤處理與重試行為
# ===========================================================================

class TestRestClientErrorHandling:
    """驗證 rest_client 的錯誤處理行為，不發出真實 HTTP 請求。"""

    def test_rest_client_has_api_get(self) -> None:
        """connectors.rest_client 應具備 api_get 函式。"""
        mod = importlib.import_module("connectors.rest_client")
        assert callable(getattr(mod, "api_get", None)), (
            "connectors.rest_client 應有 api_get 函式"
        )

    def test_rest_client_has_api_request(self) -> None:
        """connectors.rest_client 應具備 api_request 函式。"""
        mod = importlib.import_module("connectors.rest_client")
        assert callable(getattr(mod, "api_request", None))

    def test_rest_client_has_service_api_error(self) -> None:
        """connectors.rest_client 應匯出 ServiceAPIError 例外類別。"""
        from connectors.rest_client import ServiceAPIError  # noqa: PLC0415

        assert issubclass(ServiceAPIError, Exception)

    def test_service_api_error_attributes(self) -> None:
        """ServiceAPIError 應正確儲存 status_code、message、endpoint。"""
        from connectors.rest_client import ServiceAPIError  # noqa: PLC0415

        err = ServiceAPIError(status_code=404, message="not found", endpoint="items")
        assert err.status_code == 404
        assert err.message == "not found"
        assert err.endpoint == "items"
        assert "404" in str(err)
        assert "items" in str(err)

    def test_api_request_raises_on_4xx(self) -> None:
        """api_request 在收到 4xx 回應時應拋出 ServiceAPIError。"""
        from connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable Entity"

        # patch 目標為 connectors.rest_client 模組命名空間中已綁定的符號
        # （rest_client 使用 `from config.settings import get_headers, get_url`）
        with (
            patch("requests.request", return_value=mock_response),
            patch("connectors.rest_client.get_headers", return_value={"Content-Type": "application/json"}),
            patch("connectors.rest_client.get_url", return_value="https://example.com/test"),
        ):
            with pytest.raises(ServiceAPIError) as exc_info:
                api_request("GET", "items", require_auth=False)

        assert exc_info.value.status_code == 422

    def test_api_request_returns_json_on_success(self) -> None:
        """api_request 在 2xx 回應時應回傳 response.json() 的結果。"""
        from connectors.rest_client import api_request  # noqa: PLC0415

        expected_payload: dict[str, Any] = {"items": [{"id": 1}], "total": 1}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_payload

        with (
            patch("requests.request", return_value=mock_response),
            patch("connectors.rest_client.get_headers", return_value={"Content-Type": "application/json"}),
            patch("connectors.rest_client.get_url", return_value="https://example.com/test"),
        ):
            result = api_request("GET", "items", require_auth=False)

        assert result == expected_payload

    def test_api_request_retries_on_connection_error(self) -> None:
        """api_request 在 ConnectionError 時應重試，耗盡後拋出 ServiceAPIError。"""
        from connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        sleep_calls: list[float] = []

        with (
            patch(
                "requests.request",
                side_effect=requests.exceptions.ConnectionError("offline"),
            ),
            patch("connectors.rest_client.get_headers", return_value={}),
            patch("connectors.rest_client.get_url", return_value="https://example.com/test"),
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
        from connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        with (
            patch(
                "requests.request",
                side_effect=requests.exceptions.Timeout("timed out"),
            ),
            patch("connectors.rest_client.get_headers", return_value={}),
            patch("connectors.rest_client.get_url", return_value="https://example.com/test"),
            patch("time.sleep"),
        ):
            with pytest.raises(ServiceAPIError) as exc_info:
                api_request("GET", "items", require_auth=False, retries=2)

        assert exc_info.value.status_code == 0

    def test_api_request_exponential_backoff_values(self) -> None:
        """重試等待時間應符合指數退避：2^0=1, 2^1=2。"""
        from connectors.rest_client import ServiceAPIError, api_request  # noqa: PLC0415

        sleep_calls: list[float] = []

        with (
            patch(
                "requests.request",
                side_effect=requests.exceptions.ConnectionError("offline"),
            ),
            patch("connectors.rest_client.get_headers", return_value={}),
            patch("connectors.rest_client.get_url", return_value="https://example.com/test"),
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
        from connectors.rest_client import api_request  # noqa: PLC0415

        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.text = "Unauthorized"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"ok": True}

        # 模擬 invalidate 後 get_headers 回傳不同（已刷新）的 token
        # patch 目標為 connectors.rest_client 命名空間中已綁定的 get_headers 符號
        get_headers_mock = MagicMock(side_effect=[
            {"Authorization": "Bearer old-token"},   # 第一次請求（401 前）
            {"Authorization": "Bearer new-token"},   # 重試請求（invalidate 後）
        ])
        invalidate_mock = MagicMock()

        with (
            patch("requests.request", side_effect=[resp_401, resp_200]) as req_mock,
            patch("connectors.rest_client.get_headers", get_headers_mock),
            patch("connectors.rest_client.get_url", return_value="https://example.com/test"),
            patch("auth.vendor_login.invalidate_access_token", invalidate_mock),
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
        """在無 VENDOR_ACCESS_TOKEN 的情況下，冷匯入 connectors.rest_client 不應拋出例外。

        強化版：
        - 清除 connectors.rest_client 及其直接依賴模組的快取，確保真正冷匯入
        - 在匯入期間封鎖所有網路相關函式，若匯入觸碰網路則測試失敗
        """
        # 匯入期間若觸碰網路應立即失敗
        def _network_forbidden(*args: object, **kwargs: object) -> None:
            raise AssertionError(
                "冷匯入 connectors.rest_client 不應觸發任何網路呼叫"
            )

        env_backup = os.environ.pop("VENDOR_ACCESS_TOKEN", None)

        # 清除 rest_client 及其直接依賴模組的快取，確保頂層程式碼重新執行
        _cold_import_modules = [
            "connectors.rest_client",
            "connectors",
            "config.settings",
            "config",
            "auth.vendor_login",
            "auth",
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
                mod = importlib.import_module("connectors.rest_client")
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
    """驗證 auth.vendor_login 的 token 快取與狀態邏輯，完全離線。"""

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
        from auth.vendor_login import is_authenticated  # noqa: PLC0415

        os.environ.pop("VENDOR_ACCESS_TOKEN", None)
        assert is_authenticated() is False

    def test_is_authenticated_true_when_env_token_set(self) -> None:
        """設定 VENDOR_ACCESS_TOKEN 環境變數後 is_authenticated() 應回傳 True。"""
        from auth.vendor_login import is_authenticated  # noqa: PLC0415

        os.environ["VENDOR_ACCESS_TOKEN"] = "test-token-abc"
        assert is_authenticated() is True

    def test_set_tokens_from_login_updates_cache(self) -> None:
        """set_tokens_from_login 應更新快取並使 is_authenticated() 回傳 True。"""
        from auth.vendor_login import is_authenticated, set_tokens_from_login  # noqa: PLC0415

        assert is_authenticated() is False
        set_tokens_from_login("new-access-token", "new-refresh-token")
        assert is_authenticated() is True

    def test_get_auth_headers_raises_when_no_token(self) -> None:
        """無 token 時 get_auth_headers() 應拋出 VendorAuthError。"""
        from auth.vendor_login import VendorAuthError, get_auth_headers  # noqa: PLC0415

        os.environ.pop("VENDOR_ACCESS_TOKEN", None)
        with pytest.raises(VendorAuthError):
            get_auth_headers()

    def test_get_auth_headers_returns_bearer_token(self) -> None:
        """有 token 時 get_auth_headers() 應回傳含 Authorization Bearer 的 dict。"""
        from auth.vendor_login import get_auth_headers, set_tokens_from_login  # noqa: PLC0415

        set_tokens_from_login("my-secret-token", None)
        headers = get_auth_headers()
        assert headers.get("Authorization") == "Bearer my-secret-token"

    def test_invalidate_access_token_raises_when_no_refresh(self) -> None:
        """無 refresh_token 時 invalidate_access_token() 應拋出 VendorAuthError。"""
        from auth.vendor_login import VendorAuthError, invalidate_access_token  # noqa: PLC0415

        # 設定 access token 但不設 refresh token
        os.environ["VENDOR_ACCESS_TOKEN"] = "some-token"
        os.environ.pop("VENDOR_REFRESH_TOKEN", None)

        with pytest.raises(VendorAuthError) as exc_info:
            invalidate_access_token()

        assert "refresh" in str(exc_info.value).lower()

    def test_invalidate_access_token_refreshes_on_success(self) -> None:
        """invalidate_access_token 在 refresh API 成功時應更新快取中的 access_token。"""
        from auth.vendor_login import (  # noqa: PLC0415
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
            patch("auth.vendor_login._persist_env"),  # 避免寫入 .env 檔案
        ):
            invalidate_access_token()

        headers = get_auth_headers()
        assert headers["Authorization"] == "Bearer new-access"

    def test_invalidate_access_token_raises_when_refresh_api_fails(self) -> None:
        """refresh API 回傳非 200 時 invalidate_access_token 應拋出 VendorAuthError。"""
        from auth.vendor_login import VendorAuthError, invalidate_access_token, set_tokens_from_login  # noqa: PLC0415

        set_tokens_from_login("old-access", "expired-refresh")

        fail_response = MagicMock()
        fail_response.status_code = 401
        fail_response.json.return_value = {"success": False}

        with patch("requests.post", return_value=fail_response):
            with pytest.raises(VendorAuthError):
                invalidate_access_token()

    def test_cache_seeded_only_once_from_env(self) -> None:
        """_seed_from_env_locked 應只執行一次（seeded flag 防止重複讀取）。"""
        import auth.vendor_login as vl  # noqa: PLC0415

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
        from auth.vendor_login import is_authenticated, set_tokens_from_login  # noqa: PLC0415

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
        """common_tools 應匯出 list_banks 函式。"""
        mod = importlib.import_module("tools.common_tools")
        assert callable(getattr(mod, "list_banks", None)), (
            "common_tools.list_banks 應為可呼叫函式"
        )

    def test_common_tools_has_list_delivery_types(self) -> None:
        """common_tools 應匯出 list_delivery_types 函式。"""
        mod = importlib.import_module("tools.common_tools")
        assert callable(getattr(mod, "list_delivery_types", None)), (
            "common_tools.list_delivery_types 應為可呼叫函式"
        )

    def test_auth_tools_has_get_current_user(self) -> None:
        """auth_tools 應匯出 get_current_user 函式。"""
        mod = importlib.import_module("tools.auth_tools")
        assert callable(getattr(mod, "get_current_user", None)), (
            "auth_tools.get_current_user 應為可呼叫函式"
        )

    def test_rest_client_has_api_post(self) -> None:
        """connectors.rest_client 應匯出 api_post 函式。"""
        mod = importlib.import_module("connectors.rest_client")
        assert callable(getattr(mod, "api_post", None))

    def test_rest_client_has_api_put(self) -> None:
        """connectors.rest_client 應匯出 api_put 函式。"""
        mod = importlib.import_module("connectors.rest_client")
        assert callable(getattr(mod, "api_put", None))

    def test_rest_client_has_api_delete(self) -> None:
        """connectors.rest_client 應匯出 api_delete 函式。"""
        mod = importlib.import_module("connectors.rest_client")
        assert callable(getattr(mod, "api_delete", None))

    def test_rest_client_has_fetch_all_pages(self) -> None:
        """connectors.rest_client 應匯出 fetch_all_pages 函式。"""
        mod = importlib.import_module("connectors.rest_client")
        assert callable(getattr(mod, "fetch_all_pages", None))

    def test_vendor_login_exports_expected_symbols(self) -> None:
        """auth.vendor_login 應匯出所有必要的公開函式與例外。"""
        mod = importlib.import_module("auth.vendor_login")
        expected_symbols = [
            "VendorAuthError",
            "is_authenticated",
            "get_auth_headers",
            "set_tokens_from_login",
            "invalidate_access_token",
        ]
        for sym in expected_symbols:
            assert hasattr(mod, sym), f"auth.vendor_login 缺少 {sym}"
