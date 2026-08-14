# Codebase map

This map identifies the primary owner of each runtime concern. Use the generated [Python API reference](../reference/api/index.md) for every object and line-precise source links.

## Entry points

| Path | Responsibility |
| --- | --- |
| `vllm_mlx/cli.py` | `vllm-mlx` command tree, server configuration, model workflow, and benchmark dispatch |
| `vllm_mlx/server.py` | FastAPI application, route handlers, protocol streaming, lifecycle integration, and process entry point |
| `vllm_mlx/benchmark.py` | Local model benchmark entry point |
| `vllm_mlx/bench_serve.py` | HTTP serving benchmark and workload contract runner |
| `vllm_mlx/gradio_app.py` | Multimodal Gradio chat application |
| `vllm_mlx/gradio_text_app.py` | Text-only Gradio chat application |
| `vllm_mlx/plugin.py` | vLLM out-of-tree MLX platform registration |

## API contracts

`vllm_mlx/api/` contains Pydantic wire models and conversion helpers:

- `models.py` defines OpenAI-compatible requests and responses.
- `responses_models.py` defines Responses API items and streaming events.
- `anthropic_models.py` defines Anthropic Messages types.
- `anthropic_adapter.py` converts Anthropic content and tools to internal OpenAI-style messages and converts results back.
- `prompt_canonicalize.py` normalizes system prompts.
- `streaming.py` provides a low-overhead SSE JSON encoder.
- `tool_calling.py` contains protocol-level tool utilities.
- `harmony_tools.py` renders Harmony tool definitions.
- `utils.py` contains shared content and model-detection helpers.

## Engines and request state

- `engine/base.py` is the stable engine interface and shared generation output.
- `engine/simple.py` handles direct text and multimodal generation.
- `engine/batched.py` adapts the continuous-batching core to `BaseEngine`.
- `engine/chat_template_safety.py` normalizes messages before Jinja templates.
- `engine_core.py` owns the background scheduler loop, request collectors, and model ownership.
- `request.py` defines request status, sampling parameters, request state, and scheduler output.
- `output_collector.py` maps scheduler deltas and terminal results back to individual async callers.

## Scheduling and inference

- `scheduler.py` runs text continuous batching with mlx-lm `BatchGenerator`.
- `mllm_scheduler.py` schedules multimodal requests.
- `mllm_batch_generator.py` advances multimodal batches and reports throughput.
- `model_runner.py` exposes the vLLM-facing MLX model runner.
- `mlx_streams.py` owns MLX thread-stream binding helpers.
- `multimodal_processor.py` prepares text, image, and video model inputs.

## Model ownership and workflow

- `models/llm.py` wraps text models.
- `models/mllm.py` wraps vision-language models.
- `model_registry.py` provides registry-backed loading, leases, memory budgets, and eviction.
- `lifecycle.py` provides lazy load and automatic idle unload for the default model.
- `model_workflow.py` implements inspect, acquire, convert, register, and qualify operations.
- `text_model_from_vlm.py` reconstructs an mlx-lm text model from mlx-vlm-loaded weights.
- `endpoint_model_policies.py` resolves compatible optional-endpoint models.

## Caches

- `prefix_cache.py` implements entry and block-aware prefix reuse.
- `memory_cache.py` implements memory-budgeted prefix reuse and optional quantization.
- `paged_cache.py` implements reference-counted block storage and sharing.
- `ssd_cache.py` implements serialized disk tiering.
- `mllm_cache.py` stores multimodal prompt state.
- `vision_embedding_cache.py` stores reusable vision preprocessing results.
- `utils/mamba_cache.py` adapts state-space model caches to batching.

## Output interpretation

- `reasoning/` contains complete and streaming reasoning parsers.
- `tool_parsers/` contains model-family-specific tool-call parsers and the parser registry.
- `constrained/` contains tokenizer enforcement caches, JSON Schema logits processing, and the thinking state machine.
- `utils/harmony_render.py` renders GPT-OSS Harmony prompts.
- `api/harmony_tools.py` converts tool definitions for Harmony.

## Optional model services

- `audio/` contains preprocessing, STT, and TTS engines.
- `audio_limits.py` validates optional audio route inputs.
- `embedding.py` loads and serves embedding models.
- `rerank.py` loads and serves reranking models.
- `rerank_forward.py` implements the MLX sequence-classification forward pass.

## MCP

- `mcp/config.py` loads and validates server definitions.
- `mcp/client.py` manages one MCP connection.
- `mcp/manager.py` coordinates all configured servers.
- `mcp/tools.py` converts tool schemas.
- `mcp/executor.py` applies concurrency and invokes tools.
- `mcp/security.py` validates commands, paths, arguments, and environment.
- `mcp/types.py` defines MCP-facing data structures.

## Model-specific compatibility

`patches/` contains narrow runtime adaptations for Gemma 4, GLM-4V MoE, Qwen3.5, and Qwen3-Next MTP. `specprefill.py` contains sparse-prefill logic. `optimizations.py` reports hardware and selects safe optimization values.

## Tests

Tests are organized by behavior rather than mirroring every module. Search for the public object or endpoint first, then inspect the nearest regression file. Linux CI covers static checks and non-MLX behavior. Apple Silicon CI covers model, scheduler, cache, server, and streaming paths that require MLX.

## Documentation tools

- `scripts/docs_inventory.py` parses tracked Python source without importing it.
- `scripts/gen_api_reference.py` creates module pages and source maps.
- `scripts/check_docs_coverage.py` enforces module, symbol, and public-docstring coverage.
- `scripts/mkdocs_hooks.py` creates Markdown mirrors, `llms-full.txt`, and `api-inventory.json`.
- `.github/workflows/docs.yml` validates pull requests targeting `gh-pages` and deploys pushes from that branch.
