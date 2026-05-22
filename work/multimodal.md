# TODO
Think more carefully about architecture, training data, and evaluation tasks.

Thank you for listening and for the feedback. I think the first question to ask is: what is the minimum prior a transformer needs in order to understand 3D point clouds? A spectrum could be:
1. Proper tokenization of floats
2. Proper embedding of floats
3. Invariance (separating direction and distance, RBFs…)
4. Equivariant representation (irreps, e3nn…)

Brandon: How to fight catastrophic forgetting? Perhaps make it closer to vanilla transformer so I can use LoRA?

How to deal with PBC?

Besides architecture, another problem is data, and it's a huge problem.

Also on evaluation, what task is optimal for demonstrating our motivation? The best task may be something with little data so few/zero shot generalization is preferred, or some tasks that involve inherent ambiguity in its specification so the flexibility of text is needed.

# Motivation

A multimodal-native LLM, with chemistry as first-class citizen.

![Reason in atoms](../image/reason_in_atoms.png)

A model that can communicate with us, while thinking in a fundamentally non-linguistic way.

Not a replacement for UMA — a complementary multitask, in-context learner.

First class citizen: not as text, vision or tool calls, chemistry deserves its own proper representation. LLMs can summarize a paragraph, it should be able to create coarse grain model of a system. Reason in words, now it can reason in atoms as well. Mirroring the microscopic atomic world; analogous to ideas like "visual thinking", "spatial memory", "sixth sense".

Architecture
Each token can be either a text token, a real number, or a vector.

Like text transformers: causal attention mask, parallel training, autoregressive generation.

Like geometric models: localized interaction, equivariance, tensor product, radial basis functions.


For pure text input, the equivariant message passing is noop.

Parameterization compatible with the vanilla transformer — initialized from pretrained for free prior knowledge.

For decoding, reserve a special `<|vectortoken|>`, if that is sampled, sample from a 3D Gaussian distribution instead.

# Architecture

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


Unable to model fine-grained large systems (~1M context window).
May be also include point cloud for macroscopic, what's special about chemistry is the locality and we can generate data via computation.

Lean towards this during pretraining.



## Physics Priors
Utilize physics priors for scalability and tighter hypothesis space: the cost is more data constraints and labeling.

Label vectors and group features (velocity, force…) by coordinates in training data.

Local interactions for scalability.

Markovian property for temporal sparsity.
High quality Paired data (like structure data and the paper introduced it).


Lean towards this during posttraining.


## Reinforcement Learning
Supervised learning: learn from data. RL: fill the missing part necessary for explaining but missing from data (only question and answer in dataset), where no supervision signal is available.
This allows the model do something very different from UMA. Add atoms and timesteps for temporal interpolation, spatial extension, explicit solvent…
Notice that the model does not generate the structure by calling some tools. The ability of understanding and generating structure is built-in since pretraining, allowing it to flexibly use it per instructions The lipoprotein particle is ambiguous, specifying it accurately is challenging and not necessary.
Notice that the prompt must contain coordinates that specifies a frame of reference, otherwise we cannot generate non-zero vector from invariant text.


# Phase 1: Pretraining and Finetuning
Reproduce a simplified UMA.

1. Build the Equivariant Transformer Decoder (1 week).

2. Obtain data and Pretrain (>4 weeks. Hard to estimate).

3. Finetuning.

# Phase 2: Ablation and Evaluation

If the vector model helps: compare against an invariant transformer with a vector head.

If the text pretraining helps: compare against random initialization without text pretraining.


# Downstream Tasks
The best task may be something with little data so few/zero shot generalization is preferred, or some tasks that involve inherent ambiguity in its specification so the flexibility of text is needed.

Molecular dynamics.
Structure prediction.
Property prediction and Classification.

Agentic oriented tasks.
Suggest data points where UMA is bad and explain it?

# Phase 3: Reinforcement Learning
RL for longer-timescale, coarse-grained problems.

Pure text problems, with vectors as latent only.

Interpretability of chain of thought reasoning.

# Q&A
Brandon's advices, try invariant first.
How to deal with PBC?
Catastrophic forgetting? Data mix or LoRA?
