---
title: How Simple Can You Go? An Off-the-Shelf Transformer Approach to Molecular Dynamics
arxiv: 2503.01431
---
# How Simple Can You Go? An Off-the-Shelf Transformer Approach to Molecular Dynamics

Eissler, Korjakow, Ganscha, Unke, Müller, Gugler, 2025. TU Berlin / BIFOLD + Korea U + MPI-Informatics + Google DeepMind. [arxiv](https://arxiv.org/abs/2503.01431).

## Position
The closest precursor to molxformer. Where molxformer drops every prior (no graph, no distance features, no equivariance, no conservation), Eissler keeps pairwise distance and displacement embeddings as input features but otherwise drops the same things. Sits between Uni-Mol (atom tokens + distance attention bias) and molxformer (raw coords, autoregressive) on the prior spectrum.

## Model — MD-ET
Edge Transformer (ET, Bergen et al.) minimally adapted for MD. Token = an edge in the fully connected graph of atoms (N×N×D tensor; diagonal entries `x_ii` represent atoms). 3-WL expressive via triangular attention over triples (i, l, j), `O(N³)` time and memory. No cutoff, fully connected. Inputs per edge: pairwise distance, pairwise displacement vector (with polar+azimuthal angles), spin/charge, atomic numbers.

## Priors dropped
- No built-in equivariance. Learned approximately via two randomly rotated and mirrored copies of each training structure (O(3) augmentation).
- No energy conservation. Forces are predicted directly, not as `-∇E`.
- No graph cutoff.

## Training
Supervised pretraining on QCML database, ~30M structures at PBE0 DFT (with dispersion). Few-shot finetuning for downstream MD benchmarks.

## Result
SOTA on several MD benchmarks after few-shot finetuning. The cost: runaway energy increase on larger structures in NVE MD; only small molecules sustain approximately energy-conserving simulations. Confirms the eSEN thesis that dropping conservation matters for long MD trajectories, even when test-set MAE is competitive.

## Why this matters for the survey
Demonstrates that the "scale and augmentation beat priors" recipe works for an MD transformer one architectural step away from molxformer — but also shows where the recipe breaks (long-trajectory energy drift). Together with eSEN, this bounds where conservation can be sacrificed.
