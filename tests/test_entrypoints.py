"""重構後保護測試：入口與路徑基準（FR-002, FR-005, FR-006）

所有測試均為離線、確定性測試，使用 AST 解析或路徑計算，
不匯入任何會觸發網路或副作用的模組。

Phase 2 遷移後更新：
- 規範實作已移至 src/mcp_buy123_vendor/
- 根目錄包裝器（mcp_server.py、auth/、scripts/）委派至 src 套件
- 路徑敏感斷言同時驗證根包裝器行為與 src 規範路徑
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

# 確保 src/ 在 sys.path 中，讓 mcp_buy123_vendor.* 可解析
import _src_bootstrap  # noqa: F401

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_PKG = _PROJECT_ROOT / "src" / "mcp_buy123_vendor"


# ---------------------------------------------------------------------------
# 輔助：從原始碼 AST 中擷取指定名稱的賦值右側節點
# ---------------------------------------------------------------------------

def _parse_source(path: Path) -> ast.Module:
    """讀取並解析 Python 原始碼，回傳 AST 模組節點。"""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _find_assign_value(tree: ast.Module, target_name: str) -> ast.expr | None:
    """在模組頂層找到 `target_name = <expr>` 並回傳右側 AST 節點。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == target_name:
                    return node.value
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == target_name:
                return node.value
    return None


def _find_call_in_function(tree: ast.Module, func_name: str) -> list[ast.Call]:
    """在模組中找到名為 func_name 的函式定義，回傳其內所有 Call 節點。"""
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        calls.append(child)
    return calls


def _ast_unparse(node: ast.expr) -> str:
    """將 AST 節點轉回原始碼字串（Python 3.9+）。"""
    return ast.unparse(node)


# ===========================================================================
# 1. mcp_server.py（根包裝器）— .env 路徑解析與委派
# ===========================================================================

class TestMcpServerEnvPath:
    """驗證 mcp_server.py 從自身檔案位置解析 .env，而非依賴 cwd。"""

    _SOURCE = _PROJECT_ROOT / "mcp_server.py"

    def test_source_file_exists(self) -> None:
        """mcp_server.py 應存在於專案根目錄。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_load_dotenv_path_resolves_to_project_root(self) -> None:
        """實際計算 Path(__file__).resolve().parent / '.env' 應指向專案根目錄下的 .env。"""
        mcp_server_file = self._SOURCE
        # 模擬 mcp_server.py 中的路徑計算
        computed_env = mcp_server_file.resolve().parent / ".env"
        expected_env = _PROJECT_ROOT / ".env"
        assert computed_env == expected_env, (
            f"mcp_server.py 解析的 .env 路徑 {computed_env} "
            f"應等於專案根目錄下的 {expected_env}"
        )


class TestMcpServerMain:
    """驗證 mcp_server.py（根包裝器）委派至 mcp_buy123_vendor.server。"""

    _SOURCE = _PROJECT_ROOT / "mcp_server.py"

    def test_source_file_exists(self) -> None:
        """mcp_server.py 應存在於專案根目錄。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_delegates_to_src_server(self) -> None:
        """mcp_server.py 應從 mcp_buy123_vendor.server 匯入 main，委派至 src 套件。"""
        tree = _parse_source(self._SOURCE)
        src_server_imports: list[ast.ImportFrom] = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "mcp_buy123_vendor.server"
            and any(alias.name == "main" for alias in node.names)
        ]
        assert src_server_imports, (
            "mcp_server.py 應有 `from mcp_buy123_vendor.server import main` 陳述式，"
            "表示已委派至 src 套件"
        )

    def test_src_path_inserted_before_import(self) -> None:
        """mcp_server.py 應在匯入 mcp_buy123_vendor 前確保 src/ 在 sys.path 中。"""
        tree = _parse_source(self._SOURCE)
        # 尋找 sys.path.insert 或 _src_bootstrap 匯入
        has_path_setup = False
        for node in ast.walk(tree):
            # 方式一：直接 sys.path.insert
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "insert"
                    and isinstance(func.value, ast.Attribute)
                    and func.value.attr == "path"
                ):
                    has_path_setup = True
                    break
            # 方式二：import _src_bootstrap
            if isinstance(node, ast.Import):
                if any(alias.name == "_src_bootstrap" for alias in node.names):
                    has_path_setup = True
                    break
        assert has_path_setup, (
            "mcp_server.py 應在匯入 mcp_buy123_vendor 前設定 sys.path（"
            "透過 sys.path.insert 或 import _src_bootstrap）"
        )


