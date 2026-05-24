# TODO
Continuous Token Transformer

Think more carefully about architecture, training data, and evaluation tasks.

Brandon:
1. How to fight catastrophic forgetting? Perhaps make it closer to vanilla transformer so I can use LoRA?
2. How to deal with PBC? I think probably manual data augmentation by creating mirror cells, or chain of thought doing this automatically.
Besides architecture, another problem is data, and it's a huge problem.

Also on evaluation, what task is optimal for demonstrating our motivation? The best task may be something with little data so few/zero shot generalization is preferred, or some tasks that involve inherent ambiguity in its specification so the flexibility of text is needed.

Naming note: "Continuous Tokens" is the headline phrase of Fluid (Fan et al. 2024, "Scaling Autoregressive Text-to-image Generative Models with Continuous Tokens"), and MAR / GIVT cluster around the same terminology. Frame this work as the discrete-octree-head variant within that family rather than as a new line — the differentiator is the inner-AR octree subdivision head, not the umbrella term.

# History
Originally I designed a transformer for MD trajectories.
Zack suggested it should be applicable to all atomic, or even macroscopic, point clouds.
Then I changed it to a generative equivariant transformer.
Brandon and Ray suggested we can drop equivariance entirely.
Then after reading uni3dar_2025, recommended to me by Aaron, I invented in-token autoregressive generation for sampling numerical values and vectors.
Then the idea was generalized to the Continuous Token Transformer.

# Motivation

A multimodal-native LLM, with chemistry as first-class citizen.

![Reason in atoms](../image/reason_in_atoms.png)

A model that can communicate with us, while thinking in a fundamentally non-linguistic way.

Not a replacement for UMA — a complementary multitask, in-context learner.

First class citizen: not as text, vision or tool calls, chemistry deserves its own proper representation. LLMs can summarize a paragraph, it should be able to create coarse grain model of a system. Reason in words, now it can reason in atoms as well. Mirroring the microscopic atomic world; analogous to ideas like "visual thinking", "spatial memory", "sixth sense".

# Architecture
Each token can be a text token, a real number, or a vector.

Following recent studies, equivariance is not necessary.
Identical to a vanilla transformer, except for the embedding and prediction head for real numbers and vectors.

Parameterization is compatible with the vanilla transformer — initialized from pretrained weights for free prior knowledge.

For decoding, reserve a special `<|vectortoken|>`; when it is sampled, draw the next token from a 3D Gaussian instead.

I would argue a likelihood-based distribution loss is better than regression loss, so both text and vector prediction are measured in bits of entropy.

I think the [octree](uni3dar_2025) is a good idea.
The problem is that it is good only for coordinate generation, not for predicting arbitrary vectors like force. They also assume that the order in which points appear in the data does not matter and can be reordered into a BFS tree, which itself imposes an assumption on the data. Both are things I would like to avoid.
The merit of BFS is efficient common-ancestor path compression — no need to repeat the ancestors when generating siblings. However, we make this observation: embedding and encoding do not have to match the decoding generative process, as long as tokenization is aligned. We can embed using the continuous value directly, not via tree tokens; during decoding, we repeatedly and autoregressively sample multiple octree subdivision steps from the final representation.
I am talking about an autoregressive head for sampling a float or double-precision vector from the output of the final layer. For a 3D vector, sample from 8 octants 64 times for double precision, 32 times for float. (For a scalar, replace octants with binary halves and the step counts roughly double.)
Autoregressive generation within a token.

### In-token AR head — example: `one inch is 2.54 cm`

![Continuous Token Transformer in-token AR head](../image/continuous_token_head.svg)

Outer sequence is the usual LLM token stream — text plus a special numeric token (e.g. `<scalar_token>`, `<vector_token>`). A numeric token branches off into a small inner AR head conditioned only on that token's final hidden state (no extra context attention), emitting bits coarse → fine: sign (1 bit), exponent (11 bits, MSB → LSB), mantissa (52 bits, MSB → LSB) — 64 inner steps for a double, 32 for a float.

