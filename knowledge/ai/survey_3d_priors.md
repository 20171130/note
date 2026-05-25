# Summary

Scope: transformers that consume and produce 3D coordinates (atomistic systems, point clouds).

What is the minimum prior such a transformer needs? A spectrum of increasingly strong inductive biases:

1. Tokenization of floats (quantile bins, digit-by-digit)
2. Embedding of floats (Fourier features, learned bins)
3. Invariance — separating direction and distance, e.g. RBFs over pairwise distances, or attention biases conditioned on |r_ij|
4. Equivariant representation — irreps, e3nn-style tensor products (e.g. MACE, NequIP, Allegro, eSEN)


# On the representation and generation of real numbers and vectors

Three families exist for emitting a real number from a transformer. Continuous heads commit to a distribution family: MSE (a fixed-variance Gaussian; Bishop 1994 showed mean-collapse on multi-modal targets), heteroscedastic Gaussian, MDN (fragile training), or modern per-token diffusion (MAR[^mar], AF3[^af3]) and Gaussian mixture (GIVT[^givt]) heads. They cost a separate denoiser or distribution-fitting machinery and a loss-weight against the cross-entropy on text. Naive subword/digit tokenization (Regression Transformer, LIFT[^lift]) embeds floats as text — sequence length blows up, bin adjacency is lost. One-token-per-quantile-bin (molxformer[^molxformer], Chronos[^chronos], WaveNet) keeps sequences compact and unifies the loss but ignores ordinality on the bin vocab; Token-Mol[^tokenmol] patches this with a Gaussian Cross-Entropy soft label centered on the true bin, and residual-codebook stacks (VQ-VAE[^vqvae], RQ-Transformer[^rqt], EnCodec[^encodec]) replace one bin with K codebook indices emitted by a per-slot inner AR head. For 3D coordinates the geometric variant is octree subdivision (Uni-3DAR[^uni3dar] at the outer sequence; VAR[^var] as next-scale prediction).