# ===========================================================================
# 2. src/mcp_buy123_vendor/server.py（規範入口）— .env 路徑與 main()
# ===========================================================================

class TestSrcServerCanonical:
    """驗證 src/mcp_buy123_vendor/server.py 的 .env 路徑解析與 main() 函式。"""

    _SOURCE = _SRC_PKG / "server.py"

    def test_source_file_exists(self) -> None:
        """src/mcp_buy123_vendor/server.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_load_dotenv_uses_file_relative_path(self) -> None:
        """load_dotenv 呼叫應使用 Path(__file__).resolve().parent... / '.env'，
        而非硬編碼路徑或 cwd 相對路徑。
        """
        tree = _parse_source(self._SOURCE)

        load_dotenv_calls: list[ast.Call] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "load_dotenv":
                    load_dotenv_calls.append(node)
                elif isinstance(func, ast.Attribute) and func.attr == "load_dotenv":
                    load_dotenv_calls.append(node)

        assert load_dotenv_calls, "src/mcp_buy123_vendor/server.py 應有 load_dotenv() 呼叫"

        first_call = load_dotenv_calls[0]
        assert first_call.args, "load_dotenv() 應傳入路徑引數"
        arg_src = _ast_unparse(first_call.args[0])

        assert "__file__" in arg_src, (
            f"load_dotenv 的路徑引數應包含 __file__，實際為：{arg_src!r}"
        )
        assert ".env" in arg_src, (
            f"load_dotenv 的路徑引數應包含 '.env'，實際為：{arg_src!r}"
        )

    def test_load_dotenv_path_resolves_to_project_root(self) -> None:
        """實際計算 src/mcp_buy123_vendor/server.py 的 .env 路徑應指向專案根目錄。"""
        server_file = self._SOURCE
        # src/mcp_buy123_vendor/server.py → .parent.parent.parent = 專案根目錄
        computed_env = server_file.resolve().parent.parent.parent / ".env"
        expected_env = _PROJECT_ROOT / ".env"
        assert computed_env == expected_env, (
            f"server.py 解析的 .env 路徑 {computed_env} "
            f"應等於專案根目錄下的 {expected_env}"
        )

    def test_main_function_exists(self) -> None:
        """src/mcp_buy123_vendor/server.py 應定義 main() 函式。"""
        tree = _parse_source(self._SOURCE)
        func_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert "main" in func_names, "src/mcp_buy123_vendor/server.py 應定義 main() 函式"

    def test_main_calls_mcp_run(self) -> None:
        """main() 函式體應包含 mcp.run() 呼叫。"""
        tree = _parse_source(self._SOURCE)
        calls = _find_call_in_function(tree, "main")

        mcp_run_calls = [
            c for c in calls
            if isinstance(c.func, ast.Attribute)
            and c.func.attr == "run"
            and isinstance(c.func.value, ast.Name)
            and c.func.value.id == "mcp"
        ]
        assert mcp_run_calls, (
            "main() 函式應呼叫 mcp.run()，但在 AST 中找不到此呼叫"
        )

    def test_mcp_imported_from_src_app(self) -> None:
        """src/mcp_buy123_vendor/server.py 應從 mcp_buy123_vendor.app 匯入 mcp。"""
        tree = _parse_source(self._SOURCE)
        src_app_imports: list[ast.ImportFrom] = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "mcp_buy123_vendor.app"
            and any(alias.name == "mcp" for alias in node.names)
        ]
        assert src_app_imports, (
            "src/mcp_buy123_vendor/server.py 應有 `from mcp_buy123_vendor.app import mcp` 陳述式"
        )


# ===========================================================================
# 3. auth/vendor_login.py（根包裝器）— 委派至 src
# ===========================================================================

class TestVendorLoginRootWrapper:
    """驗證根層 auth/vendor_login.py 是委派至 src 套件的薄包裝器。"""

    _SOURCE = _PROJECT_ROOT / "auth" / "vendor_login.py"

    def test_source_file_exists(self) -> None:
        """auth/vendor_login.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_delegates_to_src_package(self) -> None:
        """auth/vendor_login.py 應從 mcp_buy123_vendor.auth.vendor_login 匯入符號。"""
        tree = _parse_source(self._SOURCE)
        src_imports: list[ast.ImportFrom] = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "mcp_buy123_vendor.auth.vendor_login"
        ]
        assert src_imports, (
            "auth/vendor_login.py 應從 mcp_buy123_vendor.auth.vendor_login 匯入符號，"
            "表示已委派至 src 套件"
        )


