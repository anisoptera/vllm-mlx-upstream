# vllm-mlx documentation

<div class="vllm-hero" markdown>

## OpenAI and Anthropic compatible inference on Apple Silicon

Serve text, image, video, audio, embeddings, and reranking from one local process. vllm-mlx combines continuous batching, efficient KV caches, tool calling, structured output, and model residency with native MLX acceleration.

```bash
pip install vllm-mlx
vllm-mlx serve \
  mlx-community/Llama-3.2-3B-Instruct-4bit \
  --port 8000
```

[Get started](getting-started/quickstart.md){ .md-button .md-button--primary }
[Browse the Python API](reference/api/index.md){ .md-button }

</div>

## Start here

<div class="grid cards" markdown>

-   **Install and serve**

    Set up the supported environment and start your first local model.

    [Installation](getting-started/installation.md) · [Quickstart](getting-started/quickstart.md)

-   **Connect a client**

    Use OpenAI, Anthropic, Responses, audio, embedding, reranking, or MCP routes.

    [Server guide](guides/server.md) · [HTTP API](reference/http-api.md)

-   **Use the Python API**

    Integrate generation directly and inspect exact runtime interfaces.

    [Python guide](guides/python-api.md) · [API reference](reference/api/index.md)

-   **Understand the runtime**

    Follow requests through scheduling, batching, caches, parsers, and model execution.

    [Core concepts](concepts/index.md) · [Architecture](concepts/runtime-architecture.md)

-   **Find exact source behavior**

    Search every module, class, function, method, CLI option, and source range.

    [Source inventory](reference/source/index.md) · [CLI options](reference/cli-options.md)

-   **Work with LLMs and agents**

    Load compact, full-corpus, or JSON documentation designed for machine context.

    [`llms.txt`](llms.txt) · [Agent guide](development/agent-guide.md)

</div>

## What you can run

- **Language models:** text generation, reasoning, structured output, and tool calling
- **Multimodal models:** image and video understanding
- **Audio models:** speech-to-text and text-to-speech
- **Embedding models:** OpenAI-compatible vector generation
- **Rerankers:** query-document relevance scoring
- **Model registries:** multiple resident or dynamically loaded models

## Core runtime capabilities

- Continuous batching and paged KV cache management
- Prefix reuse, prompt warmup, and optional SSD cache support
- OpenAI, Anthropic, Responses, audio, reranking, and MCP protocols
- Reasoning parsers, tool parsers, constrained decoding, and JSON schemas
- Metrics, health checks, cancellation, lifecycle control, and model residency

## Requirements

- macOS on Apple Silicon
- Python 3.10 or newer
- At least 8 GB of unified memory

See the [installation guide](getting-started/installation.md) for supported dependency and environment details.
