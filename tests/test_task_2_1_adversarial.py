"""任務 2.1 對預設離線 pytest 流程的對抗性驗證。

Phase 3.1 更新：
- 測試模組不再使用 sys.path.insert 假設，改用 _src_bootstrap 確保 src/ 可解析
- _drop_modules 前綴僅保留 mcp_buy123_vendor.* 命名空間，移除舊 flat-layout 前綴
- TestImportPathAssumptions 更新為驗證 _src_bootstrap 插入 src/ 而非 repo root
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = REPO_ROOT / "src"


def _drop_modules(prefixes: tuple[str, ...]) -> None:
    """移除已載入模組，確保每次測試都重新匯入。"""
    for name in list(sys.modules):
        if name in prefixes or any(name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


@pytest.fixture(autouse=True)
def clean_import_state(monkeypatch: pytest.MonkeyPatch):
    """隔離匯入狀態，避免環境變數與模組快取互相污染。"""
    monkeypatch.delenv("BUY123_RUN_LIVE_TESTS", raising=False)
    monkeypatch.delenv("VENDOR_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("VENDOR_REFRESH_TOKEN", raising=False)
    _drop_modules((
        "tests.test_all_tools",
        "tests.test_basic",
        "mcp_buy123_vendor",
    ))
    yield
    _drop_modules((
        "tests.test_all_tools",
        "tests.test_basic",
        "mcp_buy123_vendor",
    ))


class TestOfflineSafetyAgainstLiveCalls:
    """驗證預設 pytest 流程不會偷跑 live API。"""

    def test_importing_test_all_tools_with_default_env_never_makes_http_requests(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """未 opt-in 時，匯入 live 測試模組也不得發出任何 HTTP。"""
        request_calls: list[tuple[tuple, dict]] = []
        post_calls: list[tuple[tuple, dict]] = []

        def fail_request(*args, **kwargs):
            request_calls.append((args, kwargs))
            raise AssertionError("匯入 tests.test_all_tools 時不應呼叫 requests.request")

        def fail_post(*args, **kwargs):
            post_calls.append((args, kwargs))
            raise AssertionError("匯入 tests.test_all_tools 時不應呼叫 requests.post")

        monkeypatch.setattr("requests.request", fail_request)
        monkeypatch.setattr("requests.post", fail_post)

        module = importlib.import_module("tests.test_all_tools")

        assert module._has_auth() is False
        assert request_calls == []
        assert post_calls == []

    def test_main_exits_cleanly_without_opt_in_and_never_reaches_live_tools(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """直接執行入口在未 opt-in 時應立刻退出，不碰任何 live tool。"""
        module = importlib.import_module("tests.test_all_tools")

        def fail_if_called(*args, **kwargs):
            raise AssertionError("未 opt-in 時 _main 不應執行任何 live tool")

        monkeypatch.setattr(module.common_tools, "list_banks", fail_if_called)

        with pytest.raises(SystemExit) as exc_info:
            module._main()

        assert exc_info.value.code == 0

    def test_importing_test_basic_with_missing_tokens_never_makes_http_requests(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """離線基本測試在無 token 下匯入也不得觸發網路。"""
        request_calls: list[tuple[tuple, dict]] = []
        post_calls: list[tuple[tuple, dict]] = []

        def fail_request(*args, **kwargs):
            request_calls.append((args, kwargs))
            raise AssertionError("匯入 tests.test_basic 時不應呼叫 requests.request")

        def fail_post(*args, **kwargs):
            post_calls.append((args, kwargs))
            raise AssertionError("匯入 tests.test_basic 時不應呼叫 requests.post")

        monkeypatch.setattr("requests.request", fail_request)
        monkeypatch.setattr("requests.post", fail_post)

        module = importlib.import_module("tests.test_basic")

        assert module.TestModuleImports.__name__ == "TestModuleImports"
        assert request_calls == []
        assert post_calls == []


class TestEnvBypassResistance:
    """驗證 live 測試啟用條件不會被寬鬆值繞過。"""

    @pytest.mark.parametrize(
        ("env_value", "expected_skip"),
        [(None, True), ("", True), ("0", True), ("true", True), ("1", False)],
    )
    def test_live_test_gate_requires_exact_string_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env_value: str | None,
        expected_skip: bool,
    ) -> None:
        """只有 BUY123_RUN_LIVE_TESTS=1 才能解除 skip。"""
        if env_value is None:
            monkeypatch.delenv("BUY123_RUN_LIVE_TESTS", raising=False)
        else:
            monkeypatch.setenv("BUY123_RUN_LIVE_TESTS", env_value)

        module = importlib.import_module("tests.test_all_tools")
        mark = module.pytestmark.mark

        assert mark.name == "skipif"
        assert mark.args[0] is expected_skip

    @pytest.mark.parametrize(
        ("access_token", "refresh_token", "expected"),
        [
            (None, None, False),
            ("", "refresh-only", False),
            ("access-only", None, True),
            ("access", "refresh", True),
        ],
    )
    def test_auth_gate_depends_on_access_token_presence_only(
        self,
        monkeypatch: pytest.MonkeyPatch,
        access_token: str | None,
        refresh_token: str | None,
        expected: bool,
    ) -> None:
        """auth-required 測試只會因 access token 存在而解除 skip。"""
        if access_token is None:
            monkeypatch.delenv("VENDOR_ACCESS_TOKEN", raising=False)
        else:
            monkeypatch.setenv("VENDOR_ACCESS_TOKEN", access_token)

        if refresh_token is None:
            monkeypatch.delenv("VENDOR_REFRESH_TOKEN", raising=False)
        else:
            monkeypatch.setenv("VENDOR_REFRESH_TOKEN", refresh_token)

        module = importlib.import_module("tests.test_all_tools")

        assert module._has_auth() is expected


class TestImportPathAssumptions:
    """驗證測試檔的 sys.path 假設對離線 pytest 流程是穩定的。

    Phase 3.1 更新：測試模組改用 _src_bootstrap 確保 src/ 在 sys.path 中，
    而非直接插入 repo root。驗證 src/ 目錄可解析 mcp_buy123_vendor.*。
    """

    def test_src_dir_is_resolvable_after_bootstrap(self) -> None:
        """匯入 _src_bootstrap 後，src/ 目錄應在 sys.path 中，讓 mcp_buy123_vendor.* 可解析。"""
        # 確保 _src_bootstrap 已載入（測試環境中通常已載入）
        importlib.import_module("_src_bootstrap")

        src_in_path = any(
            Path(p).resolve() == _SRC_DIR
            for p in sys.path
            if p  # 排除空字串
        )
        assert src_in_path, (
            f"_src_bootstrap 應將 {_SRC_DIR} 加入 sys.path，"
            f"但目前 sys.path 中找不到此路徑"
        )

    def test_test_modules_can_import_mcp_buy123_vendor(self) -> None:
        """匯入 tests.test_all_tools 與 tests.test_basic 後，mcp_buy123_vendor 套件應可解析。"""
        importlib.import_module("tests.test_all_tools")
        importlib.import_module("tests.test_basic")

        # 驗證 mcp_buy123_vendor 套件可匯入（src/ 已在 sys.path 中）
        pkg = importlib.import_module("mcp_buy123_vendor")
        assert pkg is not None

    def test_test_all_tools_file_path_is_correct(self) -> None:
        """tests.test_all_tools 的 __file__ 應指向正確的測試檔案。"""
        all_tools = importlib.import_module("tests.test_all_tools")
        assert all_tools.__file__ is not None
        assert all_tools.__file__.endswith("tests/test_all_tools.py")

    def test_test_basic_file_path_is_correct(self) -> None:
        """tests.test_basic 的 __file__ 應指向正確的測試檔案。"""
        basic = importlib.import_module("tests.test_basic")
        assert basic.__file__ is not None
        assert basic.__file__.endswith("tests/test_basic.py")


class TestHelperBehavior:
    """驗證測試輔助函式本身不會引入寬鬆行為。"""

    def test_call_tool_invokes_callable_once_and_reports_pass(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_call_tool 應精確呼叫一次並輸出 PASS。"""
        module = importlib.import_module("tests.test_all_tools")
        calls: list[dict[str, int]] = []

        def fake_tool(*, page: int) -> dict:
            calls.append({"page": page})
            return {"result": "ok"}

        result = module._call_tool("fake_tool", fake_tool, page=7)
        captured = capsys.readouterr()

        assert result is None
        assert calls == [{"page": 7}]
        assert "PASS" in captured.out
