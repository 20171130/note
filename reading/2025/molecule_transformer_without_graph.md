---
title: Transformers Discover Molecular Structure Without Graph Priors
arxiv: 2510.02259
---
# Transformers Discover Molecular Structure Without Graph Priors

(https://arxiv.org/pdf/2510.02259)

Used OMol25 dataset for MLIP, 1B model.

Pretraining: autoregressive language modeling, predicting text tokens and discretized vectors (coordinates, energy, forces).

Finetuning: bidirectional attention. Removed positional embedding for permutation invariance. Predicts energy and force directly, no discrete input/output.

Compared to eSEN: better energy, worse force, comparable overall. Observed predictable scaling laws.
