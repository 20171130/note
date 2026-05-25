# TODO
Continuous Token Transformer

Think more carefully about architecture, training data, and evaluation tasks.

Brandon:
1. How to fight catastrophic forgetting? Perhaps make it closer to vanilla transformer so I can use LoRA?
Besides architecture, another problem is data, and it's a huge problem.

Also on evaluation, what task is optimal for demonstrating our motivation? The best task may be something with little data so few/zero shot generalization is preferred, or some tasks that involve inherent ambiguity in its specification so the flexibility of text is needed.

Naming note: "Continuous Tokens" is the headline phrase of Fluid (Fan et al. 2024, "Scaling Autoregressive Text-to-image Generative Models with Continuous Tokens"), and MAR / GIVT cluster around the same terminology. Frame this work as the discrete-octree-head variant within that family rather than as a new line — the differentiator is the inner-AR octree subdivision head, not the umbrella term.

# History
Originally I designed a transformer for MD trajectories.
Zack suggested it should be applicable to all atomic, or even macroscopic, point clouds.
Then I changed it to a generative equivariant transformer.
Brandon and Ray suggested we can drop equivariance entirely.
Then after reading uni3dar_2025, recommended to me by Aaron, I invented in-token autoregressive generation for sampling numerical values and vectors.
Then the idea was generalized to the Continuous Token Transformer.

# Motivation

A multimodal-native LLM, with chemistry as first-class citizen.

![Reason in atoms](../image/reason_in_atoms.png)

A model that can communicate with us, while thinking in a fundamentally non-linguistic way.

Not a replacement for UMA — a complementary multitask, in-context learner.

First class citizen: not as text, vision or tool calls, chemistry deserves its own proper representation. LLMs can summarize a paragraph, it should be able to create coarse grain model of a system. Reason in words, now it can reason in atoms as well. Mirroring the microscopic atomic world; analogous to ideas like "visual thinking", "spatial memory", "sixth sense".

# Architecture
Each token can be a text token, a real number, or a vector.

Following recent studies, equivariance is not necessary.
Identical to a vanilla transformer, except for the embedding and prediction head for real numbers and vectors.

Parameterization is compatible with the vanilla transformer — initialized from pretrained weights for free prior knowledge.

For decoding, reserve a special `<|vectortoken|>`; when it is sampled, draw the next token from a 3D Gaussian instead.

I would argue a likelihood-based distribution loss is better than regression loss, so both text and vector prediction are measured in bits of entropy.

I think the [octree](uni3dar_2025) is a good idea.
The problem is that it is good only for coordinate generation, not for predicting arbitrary vectors like force. They also assume that the order in which points appear in the data does not matter and can be reordered into a BFS tree, which itself imposes an assumption on the data. Both are things I would like to avoid.
The merit of BFS is efficient common-ancestor path compression — no need to repeat the ancestors when generating siblings. However, we make this observation: embedding and encoding do not have to match the decoding generative process, as long as tokenization is aligned. We can embed using the continuous value directly, not via tree tokens; during decoding, we repeatedly and autoregressively sample multiple octree subdivision steps from the final representation.
I am talking about an autoregressive head for sampling a float or double-precision vector from the output of the final layer. For a 3D vector, sample from 8 octants 64 times for double precision, 32 times for float. (For a scalar, replace octants with binary halves and the step counts roughly double.)
Autoregressive generation within a token.

### In-token AR head — example: `one inch is 2.54 cm`

![Continuous Token Transformer in-token AR head](../image/continuous_token_head.svg)

Outer sequence is the usual LLM token stream — text plus a special numeric token (e.g. `<scalar_token>`, `<vector_token>`). A numeric token branches off into a small inner AR head conditioned only on that token's final hidden state (no extra context attention), emitting bits coarse → fine: sign (1 bit), exponent (11 bits, MSB → LSB), mantissa (52 bits, MSB → LSB) — 64 inner steps for a double, 32 for a float.

For a 3D vector, replace `<scalar_token>` with `<vector_token>` and emit all three axes jointly per step, so each subtoken is one of `2^3 = 8` octant states (one bit per axis at the current depth). Same coarse-to-fine ordering, same K, preserves cross-axis correlation.

Compression: multiple bit-levels can be packed into one inner subtoken (e.g. `2^16 = 65536` sub-vocab states sampling 4 times for a double), trading inner-step count for a wider per-step vocab. Not performance-critical since the inner head is light-weight.

Source: [continuous_token_head.d2](../image/continuous_token_head.d2) — render with `d2 --layout elk continuous_token_head.d2 continuous_token_head.svg`.

## Minor design questions
Core idea is settled (continuous-token AR, octree inner head, drop equivariance, multimodal text-vector interleaving); the following details are still open and should be resolved (RQ-Transformer read will inform several):

