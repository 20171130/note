# Generative Equivariant Transformer

## Motivation
Is it possible to merge other network architectures with transformers, rather than treating them only as inputs?
It could connect to ideas like visual thinking, spatial memory, and a sixth sense — or to multimodal-native models where other modalities are first-class citizens.
A brain that can speak while thinking in a non-linguistic way.
The goal is not to surpass UMA at what it does well, but to build a multitask, in-context learner that understands chemistry.

## Architecture
Generative Equivariant Transformer
Each token can be either a text token, a real number, or a vector.
Just like vanilla transformer, it uses causal attention mask, parallel training and autoregressive generation.
For the invariant component and pure text input, it has identical parameterization to vanilla transformer.
Therefore, we can initialize from a pretrained text transformer, getting the prior knowledge for free.
For vector input, we use localized interaction, tensor products, equivariant representation and radial basis functions. The only difference is that we add Rotary Positional Embedding.
All invariant tokens are considered to have coordinates (0, 0, 0) and infinite interaction range.

2. Symmetry: text is invariant. To generate vectors, we must break spatial symmetry and fix a reference frame — for pure text prompts, add (1,0,0), (0,1,0), (0,0,1) as the reference prompt.


## Training

### Supervised Learning
For some tokens in some corpora, correspondence to atom coordinates is natural — supervised learning can bootstrap from there.
2. MLIP force field: first read the text representation of atom types and coordinates, then predict the force on each atom.
3. MD trajectories. The key is to curate a representative mix covering force model and integrator; ensemble and
4. PDB structures..
Anything that contains text or vector, preferrable both
thermodynamic state; system composition and scale; plus any metadata (e.g. data source and timestamp), and describe them in the prompt.

### Reinforcement Learning
Although we use reinforcement learning, we can generate arbitrarily large pretraining-scale data.
Add atoms and timesteps via chain-of-thought (temporal interpolation, spatial extension, explicit solvent...).

### Downstream Tasks
Then it can be trained with property prediction or classification as downstream tasks.

# Steps
## Pretraining
1. Reproduce a simplified UMA.
2. Build the Equivariant Transformer Decoder.
3. Obtain data and Pretrain.

## Ablation
- Compare against a invariant transformer with a vector head
- Whether initializing from a pretrained text transformer helps.

## Downstream
Test whether pretraining improves downstream tasks.

## RL
If Spacetime of Thought is helpful for longer time scale coarse grain problems
If it is helpful for pure text problems, with vectors as latent only
Interpretability of spacetime of Thought
