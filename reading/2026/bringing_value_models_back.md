Bringing Value Models Back: Generative Critics for Value Modeling in LLM Reinforcement Learning
They argued that value function is P-complete, cannot be expressed by transformer TC^0, and validated that the MSE loss is not decreasing as the models scales. So they used generative instead of discriminative value model, so we have inference time scaling. I thought about this too. Similar to reward model but value model is policy-dependent. The advantage is not very significant though.

![[Pasted image 20260511103330.png]]
![[Pasted image 20260511102332.png]]