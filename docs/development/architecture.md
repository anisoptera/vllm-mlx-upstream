# Architecture

vllm-mlx is a layered inference server for Apple Silicon. Protocol code is separated from model execution, concurrent scheduling, caching, model ownership, and model-specific compatibility patches.

## System overview

```text
OpenAI and Anthropic clients
            |
      FastAPI server
            |
  protocol normalization
            |
       BaseEngine
       /        \
SimpleEngine  BatchedEngine
                   |
             AsyncEngineCore
                   |
               Scheduler
                   |
        model wrappers and caches
                   |
 mlx-lm | mlx-vlm | mlx-audio | mlx-embeddings
                   |
              MLX / Metal
```

## Primary layers

### API layer

[`server.py`](../reference/api/vllm_mlx/server.md) owns the FastAPI process, route handlers, authentication, rate limits, endpoint policy, model acquisition, streaming protocol output, and shutdown integration. Pydantic requests, responses, and protocol adapters live in [`api/`](../reference/api/vllm_mlx/api/index.md).

### Engine layer

[`BaseEngine`](../reference/api/vllm_mlx/engine/base.md) is the common contract used by the server. [`SimpleEngine`](../reference/api/vllm_mlx/engine/simple.md) calls model wrappers directly. [`BatchedEngine`](../reference/api/vllm_mlx/engine/batched.md) delegates concurrent work to [`AsyncEngineCore`](../reference/api/vllm_mlx/engine_core.md).

### Scheduler layer

[`Scheduler`](../reference/api/vllm_mlx/scheduler.md) manages waiting and running requests, mlx-lm `BatchGenerator` state, prefill and decode steps, cache attachment, cancellation, recovery, and terminal outputs. The engine core routes scheduler results into per-request output collectors.

Multimodal batching uses separate scheduler, batch generator, processor, and cache components because vision inputs and cache shapes differ from text-only inference.

### Model layer

Text generation uses [`MLXLanguageModel`](../reference/api/vllm_mlx/models/llm.md). Vision-language generation uses [`MLXMultimodalLM`](../reference/api/vllm_mlx/models/mllm.md). Embedding, reranking, STT, and TTS engines remain separate optional services with endpoint-specific compatibility policy.

### Cache layer

The scheduler can use legacy prefix entries, memory-aware entries, block-aware prefix reuse, or paged KV blocks, with optional SSD persistence. Multimodal and vision-embedding caches cover different preprocessing state. See [Caching](../concepts/caching.md) for invariants and selection guidance.

### Parser and constraint layer

Reasoning parsers separate hidden thinking from final content. Tool parsers convert model-family syntax into protocol tool calls. Constrained processors enforce JSON Schema and reasoning-budget transitions at the logits level. See [Parsing and Structured Output](../concepts/parsing-and-structured-output.md).

### Model ownership layer

[`ModelManager`](../reference/api/vllm_mlx/model_registry.md) provides registry-backed multi-model loading, memory budgets, eviction, and request leases. [`ResidencyManager`](../reference/api/vllm_mlx/lifecycle.md) provides lazy loading and idle unload for the default model.

## Request flow

1. Middleware authenticates, meters, and validates transport policy.
2. The endpoint validates the request model and protocol schema.
3. Protocol input is normalized into a prompt or internal message list.
4. The server builds sampling, reasoning, tool, and structured-output state.
5. The request acquires its model or resident engine.
6. The simple engine executes directly, or the batched engine submits to the scheduler.
7. Deltas pass through reasoning and tool parsers before protocol encoding.
8. Terminal reason and usage are emitted even when the final textual delta was suppressed.
9. Completion, error, timeout, cancellation, and disconnect paths release request and model state.

See [Request Lifecycle](../concepts/request-lifecycle.md) for the complete path.

## Concurrency invariants

- MLX generation streams are thread-local. Scheduler steps stay on one bound worker thread.
- One model cannot be owned by incompatible active engines unless ownership is transferred through the registry contract.
- A request-scoped model lease prevents eviction during generation.
- Request collectors receive one terminal result.
- Streaming cleanup runs in `finally` paths because clients can disconnect between yields.

## Cache invariants

- Cache identity includes model compatibility, not only token equality.
- Expired entries cannot satisfy exact or partial prefix lookups.
- Memory accounting changes once for each inserted or removed entry.
- Paged block reference counts agree with block-table ownership and free-list membership.
- Non-trimmable layers are never shortened to manufacture a prefix hit.
- Timers, threads, executors, and disk resources have explicit shutdown paths.

## Extension points

| Extension | Primary location | Required validation |
| --- | --- | --- |
| New HTTP field or event | `api/` and `server.py` | Protocol model and server tests |
| New tool format | `tool_parsers/` | Complete, streaming, split-marker, and server tests |
| New reasoning format | `reasoning/` | Complete, streaming, finalization, and server tests |
| New model family | model detection, wrapper, optional patch | Loader, dispatch, generation, and cache tests |
| New cache policy | cache module and scheduler | Hit, miss, eviction, concurrency, reset, and recovery tests |
| New endpoint model | engine plus endpoint policy | Compatibility, lazy load, limit, and error tests |

## Further reading

- [Runtime Architecture](../concepts/runtime-architecture.md)
- [Scheduling and Batching](../concepts/scheduling-and-batching.md)
- [Models and Modalities](../concepts/models-and-modalities.md)
- [Codebase Map](codebase-map.md)
- [Complete Python API](../reference/api/index.md)
