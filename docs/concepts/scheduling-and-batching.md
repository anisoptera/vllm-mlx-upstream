# Scheduling and continuous batching

Continuous batching keeps a changing set of requests in one decode loop. New requests can join as capacity becomes available, and completed requests leave without waiting for the original batch to finish.

## Core objects

| Object | Responsibility |
| --- | --- |
| [`Request`](../reference/api/vllm_mlx/request.md) | Prompt tokens, sampling parameters, status, generated tokens, cache state, and timing |
| [`SchedulerConfig`](../reference/api/vllm_mlx/scheduler.md) | Capacity, batching, prefill, cache, and scheduling controls |
| [`Scheduler`](../reference/api/vllm_mlx/scheduler.md) | Waiting and running sets, cache attachment, `BatchGenerator` steps, completion, and recovery |
| [`EngineCore`](../reference/api/vllm_mlx/engine_core.md) | Background loop, request submission, output collectors, and model ownership |
| [`RequestOutputCollector`](../reference/api/vllm_mlx/output_collector.md) | Low-latency aggregation of scheduler outputs for one request |
| [`AsyncEngineCore`](../reference/api/vllm_mlx/engine_core.md) | Async facade used by the batched engine |

## Admission and queues

New requests begin in a waiting queue. A scheduler step admits requests while respecting `max_num_seqs`, prefill capacity, and the selected scheduling policy. First-come-first-served is the default; priority scheduling uses the request priority when enabled.

Admission also resolves reusable prefix state. A cache hit reduces the number of prompt tokens that require prefill. Cache state must match the current model and remain valid for the cache implementation in use.

## Prefill and decode

Prefill processes prompt tokens and creates KV state. Decode advances active sequences one or more tokens at a time. `prefill_batch_size`, `completion_batch_size`, and `prefill_step_size` control the work submitted to mlx-lm's `BatchGenerator`.

Large prefill steps can improve throughput but increase latency for other queued work and raise peak memory. Smaller steps improve interleaving at the cost of more scheduler overhead.

## Worker-thread affinity

The engine core uses one dedicated worker thread for scheduler steps. MLX generation streams are thread-local, so the worker binds its streams before touching the model. Moving scheduler work between arbitrary executors can produce stream ownership errors even when Python state appears thread-safe.

The engine includes a narrow recovery path for recognized stream-thread failures. It rebuilds affected cache or batch state and reschedules active requests. This is a fallback, not permission to ignore thread affinity.

## Output delivery

Each scheduler step can produce deltas for several request IDs. The engine core routes each output to its request collector. Streaming callers consume incremental text, while non-streaming callers wait for the collector to assemble a terminal `RequestOutput` or `GenerationOutput`.

`stream_interval` controls how often token deltas cross the engine boundary. A value of one minimizes token latency. Larger values reduce Python and serialization overhead at the cost of chunk latency.

## Completion and cancellation

A request leaves the running set when it reaches a stop token, token limit, explicit cancellation, or error. The scheduler must finalize cache state, detach the sequence from `BatchGenerator`, notify the matching collector, and make capacity available to waiting requests.

Cancellation can race a scheduler step. Code that changes request state should preserve these properties:

- A request has one terminal outcome.
- A collector is notified exactly once.
- Removed sequences cannot reappear in a later batch step.
- Cache state is stored only when it is safe and complete enough to reuse.

## Multimodal batching

Multimodal scheduling has additional preprocessing and cache inputs. Image or video embeddings can be reused separately from text KV state. The multimodal batch generator tracks prompt and generation throughput while adapting model-specific cache behavior.

Use the multimodal scheduler only for wrappers that support its cache and batch contracts. Model-specific runtime patches under `vllm_mlx.patches` extend support for architectures whose upstream attention or MTP implementations do not accept batched cache objects directly.

## Tuning sequence

When tuning a server, change one limit at a time:

1. Establish a representative workload with `bench-serve`.
2. Set a safe memory budget and cache mode.
3. Increase `max_num_seqs` until throughput stops improving or tail latency becomes unacceptable.
4. Tune prefill and completion batch sizes.
5. Tune `stream_interval` for the client latency target.
6. Re-run with cache-warm and cache-cold cases.

Throughput, time to first token, inter-token latency, memory pressure, and fairness should be evaluated together.
