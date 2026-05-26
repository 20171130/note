# TODO and Progress
1. ✅ test how to manage python env and submit gpu jobs on [fair sc3](/knowledge/fair-sc.md)
2. ~~Download OMol25 data~~ — already on cluster, see [below](#omol25-on-disk). Still TODO: deeper statistics on raw shards.
3. ✅ Eval a baseline method for sanity check on OMol25 — done, see [below](#baseline-sanity-eval--passed-2026-05-24-2235-pdt). Within 11-16% of paper on energy/force.

This file is archived. Future docs live in the [Continuous Token Transformer repo](/CTT/README.md).

## OMol25 on disk

Path: `/checkpoint/ocp/shared/omol/250430-release/` (mirror `/checkpoint/ocp-h100-2/shared/omol/250409-final/`, older).

Splits group into three families. Structure counts marked "est." are `entries_in_shard0 × n_shards`, an upper bound since the last shard may be partial; cited counts come from the paper.

| family | split | shards | size | structures | sources (sampled[^direct_probe]) | charge | spin | role |
|---|---|---|---|---|---|---|---|---|
| train | `train` | 200 | 509 GB | est. 105 M[^count_discrepancy] | elytes, biomolecules, geom, orbnet, … | -1..+3 | 1..4 | full training ("All")[^omol25_table1] |
| train | `train_4M` | 80 | 22 GB | 4.0 M | all 10 OMol25 sources | -2..+3 | 1..6 | uniform subsample for cheap dev[^omol25_table1] |
| train | `simple_train` | 80 | 109 GB | est. 34.3 M | ani2x, geom, trans1x, spice, orbnet, rgd | 0 only | 1 only | "Neutral" subset[^omol25_neutral] |
| train | `simple_val` | 80 | 135 MB | est. 28 k | orbnet, geom, ani2x, spice | 0 only | 1 only | validation for `simple_train` |
| comp-OOD | `val` | 80 | 23 GB | 2.76 M | elytes, biomolecules | -3..+3 | 1 | OOD-by-composition val ("Val Comp")[^omol25_table1] |
| comp-OOD | `test` | 80 | 25 GB | 2.81 M | biomolecules, elytes | -3..+3 | 1..2 | OOD-by-composition test ("Test Comp")[^omol25_table1] |
| chem-OOD | `elytes_ood` | 80 | 553 MB | est. 124 k | elytes only | -2..+1 | 1 | electrolyte clusters with OOD anions/cations/solvents[^omol25_elyte] |
| chem-OOD | `metal_ligand_ood` | 80 | 358 MB | 42 k[^omol25_table1] | metal_complexes only | -2..+3 | 1..8 | 50 held-out metal–ligand bond combos ("M-Lig") |
| chem-OOD | `uhs_ood` | 80 | 161 MB | est. 25 k | elytes, metal_complexes | -8..+6 | 12..21 | ultra high-spin OOD (charge & spin extremes)[^uhs_probe] |

[^direct_probe]: Per-frame metadata read directly from shard 0 of each split (`data.data_id`, `data.charge`, `data.spin`, 50-record sample). Records are zlib-compressed JSON inside ASE-LMDB.
[^count_discrepancy]: Paper Table 1 reports 140,641,161 for "All"; our 200 × 525,507 estimate gives ~105 M. Either the per-shard count varies, or the on-disk release is a different cut. Not yet investigated.
[^omol25_table1]: Levine et al. 2025 Table 1, [`reading/2025/omol25.md`](../reading/2025/omol25.md). Counts: All 140,641,161; 4M 3,986,754; Val Comp 2,762,021; Test Comp 2,805,046; M-Lig val 39,615 / test 42,028.
[^omol25_neutral]: Paper §2.9: "Neutral" split = 34,335,828 charge-neutral singlet snapshots from ANI-2X, OrbNet Denali, SPICE2, GEOM, Transition-1X, RGD1. Per-shard probe matches both the count (~34.3 M) and source composition.
[^omol25_elyte]: Paper §K.4 / Table 14: OOD electrolyte clusters built from held-out anions (e.g. DFOB, HMDS), cations (e.g. TMA, tetraethylphosphonium), and/or solvents.
[^uhs_probe]: Probed shard 0 records show spin multiplicities of 12, 13, 14, 15, 16, 17, 19, 21 — i.e. extremely open-shell — and absolute charges up to 8. Confirms "ultra high spin" interpretation. Not defined in arXiv:2505.08762 v1 or fairchem `main` configs; canonical name binding only in the gated HF DATASET.md.

Precomputed stats in `stats/` (built on a 10.65M-frame subsample, ~538M atoms; OMol25 paper reports ~140M total structures, so this is roughly a 1:13 sample[^stats_sample]):

- `stats.pkl`: `energy_mean=1.94 eV`, `energy_std=9.67 eV`, `force_rms=1.43 eV/Å`, `force_md=1.17 eV/Å` (force mean magnitude), `avg_num_atoms=50.5`.
- `energy_histogram.npz` — 100 bins over `[-87.3, 254.5] eV` (after lin-ref subtraction). Per-frame percentiles: p1 −17, p50 −0.15, p99 +34, p99.9 +78, all in eV. Heavy right tail.
- `force_norm_histogram.npz` — 100 bins over `[5e-8, 50] eV/Å`. Per-atom percentiles: p50 0.75, p95 3.75, p99 10.25, p99.9 26.75, all in eV/Å. Forces span ~9 orders of magnitude; needs log-scale handling for the in-token AR head.
- `lin_ref_coeffs_hof.npz` — per-element heat-of-formation reference, 100 atomic numbers, range `[-3.19, 18.36] eV/atom`.
- `joint_hof_lin_coeffs.npz` — full energy reference, range `[-74932, 0] eV/atom` (raw DFT total energies before subtraction).

[^stats_sample]: Inferred from `hist.sum()=10.65M` frames vs the 140M figure in [OMol25 paper](../reading/2025/omol25.md). The histogram file itself does not document its sampling protocol.


## Baseline sanity eval — PASSED 2026-05-24 22:35 PDT

Goal: load a released eSEN-sm-conserving checkpoint, run inference on `val/data0000.aselmdb`, reproduce the paper's MAE within sanity bounds. Confirms data path + units are right before any model dev.

Result on 500 structures from `val/data0000`:

| metric | ours | paper Test-Comp eSEN-sm-cons All[^paper_table3] | gap |
|---|---|---|---|
| energy MAE | 1.913 kcal/mol | 2.150 kcal/mol | -11% (better) |
| force MAE | 0.198 kcal/mol/Å | 0.170 kcal/mol/Å | +16% (worse) |
| wall | 30.7 s, 0.06 s/struct on 1 H100 | — | — |

Both within 20% on a single shard. Shard 0 is elytes+biomolecules-heavy and we ran on Val-Comp (not Test-Comp), so directional differences are expected sample bias. Data path verified, units correct.

Stack: `mlip-pytorch-2.8.0-cu126.sif` + `~/envs/mlip/` (fairchem-core 2.20.0) + HF gated access. Launch via `apptainer exec --nv` under `srun --qos=h100_dev --gres=gpu:1`.

Unit-convention note: paper Table 3 reports energy MAE in kcal/mol **per structure** (not per-atom; the table footer says just "kcal/mol", no "/atom"). Force MAE is per-atom (kcal/mol/Å). Easy to misread because the page-12 prose says "per-atom MAE is the primary metric" — that applies to forces only.

Local 4M checkpoints (`omol_checkpoints/202505-0117-5120-e475/inference_ckpt_final.pt`) remain unusable from public fairchem-core because they require `fairchem.experimental.foundation_models` (internal Meta package, has the `puma.escn_md` backbone, not on PyPI). To reproduce the 4M Table 3 row (3.250 / 0.230), need to either:
- get internal `fairchem.experimental` from Brandon Wood / Muhammed Shuaibi / Saro Passaro, or
- accept the All row (2.150 / 0.170) we've already reproduced — All is the stronger model and a fair sanity target.

Scripts (all under `~/CTT/omol25_eval/`):
- `eval_baseline.py` — main eval, supports `--limit N --verbose`.
- `scripts/pull_mlip_sif.sh` — one-time apptainer SIF pull.
- `scripts/setup_mlip_apptainer.sh` — install fairchem-core into `~/envs/mlip/` via PYTHONUSERBASE.

Plan: [`~/.llms/plans/omol25_baseline_sanity_eval.plan.md`](/home/hangrui/.llms/plans/omol25_baseline_sanity_eval.plan.md). Env design: [fair-sc.md](/knowledge/fair-sc.md#python-environments).

[^paper_table3]: Levine et al. 2025 Table 3 (p. 12) and Table 4 (p. 13). Two release columns reported — "OMol-0" (original) and "OMol-1" (refined). Released registry ckpt `esen-sm-conserving-all-omol` matches the OMol-0 row.

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
