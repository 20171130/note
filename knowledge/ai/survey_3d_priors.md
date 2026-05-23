# Summary

Scope: transformers that consume or produce 3D coordinates (atomistic systems, point clouds). Excludes SMILES/text models and 2D bond-graph transformers.

What is the minimum prior such a transformer needs? A spectrum of increasingly strong inductive biases:

1. Tokenization of floats (quantile bins, digit-by-digit)
2. Embedding of floats (Fourier features, learned bins)
3. Invariance — separating direction and distance, e.g. RBFs over pairwise distances, or attention biases conditioned on |r_ij|
4. Equivariant representation — irreps, e3nn-style tensor products (e.g. MACE, NequIP, Allegro, eSEN)

Empirical question: how far up this spectrum must one go to match equivariant baselines, and where does scaling compensate for missing priors?


# Trend Analysis

Strict equivariance is genuinely being abandoned. Within MLIP GNNs, multiple 2024–2025 papers (Orb, EScAIP, PET-MAD) drop hard E(3)-equivariance and recover competitive accuracy with more data. AlphaFold 3 (DeepMind 2024) made the analogous move on the generative side. This is solid emerging practice.

Going further — dropping the graph itself and feeding raw coordinates to a plain transformer — is currently one paper at MLIP scale (Kreiman et al. 2025, the paper below). Adjacent precedents are Eissler 2025 (keeps a small distance bias), Uni-Mol 2023 (pair-distance attention bias), AlphaFold 3 (coordinate diffusion). None drops graph + physics + equivariance simultaneously for energy/force prediction. And the headline is qualified: a 1B-param transformer matches a 6M-param eSEN on energy and *loses on forces* at matched FLOPs. Promising one-off, not yet a trend; needs reproduction at another lab and a closed force gap.


# Read List

## 2025
### molecule_transformer_without_graph_2025
Title: Transformers Discover Molecular Structure Without Graph Priors[^molxformer]
UC Berkeley + LBNL (Kreiman, Bai, Atieh, Weaver, Qu, Krishnapriyan). Not a FAIR paper, but built on FAIR's stack: pretrained on OMol25, benchmarked against eSEN and UMA-S.
1B-parameter plain decoder transformer. Pretrains autoregressively over text tokens and discretized vectors (coords, energy, forces via quantile binning); finetunes with bidirectional attention, no positional embeddings (permutation invariance), direct regression of energy/forces. Matches eSEN overall (better energy, worse force) with predictable scaling laws.
See [reading note](../../reading/2025/molecule_transformer_without_graph.md).
Outbound links: OMol25, eSEN, UMA, Eissler 2025, Uni-Mol, AlphaFold 3, ADiT, Molecular Conformer Fields.


# Closest Related Work — Transformers on 3D Coordinates

Ordered by how much physics/graph prior is kept.

- AlphaFold 3 — Abramson et al. 2024[^af3]. Pairformer + diffusion transformer; outputs 3D coordinates directly. Major precedent for dropping AF2's strict equivariance in a transformer.
- ADiT (All-atom Diffusion Transformer) — Joshi et al. 2025[^adit]. Unified generative DiT over molecules and materials in continuous 3D. FAIR Chem (Joshi, Fu, Liao, Gharakhanyan, Miller, Sriram, Ulissi).
- Molecular Conformer Fields — Wang et al. 2024[^mcf]. Apple. Implicit-field transformer for conformer generation.
- Uni-Mol — Zhou et al. 2023[^unimol]. 3D transformer with pair-distance attention bias (level 3 prior, no explicit graph but physics-informed attention).
- Simple-MD Transformer — Eissler et al. 2025[^eissler]. Closest direct precursor to molxformer: off-the-shelf transformer on 3D coordinates for MD, keeps a small attention bias.
- Probing equivariance & symmetry breaking — Vadgama et al. 2025[^vadgama]. Theoretical study of when non-equivariant networks recover equivariant behavior at scale.

molxformer is the first to push this to a fully unmodified decoder transformer (no graph, no attention bias, no equivariance, no physics features) on MLIPs at billion-parameter scale.

For context only (GNNs on 3D coordinates, dropped equivariance but kept graph): EScAIP[^escaip], Orb[^orb], PET-MAD[^petmad]. Cited as the "level 3" cohort showing equivariance is not strictly necessary, but not transformers.


# eSEN vs MACE / NequIP / Allegro

eSEN[^esen] (Fu et al. 2025, "Learning Smooth and Expressive Interatomic Potentials") is the OMol25 reference baseline and the small-model backbone inside UMA[^uma]. Same family as MACE/NequIP/Allegro (equivariant GNN with e3nn irreps), but tuned for smoothness (continuous derivatives → stable MD) and expressivity. Comes in direct-force (`-d`) and conservative (`-c`, energy-gradient) variants. At 6M parameters it is state of the art on OMol25; chosen as molxformer's reference because it is small enough for FLOP-matched comparison while beating older equivariant baselines. Not a different paradigm — just the OMol25-era FAIR successor.


# To Read List

Henry's queue: eSEN[^esen], AlphaFold 3[^af3], omol25
Then, Molecular Conformer Fields, ADiT, Simple-MD Transformer, Probing equivariance & symmetry breaking.

Available for me:
- Eissler et al. 2025[^eissler] — closest off-the-shelf-transformer-for-MD precursor
- ADiT (Joshi et al. 2025)[^adit] — FAIR unified molecule/material diffusion transformer
- Uni-Mol (Zhou et al. 2023)[^unimol] — pair-distance attention bias
- Molecular Conformer Fields (Wang et al. 2024)[^mcf] — implicit-field conformer generator
- Vadgama et al. 2025[^vadgama] — non-equivariance vs scale, theoretical
- OMol25 (Levine et al. 2025)[^omol25] — pretraining corpus
- Fourier features / digit-tokenization for continuous values
- Set Transformer / DeepSets — permutation-invariant attention without positional embeddings


[^molxformer]: <https://arxiv.org/abs/2510.02259>
[^esen]: Fu et al. 2025, "Learning smooth and expressive interatomic potentials for physical property prediction." <https://arxiv.org/abs/2502.12147>
[^omol25]: Levine et al. 2025, "The Open Molecules 2025 (OMol25) dataset, evaluations, and models."
[^uma]: Wood et al. 2025, "UMA: A family of universal models for atoms." <https://arxiv.org/abs/2506.23971>
[^unimol]: Zhou et al. 2023, "Uni-Mol: A universal 3D molecular representation learning framework." ICLR 2023.
[^eissler]: Eissler et al. 2025, "How simple can you go? An off-the-shelf transformer approach to molecular dynamics." <https://arxiv.org/abs/2503.01431>
[^escaip]: Qu & Krishnapriyan 2024, "EScAIP."
[^orb]: Neumann et al. 2024, "Orb: A fast, scalable neural network potential." <https://arxiv.org/abs/2410.22570>
[^petmad]: Mazitov et al. 2025, "PET-MAD, a lightweight universal interatomic potential." <https://arxiv.org/abs/2503.14118>
[^af3]: Abramson et al. 2024, "AlphaFold 3."
[^adit]: Joshi et al. 2025, "All-atom diffusion transformers: Unified generative modelling of molecules and materials." <https://arxiv.org/abs/2503.03965>
[^mcf]: Wang et al. 2024, "Swallowing the bitter pill: Simplified scalable conformer generation." <https://arxiv.org/abs/2311.17932>
[^vadgama]: Vadgama et al. 2025, "Probing equivariance and symmetry breaking in convolutional networks." <https://arxiv.org/abs/2501.01999>
