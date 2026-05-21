Very intuitive idea.
We can use a smaller and faster model to decode, and use the original model for parallel verification.
They may have different distributions, but they can agree after discrete multimodal sampling.
For example, model A predicts distribution [0.7, 0.3], model B predicts [0.5, 0.5]. If the random uniform sample is 0.3, both predict token 0.
We resample if it lies within (0.5, 0.7) instead.
The motivation is that sometimes the large model is not necessary for predicting the easy part of the text.
I am not sure how popular it is in the industry. It fits latency-critical scenarios where we can show the speculative result first and amend it later to preserve the distribution.
