# Python API reference

The API reference is generated directly from every tracked `vllm_mlx/**/*.py` file during the MkDocs build. It is exhaustive by construction and does not import MLX on the Linux documentation runner.

Use the [Python symbol index](../python-symbols.md) to filter every class, function, method, and nested helper by name, kind, or exact callable signature. Each result shows its inputs and links directly to the detailed API record.

## What each module page contains

1. The module's purpose and complete source link.
2. Full signatures, type annotations, parameters, defaults, and return annotations.
3. Parsed docstrings, including parameter descriptions, returns, yields, warnings, examples, and exceptions when supplied by the source.
4. A source map for every class, function, method, nested class, and nested helper.
5. Exact GitHub links in `#Lx-Ly` form, pinned to the immutable commit used for the deployed build.
6. Static implementation facts for every definition, including calls, state reads and writes, return expressions, direct raises, decorators, async work, and yields.
7. Inline source rendering for addressable classes, functions, methods, and module attributes.

Private implementation objects are included because this reference also serves maintainers and coding agents. Public classes and functions must have human-authored docstrings. Private and nested helpers without parameter prose receive their exact AST signature, input kinds, annotations, defaults, direct exceptions, return paths, and conservative implementation facts. The generator does not invent semantic claims that are absent from source. The coverage check fails when a new public object lacks an explanation or a source definition is absent from the reference.

## Machine-readable forms

- [`/llms.txt`](../../llms.txt) is the compact documentation index.
- [`/llms-full.txt`](https://vllm-mlx.is-a.dev/llms-full.txt) contains all hand-written pages and every symbol record in one Markdown file.
- [`/api-inventory.json`](https://vllm-mlx.is-a.dev/api-inventory.json) contains module paths, symbols, kinds, signatures, docstrings, visibility, addressability, and exact source URLs.
- [`/source-inventory.json`](https://vllm-mlx.is-a.dev/source-inventory.json) adds maintenance scripts and runnable examples to the runtime inventory.

Maintenance scripts and examples also have [generated source-reference pages](../source/index.md).

## Navigation

Open **Reference → Python modules → vllm_mlx** in the site navigation. The complete package tree is indexed there, including **models → llm** and every other runtime module. Package overview pages correspond to `__init__.py`; all other module names map directly to their Python paths.

Use [Python symbol index](../python-symbols.md) when you know a class, function, method, parameter, or partial signature but not its module. For example, filtering for `stream_outputs` links directly to that callable's expandable contract.

Generated Markdown mirrors are also available at predictable paths. For example:

```text
https://vllm-mlx.is-a.dev/reference/api/vllm_mlx/server.md
https://vllm-mlx.is-a.dev/reference/api/vllm_mlx/scheduler.md
https://vllm-mlx.is-a.dev/reference/api/vllm_mlx/tool_parsers/qwen_tool_parser.md
```
