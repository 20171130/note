# UMA: A Family of Universal Models for Atoms

**NeurIPS 2025** — Wood, Dzamba, Fu, Gao, Shuaibi et al. (FAIR at Meta, CMU)

## Summary

UMA is a family of universal machine learning interatomic potentials (MLIPs) trained on ~500M atomic structures spanning molecules, materials, and catalysts — the largest training run of this kind to date. The goal is a single model that matches or surpasses specialized models without fine-tuning. This is closely analogous to work done at DPTech on universal atom potential models.

## Architecture

- **Base:** eSEN — an equivariant graph neural network using spherical harmonics
- **Message passing:** updates node embeddings through edge-wise convolution (eSCN) + node-wise feed-forward blocks, both with residual connections; neighbors within 6 Å
- **Inputs:** atom positions, atomic numbers, total charge, spin multiplicity, DFT task embedding
- **Outputs:** total energy, per-atom forces, stress

## Key Innovation: Mixture of Linear Experts (MoLE)

MoLE replaces the standard linear layers with a dense weighted combination of linear experts:

```
y = Σ_k α_k (W_k x)
```

Unlike classic sparse MoE (top-k, non-linear experts competing for attention), MoLE uses all experts simultaneously with continuous weights. This preserves energy surface smoothness and rotational equivariance — critical properties for MLIPs that standard sparse MoE would violate.

The expert routing weights α are computed from a global embedding that depends only on system-level information (charge, spin, DFT task) — factors that remain constant during molecular dynamics. This allows the weighted combination to be precomputed and merged into a single effective weight matrix before the simulation begins, enabling fast sequential inference.

**Open questions:**
1. **Long-range interactions:** UMA uses a 6 Å cutoff, which captures short-range quantum effects but not long-range electrostatics. There is prior work explicitly separating the two regimes — short-range via a local network and long-range via predicted multipoles. It is worth asking whether UMA handles this at all, or whether it is a known gap.
2. **Continuity argument for constant α:** The paper justifies global constant routing weights (constant during MD) as necessary to prevent discontinuities in the energy surface. But this is not actually required — if α is a continuous and differentiable function of the inputs, then energy will also be continuous and differentiable, even if α changes during simulation. This is distinct from classic sparse MoE, which encourages sparsity and can introduce discontinuities. The real reason for the constant-weights design is likely to enable precomputing the merged weight matrix before the simulation begins. Whether that offers substantial computational benefit is unclear.
3. **Global vs. element-dependent routing:** Even granting the MD-constant-weights constraint, routing could still be element-dependent rather than global. In LLMs, MoE routing is per-token, not per-prompt — the analogy here would be per-element or per-atom routing. The global routing choice may be a simplification rather than a fundamental requirement.
4. **MoLE applied to convolutions:** It appears MoLE is applied to the eSCN convolution layers (edge-wise blocks) rather than the feed-forward layers, which is unconventional. Worth confirming whether this is the case and what motivated it.

## Models

| Model | Total Params | Active Params | Speed (1k atoms, H100) |
|-------|-------------|--------------|----------------------|
| UMA-S | 150M | 6M | 16 inferences/sec |
| UMA-M | 1.4B | 50M | 3 inferences/sec |
| UMA-L | 700M | 700M | 1.6 inferences/sec |

UMA-M is the general-purpose model; UMA-S is optimized for long MD simulations; UMA-L is a scaling proof-of-principle.
