"""Tests for the static documentation source inventory."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from docs_inventory import (
    render_callable_signature,
    render_cli_reference,
    render_module_for_llms,
    render_module_page,
    render_symbol_index,
    scan_cli_options,
    scan_python_file,
)
from mkdocs_hooks import _pin_source_links, on_post_page


def test_scan_python_file_records_all_definition_kinds(tmp_path: Path) -> None:
    """Addressable and nested definitions retain signatures and source lines."""

    source_path = tmp_path / "vllm_mlx" / "sample.py"
    source_path.parent.mkdir()
    source_path.write_text(
        '''"""Sample module."""

CONSTANT = 3

class PublicClass:
    """Public class."""

    def method(self, value: int) -> str:
        """Convert a value to text."""

        def nested_helper() -> int:
            return value

        return str(nested_helper())

def public_function(flag: bool = False) -> bool:
    """Return the supplied flag.

    Args:
        flag: Value returned to the caller.
    """
    return flag
''',
        encoding="utf-8",
    )

    module = scan_python_file(source_path, tmp_path)
    symbols = {symbol.qualname: symbol for symbol in module.symbols}

    assert module.name == "vllm_mlx.sample"
    assert module.page_path == "reference/api/vllm_mlx/sample.md"
    assert module.members == ("CONSTANT", "PublicClass", "public_function")
    assert symbols["PublicClass"].kind == "class"
    assert symbols["PublicClass.method"].kind == "method"
    assert symbols["PublicClass.method"].addressable is True
    assert symbols["PublicClass.method.nested_helper"].kind == "nested function"
    assert symbols["PublicClass.method.nested_helper"].addressable is False
    assert symbols["public_function"].signature == (
        "def public_function(flag: bool=False) -> bool"
    )
    assert symbols["public_function"].parameters[0].name == "flag"
    assert symbols["public_function"].parameters[0].default == "False"
    assert symbols["public_function"].parameters[0].description == (
        "Value returned to the caller."
    )
    assert (
        render_callable_signature(symbols["public_function"], qualified=True)
        == "vllm_mlx.sample.public_function(flag: bool = False) -> bool"
    )
    assert symbols["public_function"].source_url.endswith("#L16-L22")


def test_renderers_include_source_map_and_llm_details(tmp_path: Path) -> None:
    """Human and LLM renderers include every symbol and exact source link."""

    source_path = tmp_path / "vllm_mlx" / "sample.py"
    source_path.parent.mkdir()
    source_path.write_text(
        '''"""Sample module."""

def _private_helper(value: int) -> int:
    return value + 1
''',
        encoding="utf-8",
    )
    module = scan_python_file(source_path, tmp_path)

    page = render_module_page(module)
    llm_page = render_module_for_llms(module)

    assert (
        "[`_private_helper`](#contract-vllm_mlx.sample._private_helper) | function"
        in page
    )
    assert "#L3-L4" in page
    assert "Signature and inputs" in page
    assert "`_private_helper(value: int) -> int`" in page
    assert 'id="contract-vllm_mlx.sample._private_helper"' in page
    assert "| `value` | `int` | `yes` | `none` |" in page
    assert "::: vllm_mlx.sample" in page
    assert "- _private_helper" in page
    assert "`vllm_mlx.sample._private_helper`" in llm_page
    assert "Signature: `def _private_helper(value: int) -> int`" in llm_page
    assert "Function `_private_helper` returns `value + 1`." in llm_page
    assert "Return expressions: value + 1" in llm_page


def test_symbol_index_exposes_inputs_details_and_source_ranges(tmp_path: Path) -> None:
    """The human index is filterable and links exact signatures to details."""

    source_path = tmp_path / "vllm_mlx" / "sample.py"
    source_path.parent.mkdir()
    source_path.write_text(
        '''"""Sample module."""

def convert(value: int, *, strict: bool = True) -> str:
    """Convert an integer to text."""
    return str(value)
''',
        encoding="utf-8",
    )
    module = scan_python_file(source_path, tmp_path)
    index = render_symbol_index([module])

    assert 'id="api-symbol-filter"' in index
    assert (
        "vllm_mlx.sample.convert(value: int, *, strict: bool = True) -&gt; str" in index
    )
    assert 'href="../api/vllm_mlx/sample/#contract-vllm_mlx.sample.convert"' in index
    assert urljoin(
        "https://vllm-mlx.is-a.dev/reference/python-symbols/",
        "../api/vllm_mlx/sample/#contract-vllm_mlx.sample.convert",
    ) == (
        "https://vllm-mlx.is-a.dev/reference/api/vllm_mlx/sample/"
        "#contract-vllm_mlx.sample.convert"
    )
    assert "#L3-L5" in index
    assert "Optional keyword-only input; defaults to `True`." in (
        module.symbols[0].parameters[1].description
    )


def test_cli_inventory_preserves_contract_and_source_link(tmp_path: Path) -> None:
    """Argparse declarations retain flags, behavior, help, and exact lines."""

    source_path = tmp_path / "scripts" / "tool.py"
    source_path.parent.mkdir()
    source_path.write_text(
        '''"""Sample command."""

def build_parser(parser):
    parser.add_argument(
        "--mode",
        choices=["safe", "fast"],
        default="safe",
        help="Select execution mode.",
    )
''',
        encoding="utf-8",
    )

    options = scan_cli_options([source_path], tmp_path)
    assert len(options) == 1
    option = options[0]
    assert option.context == "scripts.tool.build_parser"
    assert option.flags == ("--mode",)
    assert option.destination == "mode"
    assert option.choices == "['safe', 'fast']"
    assert option.default == "safe"
    assert option.description == "Select execution mode."
    assert option.source_url.endswith("#L4-L9")
    assert option.source_url in render_cli_reference(options)


def test_source_links_are_pinned_to_the_build_revision() -> None:
    """Published line links use a commit hash instead of a mutable branch."""

    revision = "1" * 40
    branch_link = (
        "https://github.com/waybarrios/vllm-mlx/blob/gh-pages/"
        "vllm_mlx/embedding.py#L1-L131"
    )

    pinned = _pin_source_links(branch_link, revision)

    assert f"/blob/{revision}/vllm_mlx/embedding.py#L1-L131" in pinned
    assert "/blob/gh-pages/" not in pinned


def test_homepage_edit_action_is_removed_without_affecting_docs_pages() -> None:
    """Only a page containing the homepage hero loses its edit action."""

    edit = '<a href="edit/gh-pages/docs/index.md" rel="edit"><svg></svg></a>'
    home = f'<article>{edit}<div class="vllm-hero"></div></article>'
    guide = f"<article>{edit}<h1>Guide</h1></article>"

    assert 'rel="edit"' not in on_post_page(home)
    assert 'rel="edit"' in on_post_page(guide)


def test_language_alternates_are_absolute() -> None:
    """Search metadata uses absolute URLs for every language alternate."""

    html = (
        '<link rel="alternate" href="./" hreflang="en">'
        '<link rel="alternate" href="../../es/guides/server/" hreflang="es">'
    )
    page = SimpleNamespace(canonical_url="https://vllm-mlx.is-a.dev/guides/server/")

    rendered = on_post_page(html, page=page)

    assert 'href="https://vllm-mlx.is-a.dev/guides/server/"' in rendered
    assert 'href="https://vllm-mlx.is-a.dev/es/guides/server/"' in rendered
