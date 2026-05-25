---
title: "Uni-3DAR: Unified Cross-Scale 3D Generation and Understanding via Autoregressive Modeling"
arxiv: 2503.16278
---
# Uni-3DAR: Unified Cross-Scale 3D Generation and Understanding via Autoregressive Modeling

Lu, Lin, Yao, Gao et al. 2025, DP Technology + AI for Science Institute + Peking University. [arxiv](https://arxiv.org/abs/2503.16278), [code](https://github.com/dptech-corp/Uni-3DAR).

## Tokenization
Generates the whole point cloud as a BFS traversal of an octree rather than emitting points one at a time. Each non-leaf node's eight children form a length-8 binary occupancy mask, so the child list is folded into a single token with 2⁸ = 256 possible states. Leaf nodes additionally carry accurate coordinates and domain-specific payload (atom type, etc.).

Two key tricks beyond the base octree:
- 2-Level Subtree Compression (2LSC): merges two octree levels into one token, shortening the sequence by up to 8x at the cost of larger per-token vocabulary.
- Masked Next-Token Prediction (MNTP): handles dynamically varying token positions introduced by compression. Standard AR assumes fixed sequential positions; MNTP keeps the AR objective while letting position metadata vary per token.

For macroscopic-scale point clouds the octree leaves are too coarse, so they add a VQ-VAE on 16³ voxel patches at 512³ voxel resolution. So Uni-3DAR is "pure octree" only for microscopic structures; macroscopic uses octree + VQ.

Multi-frame conditioning lets one model handle conditional tasks. Examples:
- Crystal generation as 2-frame: lattice vertices → atoms inside the lattice.
- PXRD-CSP: one composition token + four PXRD-spectrum tokens (1200-dim PXRD vector split into four conditional tokens) → crystal.
- Docking: 3-frame (protein → initial ligand → docked pose), pose ranked by cumulative AR probability.

## Experiments
Six task families, separately trained per benchmark with identical hyperparameters. Joint training across tasks is deferred.

| Task | Datasets | Result vs SOTA |
|---|---|---|
| 3D molecule generation | QM9, GEOM-DRUG | Beats EDM, GeoLDM, UniGEM* on Atom/Mol Stability, Validity, Uniqueness. QM9 Mol Sta 93.7%, Validity 98.0% — both highest reported. |
| Crystal generation (de novo + CSP + PXRD-CSP) | Carbon-24, MP-20, MPTS-52, MP-20+PXRD | Largest gains here. MP-20 CSP RMSE 0.0566 → 0.0317; PXRD-guided MP-20 RMSE 0.0707 → 0.0276 (+256% relative). |
| Macroscopic 3D objects | ShapeNet airplane/chair/car (512³ voxels, VQ-VAE patches) | Beats LION, PVD on 1-NNA (CD and EMD). |
| Protein pocket prediction | CASF-2016 + PDBBind v2020 + MOAD | Matches Vabs-Net on IoU using only 3D structure (no ESM embeddings, no SASA). |
| Molecular docking | PDBbind2020 | Top-1 RMSD<1Å 44.75% vs SurfDock 40.96%; <2Å 69.06% vs 68.41%; median 1.08 vs 1.18 Å. Top-5 slightly worse (implicit AR-probability scoring vs explicit scoring model). |
| Property prediction (after pretraining) | small molecules + 8 homopolymer DFT props | Top-1 on 4/10 mol and 4/8 polymer splits; top-2 on most. Competitive with specialized Uni-Mol / SpaceFormer. |

Reports ~21.8x faster inference than diffusion baselines.

## What this paper does for the survey thesis
The widest scale-range existence proof for "discrete spatial tokens + AR" as a unified recipe across molecules, crystals, proteins, and macroscopic objects. Beats diffusion baselines on most leaderboards while running an order of magnitude faster at inference. Extends the molxformer point: not just MLIP-scale energy/force regression, but generation, prediction, conditional tasks all in one architecture.

The principal limitation is the lack of joint training in the reported results — each task gets its own checkpoint. Joint training is the natural next step and would test whether one model can carry all tasks simultaneously (the actual "foundation model" claim).

## Open questions
- Forces / continuous payload. Paper only handles coords + atom types. To extend to forces (or any other continuous per-atom quantity), options are: (a) add a continuous head on the leaf payload — reintroduces the loss-balancing problem; (b) quantize the force into the leaf token's payload — increases vocab. No explicit experiment.
- CoT over structures. The multi-frame design already supports stepwise reasoning across structures (docking is 3 frames; PXRD-CSP uses conditioning frames). Each frame is its own octree sequence. Mechanism is there even though the paper does not call it CoT.