1. Continuous-input embedding. xVal-style single token with value-scaled embedding, vs Fourier features at multiple frequencies, vs MLP encoder over the raw value. Trade compactness vs smoothness.
2. Inner head architecture. Per-step MLP (cheapest), mini-transformer over the K-step inner sequence (most expressive, like RQ's depth transformer), or shared head with explicit step-position embedding.
3. should we generate per bit or per byte? for vectors, generate 3 dimensions together for each level of precision, or one by one?


# [Related Work](/knowledge/ai/survey_3d_priors.md)

## OMol25 comparision against baseline, evaluating if text pretraining helps
The first thing todo is comparing with molxformer on omol25.
We have causal mask instead of permutation invariance, autoregressive instead of transformer encoder style finetuning, or, GPT style instead of BERT style.
Also we use different tokenization and decoding strategies.
Evaluate if the text pretraining helps: compare
1. random initialization
2. initialize from text pretraining, full parameter finetuning
3. intialize from text pretraining, LoRA

# Pretraining

The idea is simple. The key is scaling.

For pretraining, we need data in large quantity or we can generate via computation ab initio in silico.
We look for data that are usually excluded from LLM training: MLIP force fields, MD trajectories, XYZ/PDB structures …


Curate a mix covering different
- force model, integrator
- ensemble, thermodynamic state
- system composition and scale
- any metadata or text we find with it (e.g. data source, timestamp …)

Feed it with everything we have.

DFT energy + force (the natural pretraining substrate for MLIP-style tasks):
1. OMol25 — ~140M DFT calcs at ωB97M-V/def2-TZVPD, molecules only, FAIR Chem. Our manager's group, access easy. See [reading note](../reading/2025/omol25.md).
2. OMat24 — ~110M DFT calcs for materials with PBC, FAIR. Complements OMol25 on the periodic side.
3. OC20 / OC22 — catalysts and oxides, FAIR. ~130M + 10M structures.
4. ODAC23 — MOFs and direct-air-capture sorbents, FAIR.
5. QCML — ~30M molecules at PBE0, includes out-of-equilibrium / charge / spin variations (Eissler 2025 uses this). See [reading note](../reading/2025/eissler.md).
6. SPICE / SPICE2 — drug-like small molecules at ωB97M-D3BJ, Open Force Field.
7. MPTrj — Materials Project relaxation trajectories (~1.5M structures, used by eSEN). See [reading note](../reading/2025/esen.md).
8. ANI-1x / ANI-1ccx / ANI-2x — small organics with multi-level QM labels.
9. QM9 / QM7 — small organics; saturated by modern models but useful for sanity checks.
Brandon asked how the model handles PBC — it should not be a problem once we drop the explicit coordinate treatment that geometric deep learning relies on. The model can learn to read cell vectors and offset attention keys on its own, without us hand-engineering it.

MD trajectories (per-frame coords ± forces):
10. MD-17 / MD-22 — small-molecule MD; classic benchmarks.
11. ATLAS — protein conformational ensembles (AlphaFold-DB-style for dynamics).
12. MISATO — protein-ligand MD trajectories.
13. D.E. Shaw Anton trajectories — public subset, limited.

Structure-only (XYZ / PDB / CIF, no forces):
14. PDB — ~220k experimentally solved biomolecular structures.
15. AlphaFold DB — ~200M predicted protein structures.
16. Materials Project / AFLOW / OQMD / NOMAD — millions of materials structures with DFT-computed properties.
17. COD — open small-molecule crystals (Crystallography Open Database).
18. ZINC — drug-like molecules with 3D conformers; useful for ligand-side pretraining.
19. GEOM / GEOM-DRUG — multi-conformer molecular ensembles.

Text-paired chemistry (for the multimodal-LLM half):
20. PubChem — ~100M compounds with names, descriptions, properties; the main "chemistry name → structure" corpus.
21. ChEMBL — bioactivity annotations against targets; structure + measurement text.
22. USPTO reactions — patent-extracted reaction SMILES with surrounding text; standard reaction-prediction corpus.
23. PubMed / arxiv chem — abstracts and DOIs; biggest free-form chemistry text.
Besides the pdf, we also want the files from supplementary material that contains all the numbers.

Text-only (to retain LLM capabilities, mix in during pretraining):
24. Whatever the base LLM was trained on (RedPajama, FineWeb, Dolma — match your initialization checkpoint's distribution).
25. arxiv full-text physics / chemistry / cs sections — heavy on equations and structured numeric content, good fit for the head.


Likely starting recipe: OMol25 (molecules) + OMat24 (materials with PBC) for the DFT-labeled half, PDB + AlphaFold DB for structure-only context, PubChem + USPTO for text-paired chemistry, plus the base LLM's original text mix to avoid catastrophic forgetting. Worth scoping volumes and tokenization budgets before committing.

# Downstream Tasks
Finetuning and RL dataset should be constructted based on these tasks.

## Tasks unique to a science-aware LLM
Grouped by why current methods can't do them. Pruned to items with a ready public dataset and an unambiguous metric. Items lacking eval data are dropped even if conceptually unique; pretraining-data gaps are noted separately and can be filled by synthetic construction.

### Long horizon / coarse-grained dynamics (regression collapses past the Lyapunov timescale)
- Long-horizon MD trajectory prediction. Datasets: MD17, MD22 (small molecules), MISATO (protein-ligand). Eval: NVE energy-conservation error and downstream property MAE over T ps (eSEN's TM23 / MD22 protocol). A distribution head replaces uninformative coordinate MSE.
- Reaction product prediction with text-described conditions. Dataset: USPTO-MIT. Eval: top-k accuracy.
- Retrosynthesis. Datasets: USPTO-50k, PaRoutes. Eval: top-k accuracy, multi-step route success.

### Text → structure specification (specialist generators only ingest structure-encoded conditions)
- Inverse design with text-described property constraints ("generate a molecule with LogP < 2, BBB-permeable, low hERG risk"). Datasets: PMO (Brown et al. 2022), Guacamol. Eval: success rate against thresholds, novelty, diversity.
- Property prediction and classification from mixed text + structure prompts. Datasets: MoleculeNet, TDC. Eval: RMSE / ROC-AUC on standard splits.

### Structure → text generation (specialists cannot emit text)
- Molecule captioning. Dataset: ChEBI-20 (Edwards et al. 2022). Eval: BLEU, ROUGE, exact match against curated descriptions.
- Protein function prediction (GO term assignment from sequence + structure). Dataset: CAFA. Eval: weighted F1 over GO terms — fully unambiguous classification rather than free-form text.

### In-context learning (eval constructed but unambiguous)
- Few-shot property prediction. Construct from TDC few-shot splits: prompt with K (structure, value) examples, predict for a held-out query. Eval: RMSE / accuracy — same metric as the parity benchmarks, just under a few-shot protocol.
- Multiple-choice chemistry knowledge. Dataset: ChemBench multiple-choice subset. Eval: accuracy — automatic, no LLM judge.
- Find UMA-failure cases

## Tasks existing methods already handle (for parity / generality demos)
Specialist baselines exist; matching them with one unified model is the generality argument, not a SOTA claim.

- MLIP energy + force regression on OMol25, OMat24, MPTrj. Target: match eSEN / UMA-S force RMSE at comparable FLOPs — direct comparison to molxformer's headline result.
- Unconditional 3D molecule generation on QM9 and GEOM-DRUG. Baselines: EDM, GeoLDM, Uni-3DAR. Metrics: atom/molecule stability, validity, uniqueness.
- Crystal structure prediction on MP-20, Carbon-24, MPTS-52 (de novo, CSP, and PXRD-conditioned). Baselines: DiffCSP, FlowMM, Uni-3DAR. Metrics: match rate, RMSE.
- Molecular conformer generation on GEOM-DRUG (multi-conformer ensembles). Baselines: torsional diffusion, Uni-3DAR. Metrics: COV-R / COV-P / MAT-R / MAT-P.
- Molecular property prediction (MoleculeNet: ESOL, FreeSolv, Lipophilicity, BBBP, BACE, Tox21). Baselines: Uni-Mol, Chemprop, GEM, SpaceFormer.
- Pocket-based ligand generation on CrossDocked2020. Baselines: Pocket2Mol, TargetDiff, Uni-3DAR. Metrics: Vina score, QED, SA.
- Molecular docking on PDBbind2020 / PoseBusters. Baselines: AutoDock Vina, SurfDock, AF3 (for the protein-ligand interface). Metrics: Top-1/5 RMSD success rates.
- Protein binding-pocket prediction on PDBBind / MOAD. Baselines: Vabs-Net. Metric: IoU.
- Full protein structure prediction (CASP / CAMEO) against AF3. Likely too compute-hungry and data-hungry for Phase 1.
## Reinforcement Learning
Supervised learning: learn from data. RL: fill the missing part necessary for explaining but missing from data (only question and answer in dataset), where no supervision signal is available.

Molecular dynamics is Chain-of-Thought in essence, but it is usually verbose and most of the intermediate steps are trivial. Predicting an MD trajectory or a relaxation path while skipping these trivial steps — rather than running explicit numerical integration — is a natural starting point for RL.

This allows the model do something very different from UMA. Add atoms and timesteps for periodic boundary conditions, temporal interpolation, spatial extension, explicit solvent…

Notice that the model does not generate the structure by calling some tool. The ability to understand and generate structure is built in since pretraining, allowing it to be used flexibly per instructions. The lipoprotein particle is ambiguous; specifying it accurately is challenging and not necessary.

Notice that the prompt must contain coordinates that specify a frame of reference, otherwise we cannot generate a non-zero vector from invariant text.
RL for longer-timescale, coarse-grained problems.

Pure text problems, with vectors as latent only.

Interpretability of chain of thought reasoning.
