# Guide for LLMs and coding agents

This page is a stable entry point for tools that need to understand or modify vllm-mlx. It describes where authoritative information lives and how to avoid common mistakes.

## Preferred context order

1. Read [`/llms.txt`](../llms.txt) for the documentation map.
2. Read the relevant concept or user guide.
3. Find the owning module in the [codebase map](codebase-map.md).
4. Query [`/api-inventory.json`](https://vllm-mlx.is-a.dev/api-inventory.json) for exact symbols, signatures, docstrings, visibility, and source lines.
5. Open the generated module page for inline source and related members.
6. Read the nearest tests before proposing a change.

Use [`/llms-full.txt`](https://vllm-mlx.is-a.dev/llms-full.txt) only when a large context window can hold the complete corpus.

Use [`/source-inventory.json`](https://vllm-mlx.is-a.dev/source-inventory.json) when work also touches maintenance scripts or runnable examples.

## Machine-readable API inventory

The JSON inventory has this top-level shape:

```json
{
  "schema_version": "1.0",
  "repository": "waybarrios/vllm-mlx",
  "source_branch": "gh-pages",
  "module_count": 117,
  "symbol_count": 2003,
  "modules": []
}
```

Counts change as code is added. Each module includes its path, generated page, docstring, members, and symbols. Each symbol includes:

- `full_name` and `qualname`
- `kind`
- `signature`
- complete `docstring` and compact `summary`
- conservative `implementation` facts plus calls, state access, returns, raises, decorators, await, and yield metadata
- `public`, `addressable`, and `documented` flags
- `line`, `end_line`, and a GitHub `#Lx-Ly` source URL

Do not infer a source line from a rendered HTML page. Use the inventory URL so review comments stay attached to the exact definition.

## Platform boundary

The runtime is designed for macOS on Apple Silicon. Importing many package modules on Linux fails because MLX is unavailable. Documentation tools use the Python AST and Griffe to avoid imports.

On Linux, prefer:

```bash
python scripts/check_docs_coverage.py
mkdocs build --strict
ruff check vllm_mlx/ tests/ --select E,F,W --ignore E402,E501,E731,F811,F841
black --check vllm_mlx/ tests/
```

Run MLX-dependent tests on Apple Silicon. Do not treat a Linux skip as proof of runtime correctness.

## Runtime invariants

- MLX generation streams are thread-local. Scheduler steps must stay on their bound worker thread.
- A model lease must outlive every request operation that touches the model or tokenizer.
- Parser state is request-local and must reset before a new stream.
- A parser-suppressed terminal delta still requires a terminal protocol event and finish reason.
- Cache reuse requires compatible model identity, token prefix, layout, and layer trimming behavior.
- Paged block reference counts and free-list membership must agree.
- Model reload must invalidate tokenizer-derived parser caches.
- Streaming cleanup must run after disconnect, timeout, cancellation, and ordinary failure.

## Change map

| Change | Start here | Focused tests to find |
| --- | --- | --- |
| OpenAI or Anthropic request fields | `api/models.py`, `api/anthropic_models.py`, `server.py` | API model, adapter, and server tests |
| Streaming terminal behavior | `server.py`, `api/streaming.py`, parser implementation | server and streaming regression tests |
| Continuous batching | `engine_core.py`, `scheduler.py`, `request.py` | batching, deterministic, stream-safety tests |
| Prefix or paged cache | cache module plus `scheduler.py` | memory, prefix, paged, and untrimmable cache tests |
| Model loading or eviction | `model_registry.py`, `lifecycle.py`, engine wrappers | registry and lifecycle tests |
| Tool calling | parser, `api/tool_calling.py`, `server.py` | parser-specific and promotion tests |
| Reasoning | parser, thinking processor, `server.py` | reasoning, thinking-aware, and streaming tests |
| MCP | `mcp/` and MCP endpoints | MCP security and execution tests |
| Multimodal model | `models/mllm.py`, processor, MLLM scheduler | MLLM and continuous-batching tests |

## Public API documentation rule

Every public module, class, function, and method needs a source docstring. New modules are added to the reference automatically. Private and nested helpers still appear in the line-precise source map even when they are not importable API objects.

Write docstrings that answer:

1. What contract does this object provide?
2. What do non-obvious parameters mean?
3. What is returned or yielded?
4. Which exceptions or lifecycle constraints matter?
5. Which side effects, locks, threads, caches, or external processes are involved?

Avoid duplicating the implementation line by line. Document the behavioral contract and invariants that a caller or maintainer cannot safely infer from the signature.

## Generated files

Do not edit generated files under `site/`. They are recreated by MkDocs and are not committed. Edit source Markdown, Python docstrings, or the documentation scripts instead.

## Security-sensitive areas

Treat MCP execution, remote media fetching, API authentication, subprocess launch, model download, archive or manifest handling, and filesystem cache paths as trust boundaries. Changes in these areas need focused security review in addition to ordinary correctness tests.
