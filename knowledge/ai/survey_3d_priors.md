# Summary

Scope: transformers that consume and produce 3D coordinates (atomistic systems, point clouds).

What is the minimum prior such a transformer needs? A spectrum of increasingly strong inductive biases:

1. Tokenization of floats (quantile bins, digit-by-digit)
2. Embedding of floats (Fourier features, learned bins)
3. Invariance — separating direction and distance, e.g. RBFs over pairwise distances, or attention biases conditioned on |r_ij|
4. Equivariant representation — irreps, e3nn-style tensor products (e.g. MACE, NequIP, Allegro, eSEN)


# On the representation and generation of real numbers and vectors

## Distribution heads
Two families.

Continuous heads (predict parameters of a continuous distribution):
1. Fixed-σ Gaussian = MSE. Baseline. No uncertainty, mean-collapses on multi-modal targets.
2. Heteroscedastic Gaussian (predict μ and σ). One extra linear head, same inference cost, free per-token uncertainty. Still unimodal.
3. Full-Σ Gaussian via Cholesky. Captures correlated anisotropic noise; cheap for 3D vectors.
4. Gaussian Mixture (MDN, K components). First real multi-modality; training fragile (see below).
5. Per-token diffusion or score-matching head. Most expressive, sampleable, no mode collapse. AF3, MAR. Extra denoiser network and K inference steps (distillable).

Discrete heads (shard the value space into a finite vocabulary, predict like text tokens):
6. Per-axis categorical over quantile bins. K bins per axis, D axes → D cross-entropies. Stable training, arbitrary marginal shape, tokenization-compatible with the LLM stack. molxformer, WaveNet, Chronos. Loses cross-axis structure unless each axis is conditioned on the previous.
7. Spatial-cell categorical. Shard 3D space into a single vocabulary (uniform cubes, octree nodes, or a learned VQ codebook), predict one token per cell. Captures 3D shape directly, supports coarse-to-fine generation. Uni-3DAR[^uni3dar] (Lu et al. 2025, DP Technology) is the principal recent example: octree tokenizer with up to 8x subtree compression, unified across molecules / proteins / polymers / crystals / macroscopic objects, autoregressive on the resulting 1D sequence, reports up to +256% over diffusion baselines and 21.8x faster inference.

I am interested in the octo-tree like decoding

## Why GMM is harder than it looks
- Mode collapse / dead components: one component takes all responsibility early, the rest get vanishing gradients and never recover. Effective K shrinks toward 1.
- σ → 0 singularity: a component can shrink variance around one datapoint to make likelihood unbounded. Needs a lower bound on σ or an explicit prior.
- logsumexp gradient flow: gradients are weighted by normalized component posteriors; once one component dominates by orders of magnitude, the others stop learning. Feeds back into the previous two problems.
- K is a fixed hyperparameter, picked before training.
- Init sensitivity (all μ_k near zero with equal π → permanent collapse); k-means init on a batch helps.
- All of the above amplify under varied neural-net conditioning contexts.

Mitigations exist (σ clipping, gradient clipping, π temperature schedules, MoE-style load-balancing aux loss) but are engineering overhead that should be deferred unless multi-modality is shown to matter.

# On the neccessity of Equivariance and Locality

Empirical question: how far up this spectrum must one go to match equivariant baselines, and where does scaling compensate for missing priors?

Strict equivariance is genuinely being abandoned. Within MLIP GNNs, multiple 2024–2025 papers (Orb, EScAIP, PET-MAD) drop hard E(3)-equivariance but keep a spatial graph (radial cutoff) and recover competitive accuracy with more data. This is solid emerging practice.

Going further — dropping the spatial graph itself and feeding raw coordinates to a transformer — is rarer but no longer a single paper. molxformer (Kreiman et al. 2025) and AlphaFold 3 (Abramson et al. 2024) both fit here: no E(3) equivariance, no radial cutoff, attention is global at the relevant scale.
In the middle sit Eissler 2025 (edge tokens with pair-distance + displacement embeddings, drops equivariance and conservation) and Uni-Mol 2023 (atom tokens with pair-distance attention bias) — no explicit graph but distance is still privileged in the architecture. The headline result is qualified: molxformer's 1B-param transformer matches a 6M-param eSEN on energy and *loses on forces* at matched FLOPs. Promising small cohort, not yet a settled trend; needs reproduction at another lab on the MLIP side and a closed force gap.

It seems that dropping equivariance is a trend, simplifies the neural network, better structural compatibility with LLMs, less assumption on data. But omol25 says careful treatment for smoothness and energy conservation is necessary for MD and downstream tasks. The solution may be skip MD integration altogether, use CoT as an alternative. Although symmetry is dominant for fundamental physics, it loses its lofty status as we move toward larger-scale, coarse-grained, approximate models.

Counter-evidence: Vadgama et al. 2025, under controlled head-to-head comparison, find equivariant models still beat unconstrained ones on QM9 / ShapeNet / CMU motion, and capacity scaling does not fully close the gap. Their benchmarks are small-data; the open question is whether the trend papers' regime (OMol25-scale, AlphaFold-scale) genuinely escapes this.

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
MD-ET: an Edge Transformer (edge tokens, triangular attention, O(N³)) with pair-distance + displacement embeddings, no built-in equivariance (learned via O(3) augmentation), no energy conservation (direct force). SOTA on several MD benchmarks after few-shot finetune from QCML pretraining, but runaway energy drift in long NVE MD on larger structures — concrete failure mode of dropping conservation.
See [reading note](../../reading/2025/eissler.md).
Outbound links: molxformer, Uni-Mol, eSEN, Orb, PET, QCML.

### vadgama_2025
Title: Probing equivariance and symmetry breaking in convolutional networks[^vadgama]
AMLab Amsterdam + New Theory AI (Vadgama et al.). The principal counter to the drop-equivariance narrative.
Unified group-conv architecture (Rapidash) used to compare equivariant vs unconstrained variants under matched conditions. Finds equivariance still wins when aligned with task geometry; capacity scaling helps both but does not close the gap; explicit pose-conditioned symmetry breaking on top of an equivariant backbone is the strongest recipe. Benchmarks are small-data (QM9, ShapeNet, CMU motion), so does not directly refute the trend at MLIP / AlphaFold scale.
See [reading note](../../reading/2025/vadgama.md).
Outbound links: molxformer, AF3, Rapidash, e3nn.

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
