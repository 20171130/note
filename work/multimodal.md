# Dynamics Transformer

Crystal structure with force as labels is arguably a good training dataset, with aligned token-coordinate pairs.


## Motivation
Is it possible to merge other network architectures with transformers, rather than treating them only as inputs?
It could connect to ideas like visual thinking, spatial memory, and a sixth sense—or to multimodal-native models where other modalities are first-class citizens.
A brain that can speak while thinking in a non-linguistic way.
We do not understand quantum mechanics intuitively, could a model do better than us, what if it has complex valued, or spinor neural activities?

## Related Work
How to align nodes in a multimodal message-passing network with transformer tokens, and how to join text space with multimodal space.
For transformers today we join the two spaces by summation: convert multimodal input to tokens and concatenate them with text.
The problem is that we must impose an arbitrary linear causal order.
With an RNN we could use an arguably more elegant mechanism: product.
we can place a multimodal block sequentially or in parallel with each attention block, tokenwise, but this is computationally expensive, and the scale of the system must be predetermined.
Can we amortize multimodal compute with the transformer?

## Architecture
We can associate each text token with a multimodal patch.
In a dynamics transformer, input is a text token and output is that token plus k 3D coordinates - we assign each text token with k atoms.
This yields an equivariant autoregressive model for joint text generation and dynamics evolution, with a vanilla transformer as a subnetwork when restricted to invariant components.
For intuition, add a time dimension to the multimodal representation—a trajectory snapshot (Lagrange, like a GNN) or block (Euler, like a CNN).
The first is usually more natural than the second, which requires the position of each token predetermined.
Example: reading CH₄ + 2O₂ → CO₂ + 2H₂O, the model assigns atom coordinates token by token.
The equivariant part can be made localized in both space and time, therefore with a sparse attention pattern for performance and scalability.


## Training
The fundamental problem, then, is how to assign coordinates to each patch.
For some tokens in some corpus, correspondence to atom coordinates is natural — supervised learning can bootstrap from there.
In general, predetermining a correspondence between text tokens and atoms is often suboptimal.
How many atoms per token? It depends on information density in the text: fewer than one for MD trajectories, more than one for protein/nucleic acid sequences. Three atoms per token (roto-translation of a rigid body) is a reasonable upper bound. (Later we will discuss how to elegantly handle higher information density.)
In general, the model has freedom to choose how to map tokens to atoms, as an internal model for accurate next-token prediction.
We can train on pure text data: teacher forcing for the text part, GRPO with future cross-entropy loss for the coordinates.
It should also be trained on text descriptions of MD trajectories.
Although we use reinforcement learning, we can generate arbitrarily large pretraining-scale data with dense reward, so it is more closer to pretraining in essence.
Then it ca be trained with property prediction or classification as downstream tasks.

1. Tokenization: Subword tokenizers in large language models (BPE, WordPiece) handle floats poorly; format-enforced spacing may be necessary. Integers 0–999 are usually individual vocabulary tokens, so the model can predict three digits per group.

2. Symmetry: Text is invariant. To represent vectors or tensors as text, we must break spatial symmetry and fix a reference frame—for example by prompting with (1,0,0), (0,1,0), (0,0,1) on the first token.


# Steps
1. Reproduce a simplified UMA.
2. Build the dynamics transformer.
3. Obtain MD trajectories.
4. Train on MD trajectories; compare against a baseline transformer and neural MD models.
5. Test whether MD training improves downstream tasks.
6. Spacetime of thought: add atoms and timesteps via chain-of-thought (temporal interpolation, spatial extension). Assess whether CoT helps and whether coarse-grained long-timescale prediction works better with a distributional loss than regression.

## Supplementary
1. Check whether generated coordinates are interpretable and whether the verbal channel of Spacetime of Thought is interpretable.

# Future Work
A fundemental problem is that we lose the parallel training of transformers.
We can use a diffusion language model instead, and denoise both the text and the coordinates.
