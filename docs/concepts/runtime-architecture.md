# Runtime architecture

vllm-mlx adapts vLLM-style serving concepts to MLX. The server owns protocol compatibility and request policy, engines own generation, schedulers own concurrent decode state, and model wrappers bridge to the MLX ecosystem.

## Layer map

```text
OpenAI SDKs        Anthropic SDKs        curl / custom clients
      |                  |                        |
      +------------------+------------------------+
                         |
                 FastAPI server.py
       auth, limits, validation, protocol adapters
                         |
                BaseEngine contract
                  /             \
           SimpleEngine      BatchedEngine
             direct          AsyncEngineCore
                                  |
                              Scheduler
                 queues, BatchGenerator, KV caches
                                  |
             mlx-lm | mlx-vlm | mlx-audio | mlx-embeddings
                                  |
                        MLX and Metal
```

## API and protocol layer

[`vllm_mlx.server`](../reference/api/vllm_mlx/server.md) creates the FastAPI application and implements the OpenAI-compatible, Anthropic-compatible, audio, embedding, reranking, cache, status, and MCP routes. Its main responsibilities are:

1. Authenticate and rate-limit requests when configured.
2. Validate the requested model and endpoint-specific limits.
3. Normalize OpenAI, Anthropic, Responses API, multimodal, and tool inputs.
4. Resolve the active model and acquire a model lease when registry serving is enabled.
5. Construct sampling, reasoning, structured-output, and tool-parser state.
6. Invoke the selected engine and translate `GenerationOutput` values into protocol responses.
7. Preserve terminal reasons, usage, cancellation, and model release across normal and exceptional exits.

The Pydantic wire models live in [`vllm_mlx.api`](../reference/api/vllm_mlx/api/index.md). Protocol conversion is deliberately separate from model execution so the same engines can support multiple client contracts.

## Engine layer

[`BaseEngine`](../reference/api/vllm_mlx/engine/base.md) defines the common async contract for loading, stopping, text generation, chat generation, streaming, cache management, and tokenizer access.

Two primary implementations serve different workloads:

| Engine | Execution model | Best fit | Main tradeoff |
| --- | --- | --- | --- |
| `SimpleEngine` | Direct calls into model wrappers | One active user, lowest orchestration overhead | Serialized generation paths do not continuously batch independent requests |
| `BatchedEngine` | Delegates to `AsyncEngineCore` and a scheduler | Concurrent serving and aggregate throughput | More queue, cache, and lifecycle state |

Both return [`GenerationOutput`](../reference/api/vllm_mlx/engine/base.md), which carries text, token IDs, token counts, finish reason, incremental text, completion state, and speculative decoding counters.

## Continuous-batching core

[`EngineCore`](../reference/api/vllm_mlx/engine_core.md) owns a model, tokenizer, scheduler, output collectors, and request completion events. [`AsyncEngineCore`](../reference/api/vllm_mlx/engine_core.md) wraps it with the async interface used by `BatchedEngine`.

The core runs scheduler steps on one dedicated worker thread. MLX streams are thread-local, so generation streams are rebound inside that worker before decode. This thread-affinity requirement is a correctness invariant, not only a performance choice.

## Scheduler layer

[`Scheduler`](../reference/api/vllm_mlx/scheduler.md) turns waiting requests into a running batch, advances mlx-lm's `BatchGenerator`, collects deltas, and finalizes completed or failed requests. Its configuration controls maximum sequences, batch sizes, prefill step size, scheduling policy, cache strategy, memory limits, and optional SSD tiering.

Multimodal continuous batching uses [`MLLMScheduler`](../reference/api/vllm_mlx/mllm_scheduler.md), [`MLLMBatchGenerator`](../reference/api/vllm_mlx/mllm_batch_generator.md), and [`MultimodalProcessor`](../reference/api/vllm_mlx/multimodal_processor.md). These components preserve image and video preprocessing state while applying the same request lifecycle concepts.

## Model layer

- [`MLXLanguageModel`](../reference/api/vllm_mlx/models/llm.md) wraps text-only mlx-lm loading and generation.
- [`MLXMultimodalLM`](../reference/api/vllm_mlx/models/mllm.md) wraps mlx-vlm models and multimodal preprocessing.
- [`EmbeddingEngine`](../reference/api/vllm_mlx/embedding.md) serves vector embeddings.
- [`RerankEngine`](../reference/api/vllm_mlx/rerank.md) serves cross-encoder scores.
- [`STTEngine`](../reference/api/vllm_mlx/audio/stt.md) and [`TTSEngine`](../reference/api/vllm_mlx/audio/tts.md) provide optional audio routes.

Runtime patches under [`vllm_mlx.patches`](../reference/api/vllm_mlx/patches/index.md) adapt specific upstream architectures. They should stay model-specific and must not silently alter unrelated model families.

## Parser and constraint layer

Reasoning parsers split thinking content from final content. Tool parsers translate model-specific call syntax into OpenAI-compatible tool deltas. Constrained processors modify logits to enforce JSON Schema or to control a reasoning model's transition into final content.

These components can suppress or buffer individual deltas. Streaming code must therefore treat parser finalization and the terminal finish-reason chunk as independent obligations.

## Ownership boundaries

Several resources have explicit owners:

| Resource | Owner | Release point |
| --- | --- | --- |
| Model and tokenizer | Engine or registry-managed loaded model | Engine stop, registry eviction, or residency unload |
| Request state | Scheduler and engine core | Completion, cancellation, or failure |
| Model lease | Request model context | Response cleanup, including streaming disconnects |
| Prefix and paged KV state | Scheduler cache managers | Cache clear, reset, eviction, or engine close |
| Parser state | Individual request stream | Terminal flush or request cleanup |
| MCP processes | MCP manager | Server lifespan shutdown |

Keeping these boundaries intact prevents model eviction during generation, stale parser state after reload, leaked request futures, and cache state surviving an incompatible model.

## Static documentation on Linux

The documentation pipeline parses source with the Python AST and Griffe. It does not import `vllm_mlx`, so GitHub Pages can build on Linux without MLX. Runtime validation remains an Apple Silicon responsibility.
