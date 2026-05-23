# Summary

What is the minimum prior a transformer needs to understand 3D point clouds (atomistic systems)? A spectrum of increasingly strong inductive biases:

1. Proper tokenization of floats (discretization, digit-by-digit, etc.)
2. Proper embedding of floats (Fourier features, learned bins)
3. Invariance — separating direction and distance, e.g. RBFs over pairwise distances
4. Equivariant representation — irreps, e3nn-style tensor products

The empirical question: how far up this spectrum must one go to match graph-based MLIPs at scale, and where does scaling compensate for missing priors?


# Read List

## 2025
### molecule_transformer_without_graph_2025
Title: Transformers Discover Molecular Structure Without Graph Priors[^molxformer]
1B-parameter plain transformer trained on OMol25. Pretrains autoregressively over text tokens and discretized vectors (coords, energy, forces); finetunes with bidirectional attention, no positional embeddings (for permutation invariance), and direct regression of energy/forces. Matches eSEN overall (better energy, worse force) with predictable scaling laws. Suggests level-1/2 priors (tokenization/embedding of floats) suffice when data and compute are large.
See [reading note](../../reading/2025/molecule_transformer_without_graph.md).
Outbound links: OMol25, eSEN, discretized-coordinate tokenization, MLIP scaling laws.


# To Read List

- OMol25 dataset (Meta FAIR, 2025) — pretraining corpus
- eSEN — equivariant baseline compared against
- MACE, NequIP, Allegro — equivariant MLIP architectures (level 4)
- e3nn — irreps / tensor-product framework
- RBF / Bessel basis embeddings for interatomic distances (level 3)
- Fourier features and digit-tokenization for continuous values (levels 1–2)
- Set Transformer / DeepSets — permutation-invariant attention without positional embeddings
- Scaling laws for atomistic / scientific foundation models

[^molxformer]: <https://arxiv.org/pdf/2510.02259>
