# Probing Equivariance and Symmetry Breaking in Convolutional Networks

Vadgama, Islam, Buracas, Shewmake, Moskalev, Bekkers, 2025. AMLab Amsterdam + New Theory AI + UC Berkeley + QurAI. [arxiv](https://arxiv.org/abs/2501.01999).

## Position
Counterweight to the drop-equivariance trend in this survey. The framing — "non-equivariant models recover equivariant behavior at scale" — is what the molxformer / AF3 / Eissler thread asserts; this paper investigates that claim under controlled conditions and concludes the opposite holds for the tasks they study.

## Setup
Introduces Rapidash, a unified regular-group-conv architecture that exposes the equivariance constraint as a knob (T(3), SE(3), isotropic SE(3) variants) with otherwise matched components. Equivalent to a steerable tensor field network via Fourier on the sphere, and proven to be an SE(3)-equivariant universal approximator.

## Findings
- Equivariant models outperform less-constrained alternatives when the equivariance matches task geometry.
- Scaling channel capacity or training compute helps both, but does not close the gap.
- Strongly equivariant models are more data-efficient.
- Explicit symmetry-breaking via geometric reference frames (e.g. pose conditioning) on top of equivariant backbones consistently helps further; breaking equivariance via geometric input features helps only when aligned with task geometry.
- SOTA on QM9 generation/property prediction and CMU motion prediction using Rapidash + symmetry-breaking.

## Caveats
Benchmarks are smaller-scale (QM9, ShapeNet, CMU motion) than the MLIP and protein-structure regime where the equivariance-dropping papers operate. Whether the gap genuinely closes at OMol25 / AlphaFold-data scale is not directly tested here. The paper is the strongest published evidence against premature generalization of the "scale beats priors" claim, but it does not refute it in the data-rich regime.

## Why this matters for the survey
Forces a more careful framing of the trend. The honest summary is: "drop equivariance" wins in data-rich regimes (MLIP foundation models, AlphaFold-scale structure prediction) where augmentation + scale can substitute; equivariance still wins in data-modest regimes and when the symmetry aligns with task geometry. The two camps differ less on architecture than on data regime.