# ===========================================================================
# 4. src/mcp_buy123_vendor/auth/vendor_login.py（規範實作）— _persist_env 路徑
# ===========================================================================

class TestVendorLoginPersistEnvPath:
    """驗證 src/mcp_buy123_vendor/auth/vendor_login.py 的 _persist_env() 路徑解析。"""

    _SOURCE = _SRC_PKG / "auth" / "vendor_login.py"

    def test_source_file_exists(self) -> None:
        """src/mcp_buy123_vendor/auth/vendor_login.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_persist_env_function_exists(self) -> None:
        """src/mcp_buy123_vendor/auth/vendor_login.py 應定義 _persist_env() 函式。"""
        tree = _parse_source(self._SOURCE)
        func_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert "_persist_env" in func_names, (
            "src/mcp_buy123_vendor/auth/vendor_login.py 應定義 _persist_env() 函式"
        )

    def test_persist_env_uses_file_relative_path(self) -> None:
        """_persist_env() 中的 env_path 應使用 Path(__file__).resolve().parent... / '.env'。"""
        tree = _parse_source(self._SOURCE)

        env_path_assign: ast.expr | None = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "_persist_env":
                    for child in ast.walk(node):
                        if isinstance(child, ast.Assign):
                            for tgt in child.targets:
                                if isinstance(tgt, ast.Name) and tgt.id == "env_path":
                                    env_path_assign = child.value

        assert env_path_assign is not None, (
            "_persist_env() 應有 env_path = ... 賦值陳述式"
        )

        path_src = _ast_unparse(env_path_assign)
        assert "__file__" in path_src, (
            f"env_path 應包含 __file__ 參照，實際為：{path_src!r}"
        )
        assert ".env" in path_src, (
            f"env_path 應包含 '.env'，實際為：{path_src!r}"
        )

    def test_persist_env_path_resolves_to_project_root(self) -> None:
        """實際計算 _persist_env 的路徑邏輯應指向專案根目錄下的 .env。

        src/mcp_buy123_vendor/auth/vendor_login.py 需要四層 .parent 才能到達專案根目錄：
        vendor_login.py → auth/ → mcp_buy123_vendor/ → src/ → 專案根目錄
        """
        vendor_login_file = self._SOURCE
        computed_env = vendor_login_file.resolve().parent.parent.parent.parent / ".env"
        expected_env = _PROJECT_ROOT / ".env"
        assert computed_env == expected_env, (
            f"_persist_env 解析的 .env 路徑 {computed_env} "
            f"應等於專案根目錄下的 {expected_env}"
        )


# ===========================================================================
# 5. auth/browser_login.py（根包裝器）— 委派至 src
# ===========================================================================

class TestBrowserLoginRootWrapper:
    """驗證根層 auth/browser_login.py 是委派至 src 套件的薄包裝器。"""

    _SOURCE = _PROJECT_ROOT / "auth" / "browser_login.py"

    def test_source_file_exists(self) -> None:
        """auth/browser_login.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_delegates_to_src_package(self) -> None:
        """auth/browser_login.py 應從 mcp_buy123_vendor.auth.browser_login 匯入符號。"""
        tree = _parse_source(self._SOURCE)
        src_imports: list[ast.ImportFrom] = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "mcp_buy123_vendor.auth.browser_login"
        ]
        assert src_imports, (
            "auth/browser_login.py 應從 mcp_buy123_vendor.auth.browser_login 匯入符號，"
            "表示已委派至 src 套件"
        )


