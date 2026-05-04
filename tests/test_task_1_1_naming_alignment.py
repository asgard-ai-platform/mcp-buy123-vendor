import ast
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
APP_FILE = ROOT / "src" / "mcp_buy123_vendor" / "app.py"


def load_pyproject():
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def load_app_ast():
    return ast.parse(APP_FILE.read_text(encoding="utf-8"))


def test_project_name_and_cli_entrypoints_match_public_name():
    pyproject = load_pyproject()
    scripts = pyproject["project"]["scripts"]

    assert pyproject["project"]["name"] == "mcp-buy123-vendor"
    assert scripts == {
        "mcp-buy123-vendor": "mcp_buy123_vendor.server:main",
        "mcp-buy123-vendor-login": "mcp_buy123_vendor.scripts.playwright_login:main",
    }
    assert all(name.startswith("mcp-buy123-vendor") for name in scripts)
    assert list(scripts) == ["mcp-buy123-vendor", "mcp-buy123-vendor-login"]


def test_app_creates_fastmcp_with_aligned_public_server_identifier():
    tree = load_app_ast()
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "mcp" for target in node.targets)
    ]

    assert len(assignments) == 1
    call = assignments[0].value
    assert isinstance(call, ast.Call)
    assert isinstance(call.func, ast.Name)
    assert call.func.id == "FastMCP"
    assert len(call.args) == 1
    assert isinstance(call.args[0], ast.Constant)
    assert call.args[0].value == "buy123-vendor"


def test_mcp_display_name_matches_distribution_name_without_protocol_prefix():
    pyproject = load_pyproject()
    distribution_name = pyproject["project"]["name"]

    tree = load_app_ast()
    fastmcp_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "FastMCP"
    ]

    assert len(fastmcp_calls) == 1
    assert fastmcp_calls[0].args[0].value == distribution_name.removeprefix("mcp-")


def test_entrypoint_names_do_not_use_confusing_separator_or_legacy_variants():
    pyproject = load_pyproject()
    scripts = pyproject["project"]["scripts"]

    assert "mcp_buy123_vendor" not in scripts
    assert "buy123-vendor" not in scripts
    assert "mcp-buy123" not in scripts
    assert all("_" not in name for name in scripts)
    assert all(" " not in name for name in scripts)


def test_relevant_files_do_not_contain_legacy_public_identifiers():
    combined_text = PYPROJECT.read_text(encoding="utf-8") + "\n" + APP_FILE.read_text(encoding="utf-8")

    assert "mcp-buy123\"" not in combined_text
    assert 'FastMCP("mcp-buy123-vendor")' not in combined_text
    # 只拒絕獨立出現的舊命名 buy123_vendor（不帶 mcp_ 前綴）
    # mcp_buy123_vendor 是合法的 src-layout 套件路徑，不應被視為舊命名
    import re
    assert not re.search(r'(?<!mcp_)buy123_vendor', combined_text)
    assert 'name = "buy123-vendor"' not in combined_text
