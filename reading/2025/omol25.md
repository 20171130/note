---
title: "The Open Molecules 2025 (OMol25) Dataset, Evaluations, and Models"
arxiv: 2505.08762
---
# The Open Molecules 2025 (OMol25) Dataset, Evaluations, and Models

Levine et al. 2025, FAIR Chem. First arxiv release date unchecked; latest version Mar 2026.

## Dataset
~140M DFT calculations at the ωB97M-V/def2-TZVPD level of theory, systems up to 350 atoms, billions of CPU core-hours. Molecules only — isolated systems with explicit solvation, no periodic boundary conditions. FAIR Chem's PBC datasets (OC20 catalysts, OC22 oxides, OMat24 materials) are separate. Coverage spans small molecules, biomolecules, metal complexes, and electrolytes; varying charge and spin; 83 elements.

## Baselines
eSEN, GemNet-OC, MACE, UMA — all message-passing GNNs where nodes are atoms and edges are neighbor interactions.

## Findings
- Conserving variants (`cons.`, energy-gradient forces) outperform direct (`d.`) counterparts on every split and metric.
- Within a family, larger wins: eSEN-md > eSEN-sm.
- Across families, GemNet-OC > eSEN-sm on every split and is roughly comparable to eSEN-md, except on the out-of-distribution compositions ("Comp") split where eSEN-md wins.
- Shrinking GemNet-OC's cutoff radius to eSEN's 6Å generally hurts.
- Training on the full dataset yields 50–100% better metrics than training on the 4M subset, but model trends on the two correlate well — model development can be done on 4M safely.
- No single clear winner across eSEN / GemNet-OC / MACE / UMA in the reported numbers; conserving eSEN-md and GemNet-OC are the top of the pack, with eSEN-md edging on OOD compositions. Head-to-head numbers for UMA and MACE vs the leaders are not summarized here.
