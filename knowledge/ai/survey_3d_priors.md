# Summary

What is the minimum prior a transformer needs to understand 3D point clouds (atomistic systems)? A spectrum of increasingly strong inductive biases:

1. Proper tokenization of floats (discretization, digit-by-digit, etc.)
2. Proper embedding of floats (Fourier features, learned bins)
3. Invariance — separating direction and distance, e.g. RBFs over pairwise distances
4. Equivariant representation — irreps, e3nn-style tensor products

The empirical question: how far up this spectrum must one go to match graph-based MLIPs at scale, and where does scaling compensate for missing priors?

# Trend Analysis

Two distinct moves, not one.

Level 4 → Level 3 (drop hard equivariance, keep GNN + RBF/physics features) is an established emerging trend. Multiple independent groups in 2024–2025 — EScAIP (Berkeley), Orb (Orbital Materials), PET-MAD (EPFL) — all report that non-equivariant GNNs match or beat equivariant baselines once trained on enough data, and they are being adopted in practice (Orb is a deployed production potential). AlphaFold 3 (DeepMind 2024) made the analogous move on the generative side. Solid emerging practice.

Level 3 → Level 1–2 (drop the graph entirely; raw tokens or coordinates into a plain transformer) is currently a single paper at MLIP scale (Kreiman et al. 2025, the paper above). Adjacent precedents exist — Eissler 2025 (off-the-shelf transformer for MD, still keeps a small attention bias), ADiT (Joshi 2025), AlphaFold 3 — but none drops graph + physics + equivariance simultaneously for energy/force prediction. And the headline result is qualified: a 1B-param transformer matches a 6M eSEN on energy and *loses on forces* at matched FLOPs. This is closer to "questionable single paper" than "emerging practice" — promising and influential because of the scaling argument, but unreplicated and not yet competitive on the metric practitioners care about most (forces).

Net: the field is genuinely shifting away from strict equivariance, but not yet away from graphs. Whether the all-the-way-to-tokens move becomes a trend depends on (a) someone reproducing it at a different lab, and (b) closing the force gap without re-introducing physics features.


# Read List

## 2025
### molecule_transformer_without_graph_2025
Title: Transformers Discover Molecular Structure Without Graph Priors[^molxformer]
1B-parameter plain transformer trained on OMol25. Pretrains autoregressively over text tokens and discretized vectors (coords, energy, forces); finetunes with bidirectional attention, no positional embeddings (for permutation invariance), and direct regression of energy/forces. Matches eSEN overall (better energy, worse force) with predictable scaling laws. Suggests level-1/2 priors (tokenization/embedding of floats) suffice when data and compute are large.
See [reading note](../../reading/2025/molecule_transformer_without_graph.md).
Outbound links: OMol25 (Levine 2025), eSEN (Fu 2025), UMA (Wood 2025), scaling laws (Frey 2023), MACE (Batatia 2022), NequIP (Batzner 2022), Orb (Neumann 2024), PET-MAD (Mazitov 2025), EScAIP (Qu & Krishnapriyan 2024), Equiformer-v2 (Liao 2024), ChemBERTa (Chithrananda 2020), Pure Transformer / TokenGT (Kim 2022), GraphGPS (Rampášek 2023), Uni-Mol (Zhou 2023), simple-MD transformer (Eissler 2025), AlphaFold 3 (Abramson 2024), All-atom Diffusion Transformer (Joshi 2025), Molecular Conformer Fields (Wang 2024).


# Closest Related Work (extracted from the paper)

Two clusters answer your question.

## Transformers on molecules with relaxed/no graph priors
- TokenGT — Kim et al. 2022, "Pure Transformers are Powerful Graph Learners"[^tokengt]. Encodes nodes+edges as a token sequence; vanilla transformer, but still uses graph tokens, not raw 3D coordinates.
- GraphGPS — Rampášek et al. 2023[^gps]. General graph-transformer recipe with positional/structural encodings.
- Uni-Mol — Zhou et al. 2023[^unimol]. 3D molecular transformer with attention biases derived from pair distances (physics-informed attention).
- Simple-MD Transformer — Eissler et al. 2025, "How simple can you go? An off-the-shelf transformer for MD"[^eissler]. Closest precursor: drops most physics, keeps a small bias term in attention.
- EScAIP — Qu & Krishnapriyan 2024[^escaip]. Drops hard equivariance but still GNN.
- Orb — Neumann et al. 2024[^orb]. Fast non-equivariant GNN MLIP.
- PET-MAD — Mazitov et al. 2025[^petmad]. Lightweight non-equivariant MLIP.
- ChemBERTa — Chithrananda et al. 2020[^chemberta]. Transformer on SMILES strings (text-only, no 3D).