For a 3D vector, replace `<scalar_token>` with `<vector_token>` and emit all three axes jointly per step, so each subtoken is one of `2^3 = 8` octant states (one bit per axis at the current depth). Same coarse-to-fine ordering, same K, preserves cross-axis correlation.

Compression: multiple bit-levels can be packed into one inner subtoken (e.g. `2^16 = 65536` sub-vocab states sampling 4 times for a double), trading inner-step count for a wider per-step vocab. Not performance-critical since the inner head is light-weight.

Source: [continuous_token_head.d2](../image/continuous_token_head.d2) — render with `d2 --layout elk continuous_token_head.d2 continuous_token_head.svg`.

## Open design questions
Core idea is settled (continuous-token AR, octree inner head, drop equivariance, multimodal text-vector interleaving); the following details are still open and should be resolved (RQ-Transformer read will inform several):

1. Continuous-input embedding. xVal-style single token with value-scaled embedding, vs Fourier features at multiple frequencies, vs MLP encoder over the raw value. Trade compactness vs smoothness.
2. Inner head architecture. Per-step MLP (cheapest), mini-transformer over the K-step inner sequence (most expressive, like RQ's depth transformer), or shared head with explicit step-position embedding.


# Related Work
AF3 dropped equivariance.

[molxformer](../reading/2025/molecule_transformer_without_graph.md) dropped graph structure as well.
Interesting that their conclusion is that no prior is needed, except for continuous representation.

However, they use GPT-style pretraining + BERT-style finetuning, with two different tokenization strategies, sacrificing the ability to do generative modeling.
We should also use a distribution loss instead of regression.
This paper is a good baseline and starting point.


# Pretraining
The idea is simple. The key is scaling.

We look for data that are usually excluded from LLM training: MLIP force fields, MD trajectories, XYZ/PDB structures …

Curate a mix covering different
- force model, integrator
- ensemble, thermodynamic state
- system composition and scale
- any metadata or text we find with it (e.g. data source, timestamp …)

Feed it with everything we have.

# Fine-tuning
## Transformer Philosophy
Minimal data assumption with maximal versatility (The Bitter Lesson).

Treat all vectors as coordinates.

Global causal attention.


Unable to model fine-grained large systems beyond the ~1M context window.
May also include point clouds for macroscopic systems; what's special about chemistry is locality, and we can generate data via computation.

Lean towards this during pretraining.



## Physics Priors
Utilize physics priors for scalability and tighter hypothesis space: the cost is more data constraints and labeling.

Label vectors and group features (velocity, force…) by coordinates in training data.

Local interactions for scalability.

Markovian property for temporal sparsity.
High-quality paired data (like structure data and the paper that introduced it).


Lean towards this during posttraining.


## Reinforcement Learning
Supervised learning: learn from data. RL: fill the missing part necessary for explaining but missing from data (only question and answer in dataset), where no supervision signal is available.

This allows the model do something very different from UMA. Add atoms and timesteps for periodic boundary conditions, temporal interpolation, spatial extension, explicit solvent…

Notice that the model does not generate the structure by calling some tool. The ability to understand and generate structure is built in since pretraining, allowing it to be used flexibly per instructions. The lipoprotein particle is ambiguous; specifying it accurately is challenging and not necessary.

Notice that the prompt must contain coordinates that specify a frame of reference, otherwise we cannot generate a non-zero vector from invariant text.


# Phase 1: Pretraining and Finetuning


# Phase 2: Ablation and Evaluation

If the vector model helps: compare against an invariant transformer with a vector head.

If the text pretraining helps: compare against random initialization without text pretraining.


# Downstream Tasks
Molecular dynamics.
Structure prediction.
Property prediction and classification.

Agentic-oriented tasks.
Suggest data points where UMA is bad and explain why?

# Phase 3: Reinforcement Learning
RL for longer-timescale, coarse-grained problems.

Pure text problems, with vectors as latent only.

Interpretability of chain of thought reasoning.
