# Accurate Structure Prediction of Biomolecular Interactions with AlphaFold 3

Abramson et al. 2024, Google DeepMind + Isomorphic Labs. Published in Nature 630, 493 (13 June 2024). [PDF](https://www.nature.com/articles/s41586-024-07487-w.pdf).

## Headline
Single deep-learning model for the joint structure of complexes spanning proteins, nucleic acids, small molecules, ions, and modified residues — replacing the separate AlphaFold-Multimer and ligand-docking tools that preceded it. Beats specialized SOTA on protein–ligand, protein–nucleic-acid, and antibody–antigen tasks.

## What changed from AF2

| Aspect | AF2 | AF3 |
|---|---|---|
| Trunk | Evoformer, heavy MSA processing | Pairformer (48 blocks), MSA module much smaller |
| Per-residue frames + IPA | yes (Invariant Point Attention in the structure module) | dropped |
| Structure head | deterministic regression over residues (one structure per pass) | diffusion over raw atom coordinates conditioned on token-level single + pair representations |
| Equivariance | architectural (IPA is invariant; structure module uses frames) | none — paper explicitly omits it: "no invariance or equivariance with respect to global rotations and translation of the molecule are required in the architecture" |
| Achieving rotation/translation symmetry | architecture | random rotation + translation augmentation of training inputs |
| Scope | single chains; AF-Multimer was a separate later release | proteins + nucleic acids + small molecules + ions + modified residues, unified |
| Confidence | pLDDT, PAE (regressed against structure-module output) | pLDDT + PAE + PDE, predicted via a diffusion "mini-rollout" because per-step diffusion training doesn't expose full structures |

Triangle (O(N³)) attention/multiplicative updates on the pair representation are kept in Pairformer.

## Priors kept vs dropped
The "drop the priors" framing is partially misleading. AF3 drops architectural symmetry priors but keeps connectivity priors.

Kept:
- Polymer / ligand connectivity. The atom-level diffusion uses *sequence-local* attention (3 blocks before and 3 after the 24 global-attention token blocks; Fig. 2b). "Sequence-local" means local along the polymer chain (which atoms are bonded into which residue, which residues into which chain), not a radial 3D cutoff. Ligands enter via SMILES, so bond connectivity is given.
- Pair representation with triangle updates / triangle attention. Geometric consistency prior over pair distances, O(N³). Not physics, but a strong inductive bias on relational structure.
- Biology priors: MSA + templates (heavily de-emphasized vs AF2 but still present).

Dropped:
- E(3) equivariance (recovered via random rotation+translation augmentation of training inputs).
- Per-residue frames + IPA.
- Torsion-based residue parametrizations.
- Stereochemical violation losses.
- Any radial / distance-cutoff graph construction at the token level. Token-level attention is global; the "graph" at this level is trivially complete.
- Any energy / force field / MD-style smoothness / conservation. AF3 is structure prediction only, not a potential.

So a cluster is indeed a "trivial graph" at token level, but the atom-level processing still walks the polymer connectivity graph rather than the spatial neighborhood graph.

## Hallucination control via cross-distillation
Generative diffusion can invent plausible-looking structure in disordered regions. AF3 mitigates by training on AF-Multimer (v2.3) predictions in addition to ground-truth structures — those predictions render disorder as long extended loops, so AF3 learns the same convention.

## Relevance to the survey thesis
AF3 belongs in the same tier as molxformer: drops both E(3) equivariance and the spatial graph. Token-level attention is global; the residual "graph" is polymer connectivity, given as input metadata rather than constructed from coordinates. Same recipe as molxformer on the regression side: no architectural symmetry prior, learned approximate equivariance through training-time random rotation/translation augmentation, scale and data to compensate. Two existence proofs at different problem scales (single-protein structure prediction; MLIP energy/force regression).