Each predecessor leans on data assumptions we want to drop. molxformer/Token-Mol fix a global bin grid (assumes targets have a known range and roughly uniform density across it). MDN and GIVT pick K modes a priori (assumes the distribution's shape). RQ-Transformer learns a codebook (assumes the training distribution covers the regions a learned codebook can find). Uni-3DAR assumes a canonical BFS ordering of points (assumes the input data is sparse, locally clustered, and order-invariant) and tokenizes only coordinates, not arbitrary continuous payloads. MAR's diffusion head needs a noise schedule tuned to the target's scale.

Our Continuous Token Transformer drops all of these: no sparsity, no locality, no fixed magnitude range, no codebook to learn, no distribution family, no permutation-invariance assumption. We assume only that each value is a double (and it's easy to support unbounded precision if ever necessary). Cross-entropy is the single loss across text, scalars, and vectors, with no coefficient to balance.

# On the Necessity of Equivariance and Locality

Empirical question: how far up this spectrum must one go to match equivariant baselines, and where does scaling compensate for missing priors?

Strict equivariance is genuinely being abandoned. Within MLIP GNNs, multiple 2024–2025 papers (Orb[^orb], EScAIP[^escaip], PET-MAD[^petmad]) drop hard E(3)-equivariance but keep a spatial graph (radial cutoff) and recover competitive accuracy with more data. This is solid emerging practice.

In the middle sit Uni-Mol 2023[^unimol] (atom tokens with pair-distance attention bias), Eissler 2025[^eissler] (edge tokens with pair-distance + displacement embeddings), and AlphaFold 3[^af3] (token-level pair representation with triangular updates). All three drop equivariance and any radial-cutoff graph; AF3 and Eissler also drop energy conservation. What they keep is a pair representation with triangular updates — 3-WL expressive in one layer, but O(N³) in cost. Distance is no longer baked into the graph, but it is still privileged in the architecture.

Going further, molxformer (Kreiman et al. 2025)[^molxformer] drops the pair representation as well and feeds raw coordinates straight into a node-token transformer. The theoretical price is lower than the GNN intuition suggests: for combinatorial graphs, edge message passing is strictly more expressive than node-only (regular graphs cannot be distinguished by 1-WL), but this argument does not transfer to point clouds with coordinates. Two atoms with different `xyz` are already different tokens, and deep attention can synthesize pair and triple features across layers, so a node-token transformer over coordinates is universal in the limit. What it lacks is symmetry, not expressiveness — the same physical structure under rotation maps to different representations (the input-to-representation map is multi-valued), but distinct physical structures always map to distinct representations (injective). The cost is paid in inductive bias and sample complexity, not in reachable function class. The headline result is qualified: molxformer's 1B-param transformer matches a 6M-param eSEN[^esen] on energy and *loses on forces* at matched FLOPs.

This is the underlying tradeoff: a pair representation with triangular updates buys 3-WL expressivity in one layer at O(N³) compute, so the model can stay tiny in params; plain node-token attention is O(N²) per layer but must recover the same expressive ground across depth and data, so it pays in parameters and tokens instead.

| Model       | Pair structure         | Compute per layer | Params       |
|-------------|------------------------|-------------------|--------------|
| MD-ET       | edge tokens + triangle | O(N³)             | ~5M (estimated from hyperparameters; not disclosed) |
| AlphaFold 3 | pair rep + triangle    | O(N³)             | ~100–300M (not disclosed; Boltz-1 ≈ 150M, Chai-1 ≈ 200M as open proxies, with most params likely in the Pairformer rather than the diffusion module) |
| molxformer  | node tokens, no pair   | O(N²)             | 1B |

Dropping equivariance simplifies the architecture, aligns better with LLM stacks, and assumes less about the data. OMol25[^omol25] is the standing caveat: careful treatment of smoothness and energy conservation remains necessary for MD and downstream tasks. One way out is to skip MD integration altogether and predict future directly instead (possibly with CoT). Symmetry is dominant for fundamental physics but loses its lofty status as we move toward larger-scale, coarse-grained, approximate models.

Counter-evidence with caveats: Vadgama et al. 2025[^vadgama], under controlled head-to-head comparison, find equivariant models still beat unconstrained ones on QM9 / ShapeNet / CMU motion, and capacity scaling does not close the gap. But all comparisons are within Rapidash, a regular group-conv architecture — no transformer baseline is tested — and the scaling ablation is a single pair of hidden-dim sizes (256 vs 512), under one order of magnitude. So the result is "more equivariance beats less equivariance, within group convs, at small data", not yet a refutation of the molxformer / AF3 bet of "drop equivariance, switch to large pretrained transformer, scale data". The open question — whether the gap closes once you change both architecture family and data regime — is not addressed.

# Read List

## 2025
### molecule_transformer_without_graph_2025
Title: Transformers Discover Molecular Structure Without Graph Priors[^molxformer]
UC Berkeley + LBNL (Kreiman, Bai, Atieh, Weaver, Qu, Krishnapriyan). Not a FAIR paper, but built on FAIR's stack: pretrained on OMol25, benchmarked against eSEN and UMA-S.
1B-parameter plain decoder transformer. Pretrains autoregressively over text tokens and discretized vectors (coords, energy, forces via quantile binning); finetunes with bidirectional attention, no positional embeddings (permutation invariance), direct regression of energy/forces. Matches eSEN overall (better energy, worse force) with predictable scaling laws.
See [reading note](../../reading/2025/molecule_transformer_without_graph.md).
Outbound links: OMol25, eSEN, UMA, Eissler 2025, Uni-Mol, AlphaFold 3, ADiT, Molecular Conformer Fields.

### omol25_2025
Title: The Open Molecules 2025 (OMol25) dataset, evaluations, and models[^omol25]
FAIR Chem (Levine et al.). Molecules-only DFT dataset (no PBC; FAIR's periodic datasets are OC20/OC22/OMat24) plus the baseline MLIP zoo (eSEN, GemNet-OC, MACE, UMA) used by molxformer.
That's why molxformer uses it, without the need to deal with PBC. I think CoT or input augmentation is needed for PBC.
See [reading note](../../reading/2025/omol25.md).
Outbound links: eSEN, UMA, GemNet-OC, MACE, molxformer.

### esen_2025
Title: Learning Smooth and Expressive Interatomic Potentials for Physical Property Prediction[^esen]
FAIR Chem (Fu, Wood, Barroso-Luque, Levine, Gao, Dzamba, Zitnick). OMol25 reference baseline and the small-model backbone inside UMA[^uma]; same equivariant-GNN-with-e3nn-irreps family as MACE / NequIP / Allegro, descended from eSCN / EquiformerV2.
Argues lower test error only correlates with downstream property prediction when the MLIP passes a practical energy-conservation diagnostic on OOD NVE MD.
Direct-force pretraining + conservative finetuning and MD simulation.
See [reading note](../../reading/2025/esen.md).
Outbound links: OMol25, UMA, MACE, NequIP, Allegro, eSCN, EquiformerV2, Matbench-Discovery.

### eissler_2025
Title: How simple can you go? An off-the-shelf transformer approach to molecular dynamics[^eissler]
TU Berlin / BIFOLD + Google DeepMind (Eissler, Korjakow, Ganscha, Unke, Müller, Gugler). Closest published precursor to molxformer.
MD-ET: an Edge Transformer over the fully connected atom graph, tokens are edges (N×N), 3-WL expressive via triangular attention that softmax-einsums pair features `il, lj -> ij` across the intermediate index `l`. No built-in equivariance (learned via O(3) augmentation), no energy conservation (direct force), no cutoff. SOTA on several MD benchmarks after few-shot finetune from QCML pretraining, but runaway energy drift in long NVE MD on larger structures — concrete failure mode of dropping conservation.
See [reading note](../../reading/2025/eissler.md).
Outbound links: molxformer, Uni-Mol, eSEN, Orb, PET, QCML.

### vadgama_2025
Title: Probing equivariance and symmetry breaking in convolutional networks[^vadgama]
AMLab Amsterdam + New Theory AI (Vadgama et al.). The cleanest published counter to the drop-equivariance narrative, with limits.
Unified group-conv architecture (Rapidash) used to compare SE(3) vs SO(3) vs T(3)-only variants under matched conditions. Finds equivariance still wins when aligned with task geometry; capacity scaling helps both but does not close the gap; explicit pose-conditioned symmetry breaking on top of an equivariant backbone is the strongest recipe. Limits: all comparisons stay inside Rapidash (no transformer baseline, no pretrained-init transfer), the scaling ablation is a single pair of hidden-dim sizes (under one order of magnitude), and benchmarks are small-data (QM9, ShapeNet, CMU motion). Does not directly address the molxformer / AF3 bet of "large pretrained transformer + scale".
See [reading note](../../reading/2025/vadgama.md).
Outbound links: molxformer, AF3, Rapidash, e3nn.

### uni3dar_2025
Title: Uni-3DAR: Unified Cross-Scale 3D Generation and Understanding via Autoregressive Modeling[^uni3dar]
DP Technology (Lu, Lin, Yao, Gao et al.). Discrete spatial tokenization via octree BFS (256-state nodes via 8-child occupancy mask), with 2-level subtree compression and masked next-token prediction. Beats diffusion baselines on molecule generation, crystal structure prediction (+256% relative on PXRD-CSP), pocket prediction, docking, and ShapeNet, with ~21.8x faster inference. Widest scale-range existence proof for discrete-AR + 3D in the survey.

See [reading note](../../reading/2025/uni3dar.md).
Outbound links: octree, VQ-VAE, molxformer, DiffCSP, EDM, LION, multi-frame conditioning.

# 2024

### alphafold3_2024
Title: Accurate structure prediction of biomolecular interactions with AlphaFold 3[^af3]
Google DeepMind + Isomorphic Labs (Abramson et al.). Nature 630, 493.
Drops architectural equivariance, per-residue frames + IPA, torsion parametrizations, stereochemical violation losses, and any radial cutoff at the token level (token attention is global).
Keeps: polymer / ligand connectivity (atom-level uses sequence-local attention along the chain, not 3D radial), Pairformer triangle updates on the pair representation, biology priors (MSA + templates, de-emphasized). No energy / force / conservation — structure prediction only.
See [reading note](../../reading/2024/alphafold3.md).
Outbound links: AF2, IPA, Evoformer, Pairformer, molxformer, ADiT.


# Closest Related Work — Transformers on 3D Coordinates

Ordered by how much physics/graph prior is kept.

- ADiT (All-atom Diffusion Transformer) — Joshi et al. 2025[^adit]. Unified generative DiT over molecules and materials in continuous 3D. FAIR Chem (Joshi, Fu, Liao, Gharakhanyan, Miller, Sriram, Ulissi).
- Molecular Conformer Fields — Wang et al. 2024[^mcf]. Apple. Implicit-field transformer for conformer generation.
- Uni-Mol — Zhou et al. 2023[^unimol]. 3D transformer with pair-distance attention bias (level 3 prior, no explicit graph but physics-informed attention).

molxformer is the first to push this to a fully unmodified decoder transformer (no graph, no attention bias, no equivariance, no physics features) on MLIPs at billion-parameter scale.

For context only (GNNs on 3D coordinates, dropped equivariance but kept graph): EScAIP[^escaip], Orb[^orb], PET-MAD[^petmad]. Cited as the "level 3" cohort showing equivariance is not strictly necessary, but not transformers.


# To Read List

Then, Molecular Conformer Fields, ADiT, Simple-MD Transformer, Probing equivariance & symmetry breaking.

Available for me:
- ADiT (Joshi et al. 2025)[^adit] — FAIR unified molecule/material diffusion transformer
- Uni-Mol (Zhou et al. 2023)[^unimol] — pair-distance attention bias
- Molecular Conformer Fields (Wang et al. 2024)[^mcf] — implicit-field conformer generator

## Tokenize / embed / predict continuous values
Sub-thread on level-1/2 priors (float tokenization, embedding, distribution heads). Most directly relevant to the multimodal-LLM design.

Continuous scalar embedding:
- xVal (Golkar et al. 2023, Polymathic)[^xval] — single reserved token; embedding scaled by the number's value; regression head. Strong candidate over quantile binning.
- Fourier features (Tancik et al. 2020)[^fourier] — canonical sinusoidal-at-multiple-frequencies prescription for learning high-frequency functions of scalars/coords.
- NeRF positional encoding (Mildenhall et al. 2020)[^nerf] — Fourier features applied to 3D coordinates; precedent for raw-coordinate input.
- DiT timestep embedding (Peebles & Xie 2023)[^dit] — sinusoidal + MLP, minimal-overhead conditioning on a continuous scalar.

Quantile binning at scale (validates molxformer's choice):
- Chronos (Ansari et al. 2024, Amazon)[^chronos] — time-series foundation model via scaling + quantile binning to a fixed vocabulary; ~80M–700M scaling laws.
- PatchTST (Nie et al. 2023)[^patchtst] — alternative: patch-of-values embedding instead of tokenizing individual values.

Continuous autoregression with a distribution head (matches the multimodal-LLM "likelihood loss on vectors" idea):
- MAR (Li et al. 2024)[^mar] — "Autoregressive Image Generation without Vector Quantization"; per-token diffusion head over continuous embeddings; outperforms VQ-AR at matched compute.
- Fluid (Fan et al. 2024, Google)[^fluid] — text-to-image continuous AR with a similar diffusion head; scales cleanly.
- GIVT (Tschannen et al. 2024, Google)[^givt] — Generative Infinite-Vocabulary Transformers; predicts a Gaussian mixture over each next continuous token.

Numerical reasoning baselines (mostly for completeness):
- LIFT (Dinh et al. 2022)[^lift] — finetune LLM on regression by digit-encoding numbers as text.

Discrete spatial tokenization:
- Uni-3DAR (Lu et al. 2025, DP Technology)[^uni3dar] — octree coarse-to-fine tokenizer with up to 8x subtree compression; unified autoregressive model across molecules, proteins, polymers, crystals, and macroscopic 3D objects; claims up to +256% over diffusion baselines and 21.8x faster inference.
- VQ-VAE (van den Oord et al. 2017)[^vqvae] — learned discrete codebook over continuous embeddings; foundation for the VQ→AR-token pipeline used widely in image/audio.

Per-slot inner AR head (closest architectural family to the Continuous Token Transformer design):
- RQ-Transformer (Lee et al. 2022)[^rqt] — residual VQ with a small "depth transformer" per outer slot that autoregressively emits a stack of codebook indices. Direct precedent for in-token AR over discrete codes.
- SoundStream / EnCodec (Zeghidour et al. 2021 / Défossez et al. 2022)[^encodec] — residual-VQ neural audio codec; same depth-stack tokenization that downstream audio LMs (AudioLM, MusicGen) decode via per-slot AR heads.
- VAR (Tian et al. 2024)[^var] — "next-scale" prediction; coarse-to-fine generation over outer-sequence positions rather than an inner head, but the same coarse-to-fine philosophy applies.


[^molxformer]: <https://arxiv.org/abs/2510.02259>
[^esen]: Fu et al. 2025, "Learning smooth and expressive interatomic potentials for physical property prediction." <https://arxiv.org/abs/2502.12147>
[^omol25]: Levine et al. 2025, "The Open Molecules 2025 (OMol25) dataset, evaluations, and models."
[^uma]: Wood et al. 2025, "UMA: A family of universal models for atoms." <https://arxiv.org/abs/2506.23971>
[^unimol]: Zhou et al. 2023, "Uni-Mol: A universal 3D molecular representation learning framework." ICLR 2023.
[^eissler]: Eissler et al. 2025, "How simple can you go? An off-the-shelf transformer approach to molecular dynamics." <https://arxiv.org/abs/2503.01431>
[^escaip]: Qu & Krishnapriyan 2024, "EScAIP."
[^orb]: Neumann et al. 2024, "Orb: A fast, scalable neural network potential." <https://arxiv.org/abs/2410.22570>
[^petmad]: Mazitov et al. 2025, "PET-MAD, a lightweight universal interatomic potential." <https://arxiv.org/abs/2503.14118>
[^af3]: Abramson et al. 2024, "Accurate structure prediction of biomolecular interactions with AlphaFold 3." Nature 630, 493. <https://www.nature.com/articles/s41586-024-07487-w>
[^adit]: Joshi et al. 2025, "All-atom diffusion transformers: Unified generative modelling of molecules and materials." <https://arxiv.org/abs/2503.03965>
[^mcf]: Wang et al. 2024, "Swallowing the bitter pill: Simplified scalable conformer generation." <https://arxiv.org/abs/2311.17932>
[^vadgama]: Vadgama et al. 2025, "Probing equivariance and symmetry breaking in convolutional networks." <https://arxiv.org/abs/2501.01999>
[^xval]: Golkar et al. 2023, "xVal: A Continuous Number Encoding for Large Language Models." <https://arxiv.org/abs/2310.02989>
[^fourier]: Tancik et al. 2020, "Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains." NeurIPS. <https://arxiv.org/abs/2006.10739>
[^nerf]: Mildenhall et al. 2020, "NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis." <https://arxiv.org/abs/2003.08934>
[^dit]: Peebles & Xie 2023, "Scalable Diffusion Models with Transformers." <https://arxiv.org/abs/2212.09748>
[^chronos]: Ansari et al. 2024, "Chronos: Learning the Language of Time Series." <https://arxiv.org/abs/2403.07815>
[^patchtst]: Nie et al. 2023, "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers." ICLR. <https://arxiv.org/abs/2211.14730>
[^mar]: Li et al. 2024, "Autoregressive Image Generation without Vector Quantization." NeurIPS. <https://arxiv.org/abs/2406.11838>
[^fluid]: Fan et al. 2024, "Fluid: Scaling Autoregressive Text-to-image Generative Models with Continuous Tokens." <https://arxiv.org/abs/2410.13863>
[^givt]: Tschannen et al. 2024, "GIVT: Generative Infinite-Vocabulary Transformers." ECCV. <https://arxiv.org/abs/2312.02116>
[^lift]: Dinh et al. 2022, "LIFT: Language-Interfaced Fine-Tuning for Non-Language Machine Learning Tasks." NeurIPS. <https://arxiv.org/abs/2206.06565>
[^vqvae]: van den Oord et al. 2017, "Neural Discrete Representation Learning." NeurIPS. <https://arxiv.org/abs/1711.00937>
[^uni3dar]: Lu et al. 2025, "Uni-3DAR: Unified 3D Generation and Understanding via Autoregressive Modeling on Compressed Spatial Tokens." DP Technology. <https://arxiv.org/abs/2503.16278>
[^rqt]: Lee et al. 2022, "Autoregressive Image Generation using Residual Quantization." CVPR. <https://arxiv.org/abs/2203.01941>
[^encodec]: Défossez et al. 2022, "High Fidelity Neural Audio Compression" (EnCodec); Zeghidour et al. 2021, "SoundStream: An End-to-End Neural Audio Codec." <https://arxiv.org/abs/2210.13438>
[^var]: Tian et al. 2024, "Visual Autoregressive Modeling: Scalable Image Generation via Next-Scale Prediction." NeurIPS best paper. <https://arxiv.org/abs/2404.02905>
[^tokenmol]: Wang et al. 2024, "Token-Mol 1.0: tokenized drug design with large language models." <https://arxiv.org/abs/2407.07930>
