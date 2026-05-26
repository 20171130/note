# TODO and Progress
1. ✅ test how to manage python env and submit gpu jobs on [fair sc3](/knowledge/fair-sc.md)
2. ~~Download OMol25 data~~ — already on cluster, see [below](#omol25-on-disk). Still TODO: deeper statistics on raw shards.
3. ✅ Eval a baseline method for sanity check on OMol25 — done, see [below](#baseline-sanity-eval--passed-2026-05-24-2235-pdt). Within 11-16% of paper on energy/force.

This file is archived. Future docs live in the [Continuous Token Transformer repo](/CTT/README.md). OMol25-specific content (on-disk split table, baseline sanity eval, comparison plan) moved to [`CTT/omol25_eval/data_and_baseline.md`](/CTT/omol25_eval/data_and_baseline.md) on 2026-05-26.

# History
Originally I designed a transformer for MD trajectories.
Zack suggested it should be applicable to all atomic, or even macroscopic, point clouds.
Then I changed it to a generative equivariant transformer.
Brandon and Ray suggested we can drop equivariance entirely.
Then after reading uni3dar_2025, recommended to me by Aaron, I invented in-token autoregressive generation for sampling numerical values and vectors.
Then the idea was generalized to the Continuous Token Transformer.

Naming note: moved to [CTT/README.md#naming](../../CTT/README.md#naming).

# Motivation
Moved to [CTT/README.md#motivation](../../CTT/README.md#motivation).

# Architecture
Moved to [CTT/README.md#architecture](../../CTT/README.md#architecture). Open design questions tracked in [CTT/README.md#open-design-questions](../../CTT/README.md#open-design-questions).


# [Related Work](/knowledge/ai/survey_3d_priors.md)

(OMol25-specific comparison plan moved to [`CTT/omol25_eval/data_and_baseline.md`](/CTT/omol25_eval/data_and_baseline.md#omol25-comparison-against-baseline-evaluating-if-text-pretraining-helps).)

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
