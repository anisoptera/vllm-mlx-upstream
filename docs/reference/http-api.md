# HTTP API reference

The server implements OpenAI-compatible, Anthropic-compatible, operational, cache, audio, reranking, and MCP routes in [`vllm_mlx.server`](api/vllm_mlx/server.md). Request and response schemas are documented in [`vllm_mlx.api`](api/vllm_mlx/api/index.md).

Default base URL:

```text
http://127.0.0.1:8000
```

When `--api-key` is configured, protected routes require `Authorization: Bearer <key>`.

## Generation protocols

| Method | Path | Purpose | Implementation |
| --- | --- | --- | --- |
| `POST` | `/v1/completions` | OpenAI-compatible text completions | [`create_completion`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4763-L4909) |
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat, tools, reasoning, and multimodal input | [`create_chat_completion`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4916-L5114) |
| `POST` | `/v1/responses` | OpenAI-compatible Responses API | [`create_response`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L5194-L5214) |
| `POST` | `/v1/messages` | Anthropic-compatible Messages API | [`create_anthropic_message`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L5357-L5578) |
| `POST` | `/v1/messages/count_tokens` | Count Anthropic message tokens | [`count_anthropic_tokens`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L5585-L5666) |

OpenAI streaming uses Server-Sent Events and terminates with `data: [DONE]`. Anthropic and Responses API streams emit their protocol-specific typed terminal events.

## Vector and ranking protocols

| Method | Path | Purpose | Implementation |
| --- | --- | --- | --- |
| `POST` | `/v1/embeddings` | OpenAI-compatible embeddings | [`create_embeddings`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3787-L3908) |
| `POST` | `/v1/rerank` | Score query-document relevance | [`rerank_documents`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3920-L4038) |

## Audio protocols

| Method | Path | Purpose | Implementation |
| --- | --- | --- | --- |
| `POST` | `/v1/audio/transcriptions` | Speech-to-text transcription | [`create_transcription`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4130-L4196) |
| `POST` | `/v1/audio/speech` | Text-to-speech synthesis | [`create_speech`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4200-L4254) |
| `GET` | `/v1/audio/voices` | List available voices for a TTS model | [`list_voices`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4258-L4267) |

Upload and input limits are applied before model execution. Audio dependencies are installed separately with the `audio` extra.

## MCP protocols

| Method | Path | Purpose | Implementation |
| --- | --- | --- | --- |
| `GET` | `/v1/mcp/tools` | List tools discovered from configured MCP servers | [`list_mcp_tools`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4047-L4063) |
| `GET` | `/v1/mcp/servers` | List MCP server connection state | [`list_mcp_servers`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4067-L4084) |
| `POST` | `/v1/mcp/execute` | Execute a named MCP tool | [`execute_mcp_tool`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L4088-L4117) |

MCP execution is a trust boundary. Use explicit server configuration and review the [MCP guide](../guides/mcp-tools.md) before exposing it to untrusted clients.

## Models and operations

| Method | Path | Purpose | Implementation |
| --- | --- | --- | --- |
| `GET` | `/health` | Basic health and residency readiness | [`health`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3489-L3544) |
| `GET` | `/metrics` | Prometheus metrics when enabled | [`metrics`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3476-L3485) |
| `GET` | `/v1/status` | Server, model, engine, and lifecycle status | [`status`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3548-L3597) |
| `GET` | `/v1/models` | List API-visible model IDs | [`list_models`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3760-L3775) |
| `POST` | `/v1/requests/{request_id}/cancel` | Cancel active generation | [`cancel_request`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3720-L3747) |
| `DELETE` | `/v1/requests/{request_id}` | Delete or cancel active generation | [`delete_request`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3754-L3756) |

## Cache operations

| Method | Path | Purpose | Implementation |
| --- | --- | --- | --- |
| `GET` | `/v1/cache/stats` | Return active engine cache statistics | [`cache_stats`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3601-L3627) |
| `DELETE` | `/v1/cache` | Clear all supported engine caches | [`clear_cache`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3631-L3659) |
| `DELETE` | `/v1/cache/prefix` | Clear the prefix cache | [`clear_prefix_cache`](https://github.com/waybarrios/vllm-mlx/blob/gh-pages/vllm_mlx/server.py#L3663-L3713) |

## Error behavior

Validation failures use HTTP 4xx responses. Authentication failures return 401. Rate limits return 429. Busy, timeout, model-loading, and internal generation failures are mapped by the endpoint to a protocol-compatible error body where possible.

For complete fields and validation rules, inspect the Pydantic model reference rather than inferring support from an upstream OpenAI or Anthropic schema.
