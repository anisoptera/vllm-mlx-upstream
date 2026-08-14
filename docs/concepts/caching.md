# Caching

vllm-mlx contains several caches because text KV state, paged blocks, multimodal embeddings, and disk persistence have different ownership and reuse rules.

## Cache selection

| Component | Unit of reuse | Primary purpose |
| --- | --- | --- |
| [`PrefixCacheManager`](../reference/api/vllm_mlx/prefix_cache.md) | Whole token prefix entry | Simple in-memory prefix reuse |
| [`BlockAwarePrefixCache`](../reference/api/vllm_mlx/prefix_cache.md) | Token blocks | Prefix reuse aligned with block boundaries |
| [`MemoryAwarePrefixCache`](../reference/api/vllm_mlx/memory_cache.md) | KV cache entry with measured bytes | Enforce a byte or memory-percentage budget |
| [`PagedCacheManager`](../reference/api/vllm_mlx/paged_cache.md) | Reference-counted KV blocks | Share blocks across active and cached sequences |
| [`SSDCacheTier`](../reference/api/vllm_mlx/ssd_cache.md) | Serialized cache entry | Extend prefix reuse beyond RAM |
| [`MLLMPrefixCacheManager`](../reference/api/vllm_mlx/mllm_cache.md) | Multimodal prompt state | Reuse text and multimodal prefill work |
| [`VisionEmbeddingCache`](../reference/api/vllm_mlx/vision_embedding_cache.md) | Encoded image or pixel input | Avoid repeated vision encoding |

## Cache identity

Reusable KV state depends on more than matching token IDs. The memory-aware cache associates entries with a model fingerprint so cache data is not reused across incompatible models. Multimodal caches additionally account for media-derived state. Quantization format and cache layout must remain compatible with the consumer.

When changing model loading, tokenizer selection, or model residency, verify that every cache either receives a distinct identity or is cleared before the new model becomes active.

## Prefix matching

Prefix lookup can be exact or partial:

- Exact match reuses the complete cached token sequence.
- Prefix match reuses a cached sequence that is a prefix of the new prompt.
- Supersequence handling can trim a longer reusable entry when its cache layers support trimming.
- Longest-common-prefix matching can reuse the compatible portion of a related prompt.

The cache must not trim a layer that declares itself non-trimmable. In that case it should choose a safe reusable boundary or decline the hit.

## Memory-aware cache

`MemoryAwarePrefixCache` estimates the bytes held by nested MLX arrays and evicts entries to stay within its configured budget. Its statistics expose entry counts, hit and miss data, eviction reasons, current bytes, and utilization.

Important controls include:

- An explicit memory limit in MiB.
- A percentage of available memory.
- Minimum prefix length.
- Optional cache quantization.
- Optional persistence integration.

All lookup paths must apply the same model-identity, prefix-length, and layer-trimming rules. Cache mutation and accounting must stay coordinated so an entry is charged or subtracted exactly once.

## Paged cache

Paged caching divides tokens into fixed-size blocks. Each block tracks an ID, reference count, parent-dependent hash, free-list links, and per-layer cache data. A chain hash makes the same token block under different prefixes distinguishable.

The free-block queue supports constant-time removal and insertion. The hash map finds reusable blocks. Block tables map each request to the blocks it currently references. Copy-on-write preserves isolation when a request needs to modify a shared block.

Reference counts are the main invariant:

- A block with active owners cannot be returned to the free queue.
- A shared block is released only after the final owner leaves.
- Hash mappings cannot point at a block that has been reassigned.
- Reset and error recovery must rebuild both ownership and lookup structures consistently.

## SSD tier

The SSD tier serializes eligible prefix entries and restores them when memory lookup misses. Storage includes enough metadata to reject incompatible or corrupt entries. Disk I/O should remain outside latency-sensitive event-loop work, and shutdown must close resources after pending persistence completes.

Treat the SSD directory as disposable generated state. Do not share it between model configurations unless their cache identity contract explicitly permits it.

## Cache lifecycle

Cache state may be cleared through the API, reset by the scheduler, persisted during engine unload, or evicted due to memory pressure. A component that starts a thread, file handle, or executor needs a separate close operation. Clearing entries alone does not release background resources.

## Observing cache behavior

Use `GET /v1/cache/stats` for server-visible cache statistics and `DELETE /v1/cache` or `DELETE /v1/cache/prefix` for explicit invalidation. Benchmark both cold and warm runs. A high hit rate is useful only when entries are compatible, memory remains within budget, and tail latency improves.
