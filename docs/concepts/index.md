# Core concepts

These pages explain how vllm-mlx works beneath the command line and HTTP APIs. Use them when choosing an engine mode, debugging latency or memory behavior, or changing runtime code.

## Runtime and requests

- [Runtime architecture](runtime-architecture.md) describes the API, engine, scheduler, model, parser, and hardware layers.
- [Request lifecycle](request-lifecycle.md) traces one request from validation through terminal output and cleanup.
- [Scheduling and batching](scheduling-and-batching.md) explains queues, continuous batching, worker-thread affinity, and output collection.

## Models and memory

- [Caching](caching.md) compares the legacy prefix cache, memory-aware cache, paged cache, multimodal cache, and SSD tier.
- [Models and modalities](models-and-modalities.md) explains text, vision, audio, embeddings, reranking, model registration, and residency.

## Output interpretation

- [Parsing and structured output](parsing-and-structured-output.md) covers reasoning extraction, tool-call parsers, JSON Schema enforcement, streaming, and terminal events.

For individual Python objects, continue to the [generated API reference](../reference/api/index.md). Every source definition is indexed there with an exact line link.
