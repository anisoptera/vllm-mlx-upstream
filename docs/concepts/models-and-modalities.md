# Models and modalities

vllm-mlx routes several model families through one server while keeping their loading and preprocessing contracts separate.

## Text generation

[`MLXLanguageModel`](../reference/api/vllm_mlx/models/llm.md) wraps mlx-lm for text-only generation. It owns the model, tokenizer, chat template behavior, and generation parameters used by the simple engine. Continuous batching uses the model and tokenizer through the engine core and scheduler.

## Vision-language generation

[`MLXMultimodalLM`](../reference/api/vllm_mlx/models/mllm.md) wraps mlx-vlm. [`MultimodalProcessor`](../reference/api/vllm_mlx/multimodal_processor.md) extracts and prepares images or videos while retaining the textual conversation required by the chat template.

Model-specific patches adapt attention or multi-token prediction implementations that need different mask, cache, or hidden-state handling in a batch. Patch activation must be narrow and reversible because upstream mlx-vlm behavior can change independently.

## Audio

Audio endpoints are optional because mlx-audio and its model families have separate dependencies. [`STTEngine`](../reference/api/vllm_mlx/audio/stt.md) handles transcription models. [`TTSEngine`](../reference/api/vllm_mlx/audio/tts.md) handles speech synthesis and voice selection.

[`audio_limits`](../reference/api/vllm_mlx/audio_limits.md) enforces upload and text limits before expensive processing. The API layer should reject oversized content before loading an optional model or allocating a large buffer.

## Embeddings and reranking

[`EmbeddingEngine`](../reference/api/vllm_mlx/embedding.md) uses mlx-embeddings to produce vectors. [`RerankEngine`](../reference/api/vllm_mlx/rerank.md) uses a BERT-family sequence-classification forward pass implemented in [`rerank_forward`](../reference/api/vllm_mlx/rerank_forward.md).

These endpoints apply model compatibility policies independently from generation. A chat model name should not silently select an incompatible embedding or reranking model.

## Model detection

The registry and API utilities inspect model identifiers and configuration metadata to classify text, vision, embedding, reranking, STT, and TTS workloads. Name heuristics are fallbacks. Configuration metadata and successful loader selection are stronger signals.

When adding a model family:

1. Confirm which upstream loader owns it.
2. Add the narrowest detection rule.
3. Keep text and multimodal classification mutually coherent.
4. Add loader and endpoint-policy tests.
5. Document required optional dependencies and a known model identifier.

## Registry-backed serving

[`ModelManager`](../reference/api/vllm_mlx/model_registry.md) loads registered models under a memory budget. A registry entry describes the source model and serving defaults. A loaded model owns its engine and accounting metadata. A request obtains a [`ModelLease`](../reference/api/vllm_mlx/model_registry.md) so eviction cannot remove a model while it is in use.

The manager estimates whether a candidate fits, chooses an eviction candidate according to policy, loads the model, and updates budget state. Loading and eviction must be serialized because device memory and engine ownership are shared resources.

## Single-model residency

[`ResidencyManager`](../reference/api/vllm_mlx/lifecycle.md) controls lazy loading and automatic unload of the default model. Its state machine distinguishes unloaded, loading, loaded, and unloading behavior while tracking activity.

Key invariants:

- Concurrent first requests share one load operation.
- An active request prevents idle unload.
- Unload persists eligible state before stopping the engine.
- Reload invalidates tokenizer-derived parser instances.
- Server shutdown closes the current engine even if background lifecycle work is active.

## Model workflow

[`model_workflow`](../reference/api/vllm_mlx/model_workflow.md) implements inspect, acquire, convert, register, and qualify operations. Its manifests make source revision, file inventory, conversion recipe, and output artifacts auditable.

Use inspection before download or conversion. Use acquisition when a complete local artifact is required. Use conversion for upstream weights that are not already in MLX format. Use qualification to exercise the resulting artifact against the intended server behavior.
