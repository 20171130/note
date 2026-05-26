Escalate distributed-training strategy only when the lower rung OOMs. Each rung is strictly more complex than the previous; pay the cost when it pays back, not before.

# Per-GPU memory math (bf16 weights, AdamW)

At bf16 with AdamW the per-GPU resident state (params + bf16 grads + fp32 master + Adam m/v) is ~12 bytes/param, ignoring activations and KV cache.

| Model | Per-GPU state | Fits 80 GB H100 (DDP)? |
|-------|---------------|-------------------------|
| 0.6B  | ~10 GB        | yes, easily             |
| 1.5B  | ~24 GB        | yes                     |
| 3B    | ~48 GB        | tight; depends on ctx + activations |
| 7B    | ~112 GB       | no — needs sharding     |
| 14B+  | —             | no — TP/PP starts paying back |

Activation memory adds on top and depends on context length × batch × layer count. At long context (≥8k) the 3B boundary moves down. Profile before committing.

# Three rungs

1. DDP. Single launcher line: `accelerate launch --multi_gpu --mixed_precision=bf16 ...`. Replicated weights, all-reduce grads. Fits ≤ ~3B at bf16 + AdamW. No model code changes.
2. FSDP / ZeRO-3 via accelerate. Same trainer, same model code, one extra flag: `accelerate launch --config_file fsdp.yaml ...` with a 5-line FSDP YAML (transformer auto-wrap on the decoder layer class, bf16 autocast, no offload, fp32 master). Shards params + grads + optimizer states across ranks. Covers ~3-13B. Essentially free — most non-trivial cost is a one-time checkpoint shard-format decision.
3. Megatron-LM (TP/PP). Required when activation memory dominates even after FSDP sharding, or when single-layer matmul becomes the per-step bottleneck (typically ≥13B). Costs: custom non-HF model wiring; pipeline schedule complexity; container/build-env quirks (slime.sif). Pay this cost ONCE, when it actually pays back.

# Anti-patterns

- DDP → Megatron skipping FSDP. Megatron's value-add is tensor + pipeline parallelism, not parameter sharding (FSDP/ZeRO-3 already covers that). Skipping FSDP means paying Megatron's integration cost for problems FSDP would solve at zero marginal complexity.
- Pre-configuring FSDP "to be safe" for a model that fits under DDP. FSDP adds shard-aware checkpointing, marginally slower step time, and harder debugging — buys nothing if state fits per-rank. See [log 2026-05-26 07:44](../../log/2026-05-26.md#2026-05-26-0744-pdt--ctt-fsdpddp-doc-fix-high-1-from-morning-review) for the FSDP-claimed-but-not-configured doc-gap that triggered this note.
- Bypassing the ladder for "we'll need it eventually" reasons. Each rung's complexity is permanent debt; defer until forced.

# Quick decisions

- Does the model + Adam state fit on one rank? → DDP.
- Does it overflow DDP but fit when sharded across N ranks? → FSDP (one launcher flag).
- Is the activation memory or single-layer matmul still the bottleneck after FSDP? → Megatron.
