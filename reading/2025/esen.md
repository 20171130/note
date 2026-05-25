---
title: Learning Smooth and Expressive Interatomic Potentials for Physical Property Prediction
arxiv: 2502.12147
---
# Learning Smooth and Expressive Interatomic Potentials for Physical Property Prediction

Fu, Wood, Barroso-Luque, Levine, Gao, Dzamba, Zitnick, 2025, FAIR Chem ([arxiv](https://arxiv.org/abs/2502.12147), [code](https://github.com/facebookresearch/fairchem)).

## Question
When does lower MLIP test error actually translate to better downstream physical-property prediction (relaxation, NVE MD, phonon spectra, thermal conductivity κ)? Often it doesn't — direct-force models top the OC20/OC22/Matbench-Discovery leaderboards but drift in MD.

## Energy-conservation test
The paper proposes a practical diagnostic: run NVE MD with a fixed time step on out-of-distribution systems (TM23 settings for inorganics, MD22 for organics) and measure total-energy drift. From the Verlet error bound (Hairer 2003), bounded drift implies the PES is conservative and has bounded high-order derivatives. Among models that pass, test-set energy MAE correlates strongly with property-prediction metrics; among models that fail, it doesn't. So passing the test is necessary in practice for test-error reductions to mean anything downstream — the paper doesn't claim equivalence.

## Recipe for passing the test
Architectural choices that preserve energy conservation:
- Conservative forces (`F = -∇E` via autograd) instead of a direct-force head.
- Equivariant Gated nonlinearity (Weiler 2018) directly on spherical-harmonic features, not projection to a spatial grid (avoids aliasing past Nyquist).
- All neighbors within a 6 Å cutoff, not a max-K cap (cap creates discontinuities under perturbation).
- Polynomial envelope on edge messages so values and derivatives decay smoothly to zero at the cutoff.
- Few radial basis functions (10, not 512) to limit high-frequency content.

## Direct-force pretrain → conservative finetune
Conservative training is expensive (extra backward pass, no low-precision). Pretrain a direct-force model, drop the force head, finetune with `F = -∇E`. Reaches lower validation loss than from-scratch conservative training and saves ~40% wallclock.

## Architecture lineage
eSEN is the FAIR Chem successor to eSCN / EquiformerV2; same SO(2) convolution and Equiformer-style nodewise feed-forward + equivariant LayerNorm, with the above smoothness fixes. Same equivariant-GNN-with-e3nn-irreps family as MACE / NequIP / Allegro. eSEN is the OMol25 reference baseline and the small-model backbone inside UMA.