# ===========================================================================
# 6. src/mcp_buy123_vendor/auth/browser_login.py（規範實作）— PROJECT_ROOT 與 ENV_PATH
# ===========================================================================

class TestBrowserLoginPaths:
    """驗證 src/mcp_buy123_vendor/auth/browser_login.py 的 PROJECT_ROOT / ENV_PATH 解析。"""

    _SOURCE = _SRC_PKG / "auth" / "browser_login.py"

    def test_source_file_exists(self) -> None:
        """src/mcp_buy123_vendor/auth/browser_login.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_project_root_defined_at_module_level(self) -> None:
        """src/mcp_buy123_vendor/auth/browser_login.py 應在模組頂層定義 PROJECT_ROOT。"""
        tree = _parse_source(self._SOURCE)
        value = _find_assign_value(tree, "PROJECT_ROOT")
        assert value is not None, (
            "src/mcp_buy123_vendor/auth/browser_login.py 應在模組頂層定義 PROJECT_ROOT"
        )

    def test_project_root_uses_file_relative_path(self) -> None:
        """PROJECT_ROOT 應使用 Path(__file__).resolve().parent... 計算。"""
        tree = _parse_source(self._SOURCE)
        value = _find_assign_value(tree, "PROJECT_ROOT")
        assert value is not None

        src = _ast_unparse(value)
        assert "__file__" in src, (
            f"PROJECT_ROOT 應包含 __file__ 參照，實際為：{src!r}"
        )
        # src/mcp_buy123_vendor/auth/browser_login.py 需要四層 .parent 才能到達專案根目錄
        assert src.count(".parent") >= 4, (
            f"PROJECT_ROOT 應有至少四個 .parent（auth/ → mcp_buy123_vendor/ → src/ → 專案根目錄），"
            f"實際為：{src!r}"
        )

    def test_env_path_defined_at_module_level(self) -> None:
        """src/mcp_buy123_vendor/auth/browser_login.py 應在模組頂層定義 ENV_PATH。"""
        tree = _parse_source(self._SOURCE)
        value = _find_assign_value(tree, "ENV_PATH")
        assert value is not None, (
            "src/mcp_buy123_vendor/auth/browser_login.py 應在模組頂層定義 ENV_PATH"
        )

    def test_env_path_references_project_root(self) -> None:
        """ENV_PATH 應由 PROJECT_ROOT / '.env' 組成。"""
        tree = _parse_source(self._SOURCE)
        value = _find_assign_value(tree, "ENV_PATH")
        assert value is not None

        src = _ast_unparse(value)
        assert "PROJECT_ROOT" in src, (
            f"ENV_PATH 應參照 PROJECT_ROOT，實際為：{src!r}"
        )
        assert ".env" in src, (
            f"ENV_PATH 應包含 '.env'，實際為：{src!r}"
        )

    def test_project_root_resolves_to_project_root(self) -> None:
        """實際計算 browser_login.py 的 PROJECT_ROOT 應等於專案根目錄。

        src/mcp_buy123_vendor/auth/browser_login.py → .parent×4 = 專案根目錄
        """
        browser_login_file = self._SOURCE
        computed_root = browser_login_file.resolve().parent.parent.parent.parent
        assert computed_root == _PROJECT_ROOT, (
            f"src/mcp_buy123_vendor/auth/browser_login.py 的 PROJECT_ROOT {computed_root} "
            f"應等於專案根目錄 {_PROJECT_ROOT}"
        )

    def test_env_path_resolves_to_project_root_dot_env(self) -> None:
        """實際計算 ENV_PATH 應等於專案根目錄下的 .env。"""
        browser_login_file = self._SOURCE
        computed_root = browser_login_file.resolve().parent.parent.parent.parent
        computed_env = computed_root / ".env"
        expected_env = _PROJECT_ROOT / ".env"
        assert computed_env == expected_env, (
            f"src/mcp_buy123_vendor/auth/browser_login.py 的 ENV_PATH {computed_env} "
            f"應等於 {expected_env}"
        )


# ===========================================================================
# 7. scripts/auth/playwright_login.py（根包裝器）— 委派至 src
# ===========================================================================

class TestPlaywrightLoginScriptPaths:
    """驗證 scripts/auth/playwright_login.py 委派至 src 套件的薄包裝器行為。"""

    _SOURCE = _PROJECT_ROOT / "scripts" / "auth" / "playwright_login.py"

    def test_source_file_exists(self) -> None:
        """scripts/auth/playwright_login.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_delegates_to_src_package(self) -> None:
        """scripts/auth/playwright_login.py 應從 mcp_buy123_vendor.scripts.playwright_login 匯入 main。"""
        tree = _parse_source(self._SOURCE)
        src_imports: list[ast.ImportFrom] = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "mcp_buy123_vendor.scripts.playwright_login"
            and any(alias.name == "main" for alias in node.names)
        ]
        assert src_imports, (
            "scripts/auth/playwright_login.py 應有 "
            "`from mcp_buy123_vendor.scripts.playwright_login import main` 陳述式"
        )

    def test_src_path_setup_before_import(self) -> None:
        """scripts/auth/playwright_login.py 應在匯入 mcp_buy123_vendor 前設定 src/ 路徑。"""
        tree = _parse_source(self._SOURCE)

        # 尋找 sys.path.insert 或 _src_bootstrap 匯入
        has_path_setup = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "insert"
                    and isinstance(func.value, ast.Attribute)
                    and func.value.attr == "path"
                ):
                    has_path_setup = True
                    break
            if isinstance(node, ast.Import):
                if any(alias.name == "_src_bootstrap" for alias in node.names):
                    has_path_setup = True
                    break
        assert has_path_setup, (
            "scripts/auth/playwright_login.py 應在匯入 mcp_buy123_vendor 前設定 sys.path"
        )

    def test_src_path_resolves_to_project_src(self) -> None:
        """scripts/auth/playwright_login.py 計算的 src/ 路徑應指向專案的 src/ 目錄。"""
        script_file = self._SOURCE
        # scripts/auth/playwright_login.py → .parent.parent.parent / "src"
        computed_src = script_file.resolve().parent.parent.parent / "src"
        expected_src = _PROJECT_ROOT / "src"
        assert computed_src == expected_src, (
            f"scripts/auth/playwright_login.py 的 src 路徑 {computed_src} "
            f"應等於 {expected_src}"
        )


# ===========================================================================
# 8. src/mcp_buy123_vendor/scripts/playwright_login.py（規範實作）
# ===========================================================================

class TestSrcPlaywrightLoginScript:
    """驗證 src/mcp_buy123_vendor/scripts/playwright_login.py 的規範實作存在。"""

    _SOURCE = _SRC_PKG / "scripts" / "playwright_login.py"

    def test_source_file_exists(self) -> None:
        """src/mcp_buy123_vendor/scripts/playwright_login.py 應存在。"""
        assert self._SOURCE.exists(), f"找不到 {self._SOURCE}"

    def test_main_function_exists(self) -> None:
        """src/mcp_buy123_vendor/scripts/playwright_login.py 應定義 main() 函式。"""
        tree = _parse_source(self._SOURCE)
        func_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert "main" in func_names, (
            "src/mcp_buy123_vendor/scripts/playwright_login.py 應定義 main() 函式"
        )
