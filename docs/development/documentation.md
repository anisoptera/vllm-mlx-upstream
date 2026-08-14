# Documentation development

The documentation site uses MkDocs Material, mkdocstrings, and static AST inventory tools. It publishes all existing Markdown pages, an exhaustive Python reference, and machine-readable artifacts for LLMs and coding agents.

## Install documentation dependencies

```bash
python -m pip install -r docs/requirements.txt
```

This installs only the static documentation toolchain, so Linux builders do not need MLX. Apple Silicon developers may instead use `python -m pip install -e ".[docs]"` when they also want an editable runtime installation.

## Preview locally

```bash
python scripts/check_docs_coverage.py
mkdocs serve
```

Open `http://127.0.0.1:8000/vllm-mlx/`. Checked-in API pages are refreshed with `python scripts/gen_api_reference.py`.

## Run the release-equivalent build

```bash
python scripts/check_docs_coverage.py
mkdocs build --strict
```

Strict mode turns configuration, navigation, cross-reference, and link warnings into failures. The generated site is written to `site/`.

## Coverage contract

`scripts/check_docs_coverage.py` enforces:

- One generated API page for every tracked `vllm_mlx/**/*.py` module.
- One source-map entry for every class, function, method, nested class, and nested function.
- One searchable symbol-index entry and callable contract for every definition.
- An explicit parameter record with kind, type, requirement, default, and description for every callable input.
- A module docstring for every module.
- A docstring for every public, addressable class, function, and method.
- Conservative implementation facts for every private or nested definition, generated from its own AST body.
- An H1 heading in every hand-written Markdown page.
- Presence of the Pages workflow and agent-facing artifacts.

The check prints module, symbol, public explanation, and Markdown page totals. New code cannot silently reduce documentation coverage.

## Add or change Python code

New modules are discovered from Git-tracked Python files. No navigation file needs updating. Add a module docstring and document every public object in the source:

```python
def resolve_model(name: str, *, allow_remote: bool = True) -> ModelSpec:
    """Resolve a user-facing model name into a validated model specification.

    Args:
        name: Registry name, local path, or supported remote identifier.
        allow_remote: Whether remote model identifiers may be resolved.

    Returns:
        The validated model specification used by the loader.

    Raises:
        ValueError: If the name is empty or incompatible with policy.
    """
```

Private and nested definitions are included in the source map automatically. Add a docstring when their contract or invariants are not obvious.

## Add a guide

Place English pages in the appropriate `docs/` section. Use a descriptive H1 and relative links between documentation pages. Add translated pages under `docs/es`, `docs/fr`, or `docs/zh` when a translation is available.

Every guide should distinguish:

- Supported behavior from examples or recommendations.
- Defaults from optional configuration.
- Linux-compatible checks from Apple Silicon runtime checks.
- Public contracts from implementation details.

## Generated API pages

`scripts/gen_api_reference.py` writes deterministic, checked-in pages for every Python module. The workflow runs the generator with `--check` so stale pages fail CI. Each module page contains:

- Module summary and complete source link.
- Full mkdocstrings rendering with signatures, parsed parameter sections, and inline source.
- Expandable contracts for every public, private, and nested definition.
- Explicit inputs, defaults, return annotations, direct exceptions, and source-grounded behavior.
- Exact `#Lx-Ly` links for every definition.

`docs/reference/python-symbols.md` adds a filterable index over every runtime symbol and signature. Source links are stored against `gh-pages` for readable Markdown, then rewritten during the build to the exact commit in `VLLM_MLX_DOCS_SOURCE_REVISION`. This keeps `#Lx-Ly` permalinks correct after either branch changes.

## LLM and agent artifacts

`docs/llms.txt` is the compact, curated index defined by the emerging llms.txt convention. `scripts/mkdocs_hooks.py` creates these build artifacts:

- `llms-full.txt`: every hand-written page plus a complete record for every Python symbol.
- `api-inventory.json`: structured module and symbol metadata.
- Markdown mirrors of hand-written and generated API pages.

The compact index is hand-maintained because page priority and descriptions require editorial judgment. The complete corpus and inventory are generated so they cannot drift from source.

## GitHub Pages deployment

`.github/workflows/docs.yml` builds documentation on pull requests targeting `gh-pages`. A successful push to `gh-pages` uploads the site artifact and deploys it through the protected `github-pages` environment. Documentation changes stay on that dedicated branch and do not need to enter `main`.

Repository administrators must select **GitHub Actions** as the Pages publishing source once in repository settings. The workflow uses least-privilege permissions: the build reads contents, and only the deploy job receives `pages: write` and `id-token: write`.

## Review checklist

- Run the coverage check and strict build.
- Open the changed page in the local preview.
- Verify commands and request examples against current code.
- Follow every new relative link.
- Confirm source links use the correct module, immutable commit, and line range.
- Inspect `site/llms.txt`, `site/llms-full.txt`, and `site/api-inventory.json`.
- Check that no generated `site/` content is staged.
- Run focused tests when documentation tools or source docstrings change.