## Transformers with continuous vectors / coordinates as I/O
- AlphaFold 3 — Abramson et al. 2024[^af3]. Diffusion transformer outputs 3D coordinates directly; relaxes the equivariance constraints of AF2.
- All-atom Diffusion Transformer (ADiT) — Joshi et al. 2025[^adit]. Unified generative transformer over molecules and materials in continuous 3D.
- Molecular Conformer Fields — Wang et al. 2024[^mcf]. Implicit-field transformer generating conformers.
- Probing equivariance & symmetry breaking — Vadgama et al. 2025[^vadgama]. Studies when non-equivariant networks recover equivariant behavior at scale.

The current paper is the first to push this all the way to a fully unmodified decoder transformer (no attention bias, no graph, no equivariance) on MLIPs at billion-parameter scale.


# eSEN vs MACE / NequIP / Allegro

eSEN[^esen] (Fu et al. 2025, "Learning Smooth and Expressive Interatomic Potentials") is the OMol25 reference baseline and is from the same FAIR/Berkeley line (it's also the small-model backbone inside UMA[^uma]). Differences:

- MACE/NequIP/Allegro: built on e3nn irreps and tensor products. Strict E(3)-equivariance baked into every layer. Heavy compute per edge; saturate around a few hundred million parameters in practice.
- eSEN: equivariant GNN designed for smoothness (continuous derivatives → stable MD) and expressivity. Comes in a direct-force variant (`-d`) and a conservative variant (`-c`, energy-gradient forces). At 6M parameters it is "state of the art" on OMol25 per the paper's framing, and chosen as the reference because it is small enough to compare at matched FLOPs while still beating older equivariant baselines.

Short answer: eSEN sits in the same family but is newer, smoother (better MD stability), and is the OMol25-era successor that the FAIR group benchmarks against — not a radically different paradigm from MACE/NequIP/Allegro.


# To Read List

- OMol25 dataset (Levine et al. 2025)[^omol25] — pretraining corpus
- eSEN (Fu et al. 2025)[^esen] — equivariant baseline
- UMA (Wood et al. 2025)[^uma] — MoE-scaled OMol25 reference model
- Eissler et al. 2025[^eissler] — closest "off-the-shelf transformer for MD" precursor
- AlphaFold 3 (Abramson et al. 2024)[^af3] — biggest precedent for transformer-with-coordinate-I/O
- ADiT (Joshi et al. 2025)[^adit] — unified molecule/material diffusion transformer
- TokenGT (Kim et al. 2022)[^tokengt] — pure transformer on graph tokens
- Uni-Mol (Zhou et al. 2023)[^unimol] — 3D-aware attention bias
- Scaling laws for atomistic models (Frey et al. 2023)
- Fourier features / digit-tokenization for continuous values (levels 1–2)
- Set Transformer / DeepSets — permutation-invariant attention without positional embeddings


[^molxformer]: <https://arxiv.org/abs/2510.02259>
[^esen]: Fu et al. 2025, "Learning smooth and expressive interatomic potentials for physical property prediction." <https://arxiv.org/abs/2502.12147>
[^omol25]: Levine et al. 2025, "The Open Molecules 2025 (OMol25) dataset, evaluations, and models."
[^uma]: Wood et al. 2025, "UMA: A family of universal models for atoms." <https://arxiv.org/abs/2506.23971>
[^tokengt]: Kim et al. 2022, "Pure Transformers are Powerful Graph Learners." <https://arxiv.org/abs/2207.02505>
[^gps]: Rampášek et al. 2023, "Recipe for a general, powerful, scalable graph transformer." <https://arxiv.org/abs/2205.12454>
[^unimol]: Zhou et al. 2023, "Uni-Mol: A universal 3D molecular representation learning framework." ICLR 2023.
[^eissler]: Eissler et al. 2025, "How simple can you go? An off-the-shelf transformer approach to molecular dynamics." <https://arxiv.org/abs/2503.01431>
[^escaip]: Qu & Krishnapriyan 2024, "EScAIP."
[^orb]: Neumann et al. 2024, "Orb: A fast, scalable neural network potential." <https://arxiv.org/abs/2410.22570>
[^petmad]: Mazitov et al. 2025, "PET-MAD, a lightweight universal interatomic potential." <https://arxiv.org/abs/2503.14118>
[^chemberta]: Chithrananda et al. 2020, "ChemBERTa: Large-scale self-supervised pretraining for molecular property prediction." <https://arxiv.org/abs/2010.09885>
[^af3]: Abramson et al. 2024, "AlphaFold 3."
[^adit]: Joshi et al. 2025, "All-atom diffusion transformers: Unified generative modelling of molecules and materials." <https://arxiv.org/abs/2503.03965>
[^mcf]: Wang et al. 2024, "Swallowing the bitter pill: Simplified scalable conformer generation." <https://arxiv.org/abs/2311.17932>
[^vadgama]: Vadgama et al. 2025, "Probing equivariance and symmetry breaking in convolutional networks." <https://arxiv.org/abs/2501.01999>
