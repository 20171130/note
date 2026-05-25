---
title: Probing Equivariance and Symmetry Breaking in Convolutional Networks
arxiv: 2501.01999
---
# Probing Equivariance and Symmetry Breaking in Convolutional Networks

Vadgama, Islam, Buracas, Shewmake, Moskalev, Bekkers, 2025. AMLab Amsterdam + New Theory AI + UC Berkeley + QurAI. [arxiv](https://arxiv.org/abs/2501.01999).

They introduce Rapidash, a regular group-conv architecture, and compare its SE(3), SO(3), and T(3)-only (translation-only) variants under matched components. Not directly compelling for the molxformer-style bet I am evaluating. My drop-equivariance argument is about replacing group-equivariant convolutions with a much larger transformer (≥1B like molxformer) and possibly with prior knowledge transfer (initializing from a pretrained text transformer). When Vadgama et al. test whether more parameters close the gap, they scale Rapidash, not a transformer; the results stay within one model family — group convs — that is structurally different from the SOTA non-physics generative-transformer stack the trend papers use. Their scaling curve is also only a pair of points (hidden dim 256 vs 512 "inflated"), less than an order of magnitude.

## Position
Counterweight to the drop-equivariance trend in this survey. The framing — "non-equivariant models recover equivariant behavior at scale" — is what the molxformer / AF3 / Eissler thread asserts; this paper investigates that claim under controlled conditions inside the group-conv family and concludes the opposite holds for the tasks they study. Whether the conclusion extends to the transformer family or to OMol25 / AlphaFold-scale data is not tested.

## Setup
Introduces Rapidash, a unified regular-group-conv architecture that exposes the equivariance constraint as a knob (T(3), SE(3), isotropic SE(3) variants) with otherwise matched components. Equivalent to a steerable tensor field network via Fourier on the sphere, and proven to be an SE(3)-equivariant universal approximator.

## Findings
- Equivariant models outperform less-constrained alternatives when the equivariance matches task geometry.
- Scaling channel capacity or training compute helps both, but does not close the gap.
- Strongly equivariant models are more data-efficient.
- Explicit symmetry-breaking via geometric reference frames (e.g. pose conditioning) on top of equivariant backbones consistently helps further; breaking equivariance via geometric input features helps only when aligned with task geometry.
- SOTA on QM9 generation/property prediction and CMU motion prediction using Rapidash + symmetry-breaking.

## Caveats
- All comparisons are inside Rapidash, a regular group-conv architecture; no transformer baseline (and no large pretrained transformer initialization) is tested. So the result is "more equivariance beats less equivariance, *within group convs*", not "equivariance beats transformers".
- Capacity scaling is a 2-point ablation (hidden dim 256 vs 512 "inflated"), well under one order of magnitude.
- Benchmarks are smaller-scale (QM9, ShapeNet, CMU motion) than the MLIP and protein-structure regime where the equivariance-dropping papers operate. Whether the gap genuinely closes at OMol25 / AlphaFold-data scale is not directly tested.

The paper is the cleanest published evidence against premature generalization of the "scale beats priors" claim, but it does not address the specific bet of "drop equivariance, switch to large pretrained transformer".

## Why this matters for the survey
Forces a more careful framing of the trend. Honest summary: within group-conv architectures and at small data, equivariance still wins; the open question — not closed by this paper — is whether transformer-family models at MLIP / AlphaFold scale escape this. The two camps differ less on architecture style than on (architecture family × data regime), and Vadgama controls one of those axes but not the other.
