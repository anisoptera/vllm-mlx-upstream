# Parsing, tools, and structured output

Model output may contain final text, hidden reasoning, tool calls, or syntax constrained by a schema. vllm-mlx keeps token constraints and text interpretation separate so each concern can be tested independently.

## Reasoning parsers

[`ReasoningParser`](../reference/api/vllm_mlx/reasoning/base.md) defines complete-output and streaming extraction. A parser returns reasoning content, final content, or no delta when the current text is only a control marker.

Implementations cover tagged formats such as Qwen3, DeepSeek-R1, GLM, Gemma, Mistral, Poolside, and channel-based Harmony output. Stateful parsers reset before each request and may flush buffered content at stream finalization.

Streaming implementations receive previous text, current text, and the new delta. They must handle markers split across chunks, repeated markers, missing closing markers, and final markers that contain no user-visible text.

## Thinking-aware token constraints

[`ThinkingAwareLogitsProcessor`](../reference/api/vllm_mlx/constrained/thinking_processor.md) tracks four phases:

1. `IDLE` waits for the reasoning start sequence.
2. `THINKING` counts reasoning tokens.
3. `TRANSITIONING` forces the reasoning end sequence when the budget is exhausted.
4. `CONTENT` delegates to the inner structured-output processor and prevents reasoning control tokens from reappearing.

The processor keeps snapshots because speculative generation can roll token history back. After entering content, state no longer changes and redundant snapshots are avoided.

## Tool parsers

[`ToolParser`](../reference/api/vllm_mlx/tool_parsers/abstract_tool_parser.md) is the common interface for complete and streaming extraction. [`ToolParserManager`](../reference/api/vllm_mlx/tool_parsers/abstract_tool_parser.md) registers parser names and resolves aliases.

Parsers under `vllm_mlx.tool_parsers` cover model-specific JSON, XML, bracketed, token-delimited, and Harmony formats. Auto detection is convenient, but an explicit parser is more predictable in production.

A streaming tool parser can buffer partial markup until it knows whether text is ordinary assistant content or a tool call. The server must not leak half of a tool marker as content, and it must flush valid ordinary text if a suspected marker never completes.

## MCP execution

MCP expands tool calling from parsing into external execution:

- Configuration defines allowed server processes and environment.
- Clients connect to individual MCP servers.
- The manager aggregates tool discovery across servers.
- Tool schemas are converted into the OpenAI representation sent to models.
- The executor applies concurrency limits and dispatches calls.
- Security validation rejects unsafe commands, arguments, paths, or environment values.

MCP crosses an execution trust boundary. Review configuration parsing, command validation, subprocess environment, timeouts, and output size limits when changing this area.

## JSON Schema enforcement

[`JSONSchemaLogitsProcessor`](../reference/api/vllm_mlx/constrained/json_schema_processor.md) adapts lm-format-enforcer to mlx-lm logits. Tokenizer-specific enforcement data is cached by tokenizer identity in [`constrained.cache`](../reference/api/vllm_mlx/constrained/cache.md).

The API accepts JSON object or JSON Schema response formats. The server builds the processor before generation and validates or cleans the final result according to the selected contract. When reasoning is active, schema enforcement applies to final content rather than hidden thinking.

## Streaming terminal contract

OpenAI-style streams end with a chunk carrying the finish reason and final usage, followed by `data: [DONE]`. Anthropic streams use typed content, message-delta, and message-stop events. Responses API streams use typed response lifecycle events.

Parser output and generation completion are independent signals. A terminal model delta can be consumed entirely by a reasoning or tool parser, so the server tracks whether a finish reason has actually been emitted and synthesizes the terminal protocol event when necessary.

## Adding a parser

1. Implement both complete and streaming extraction.
2. Register a stable parser name and any compatibility aliases.
3. Add tests for ordinary content, one tool or reasoning block, multiple blocks, split markers, malformed output, and finalization.
4. Test the server integration for both streaming and non-streaming responses.
5. Document the required CLI flag and a known-compatible model family.
