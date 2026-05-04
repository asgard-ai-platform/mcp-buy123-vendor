#!/usr/bin/env python3
"""Initialize the MCP server template by replacing {service} placeholders."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def prompt_service_name() -> str:
    print("MCP Server Template Initializer")
    print("=" * 40)
    while True:
        name = input("Enter service name (e.g., ecpay, stripe): ").strip().lower()
        if re.match(r"^[a-z][a-z0-9-]*$", name):
            return name
        print("  Invalid: use lowercase letters, numbers, and hyphens only (must start with a letter)")


def apply(path: Path, replacements: list[tuple[str, str]], drop_todo: bool = False) -> None:
    content = path.read_text()
    if drop_todo:
        lines = [l for l in content.splitlines(keepends=True) if "TODO:" not in l]
        content = "".join(lines)
    for old, new in replacements:
        content = content.replace(old, new)
    path.write_text(content)
    print(f"  updated  {path.relative_to(ROOT)}")


def main() -> None:
    service = prompt_service_name()
    service_title = service.replace("-", " ").title()

    print()

    # app.py — remove TODO comment, replace placeholder
    apply(
        ROOT / "app.py",
        [('{service}', service)],
        drop_todo=True,
    )

    # .mcp.json — rename server key and script entry point in args
    apply(
        ROOT / ".mcp.json",
        [('{service}', service), ('mcp-service', f'mcp-{service}')],
    )

    # pyproject.toml — package name, description, script entry point
    apply(
        ROOT / "pyproject.toml",
        [
            ('{service}', service),
            ('{Service Name}', service_title),
            ('mcp-service =', f'mcp-{service} ='),
        ],
        drop_todo=True,
    )

    # README.md, README.zh-TW.md — project structure example
    for fname in ("README.md", "README.zh-TW.md"):
        apply(ROOT / fname, [('{service}', service)])

    print()
    print(f"Done! Service initialized as: mcp-{service}")


if __name__ == "__main__":
    main()
