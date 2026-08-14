# Request lifecycle

This page follows a generation request through the HTTP server. Exact helper signatures and source are available in the [`vllm_mlx.server` reference](../reference/api/vllm_mlx/server.md).

## 1. Transport and middleware

FastAPI accepts the request and runs the HTTP middleware. Depending on configuration, the request may be subject to bearer authentication, per-client rate limiting, request timing metrics, remote-media safety validation, and endpoint-specific size limits.

Errors raised here are protocol errors. Model generation has not started, so no scheduler request or model lease needs cleanup.

## 2. Request model validation

The server resolves the user-facing `model` field against either the single active engine or the registry-backed model set. Registry serving returns a request-scoped context that holds a lease while generation is active. A missing or incompatible model is rejected before expensive work begins.

Optional endpoints such as embeddings, reranking, and audio apply their own model policy. They may use a preloaded endpoint model, a compatible requested model, or reject the request when the model type does not match.

## 3. Protocol normalization

Each public protocol is converted into the internal chat or prompt representation:

- Chat Completions normalizes messages, media, tools, tool choice, and chat-template keyword overrides.
- Completions accepts an already textual prompt.
- Responses converts input items and prior persisted response items into chat messages, then converts generated output back into Responses API events or objects.
- Anthropic Messages moves system content into the leading system prompt, converts content blocks and tools, and maps stop reasons back to Anthropic values.
- Multimodal requests separate text from image, video, or audio inputs before model preprocessing.

This boundary is also where server defaults are merged with request-level overrides.

## 4. Generation policy construction

The server derives a generation invocation containing token limits, sampling values, stop sequences, chat-template arguments, and optional processors.

Processors may include:

- Logit bias.
- JSON object or JSON Schema enforcement.
- A thinking-aware wrapper that controls reasoning budget and the transition to final content.
- Forced-tool instructions or a model-native tool format.

Tool and reasoning parsers are selected separately from logit processors. Parsers interpret generated text, while processors constrain token selection.

## 5. Engine acquisition

For a resident single model, the lifecycle manager may load the engine lazily and increments activity before returning it. For registry serving, the request acquires a model lease. The server then invokes the common `BaseEngine` contract.

Cleanup callbacks are prepared before generation begins. This ensures cancellation, timeouts, disconnects, and ordinary exceptions all release the same resources.

## 6. Scheduling and generation

`SimpleEngine` performs the model call directly. `BatchedEngine` submits a request to `AsyncEngineCore`, which creates internal request state and places it in the scheduler waiting queue.

The scheduler admits work according to capacity, creates or reuses KV cache state, and advances the active batch. Output collectors turn scheduler outputs into complete results or async deltas for each caller.

## 7. Streaming transformation

Streaming endpoints process every generation delta in this order:

1. Track accumulated and incremental model text.
2. Extract reasoning content if a reasoning parser is active.
3. Extract or buffer tool-call markup if a tool parser is active.
4. Apply response-format cleanup where required.
5. Encode the protocol-specific event or Server-Sent Event payload.
6. Update usage and finish-reason state.

A parser may consume a marker and return no user-visible delta. The stream still has to flush buffered parser content, emit a terminal finish reason and usage when the protocol requires them, and finally emit `[DONE]` for OpenAI-style streams.

## 8. Completion, timeout, or disconnect

Normal completion records the model finish reason, usually `stop` or `length`. A timeout cancels the internal request and returns the server's timeout response. A client disconnect follows the same cancellation path without continuing unnecessary generation.

The request ID routes make cancellation explicit:

- `POST /v1/requests/{request_id}/cancel` asks the active engine to cancel.
- `DELETE /v1/requests/{request_id}` is the deletion alias.

Cancellation is idempotent at the HTTP boundary, but internal cleanup must still distinguish an unknown request from a request that has already reached a terminal state.

## 9. Final cleanup

The response cleanup path releases model activity or the model lease, detaches request-local parser state, records metrics, and lets the scheduler reclaim request state. Streaming generators must perform this work in `finally` blocks because the client can disconnect between any two yielded events.

## Lifecycle invariants

- Validate before scheduling whenever possible.
- Acquire the model before touching tokenizer-derived request state.
- Release the same model context that was acquired, even if the global active engine changes.
- Never emit content after the terminal protocol event.
- Never omit a terminal reason because a parser consumed the final textual delta.
- Keep final usage tied to the last generation output, not to a parser-only delta.
- Treat disconnect, timeout, cancellation, and exception cleanup as first-class paths.
