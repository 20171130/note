# Autoregressive Image Generation using Residual Quantization

Lee et al. 2022, Kakao Brain + POSTECH. [arxiv](https://arxiv.org/abs/2203.01941).

Seems like an upgrade of VQ-VAE. Recall VQ-VAE: a CNN encoder downsamples the image into a 2D grid of feature vectors; each vector is replaced by its nearest neighbor in a learned codebook; the resulting 2D map of discrete codes is unrolled into a sequence and modeled by a transformer.
Essentially the power of autoregressive generation + the efficiency of vae for dealing with high resolution details.
There is codebook collapse problem and unstable training.

Typical scales:
- **Patch / downsampling factor.** VQ-GAN at 256×256 uses an 8× downsample → a 32×32 = 1024-token grid; later VQ models go further, 16× → 16×16 = 256 tokens. RQ-VAE compresses much harder: 32× downsample → 8×8 = 64 spatial positions (each with depth-D residual codes).

- **Codebook size K.** Commonly 1024 to 16,384 entries; embedding dim per code is small (256). RQ-VAE uses K=2048 (FFHQ) or K=16,384 (LSUN / ImageNet) with depth D≈4, so the effective code count is K^D — same expressivity as a K^D-entry VQ codebook without the codebook-collapse pain.

Notice the huge compression ratio: a 2^10-entry codebook (10 bits) encodes an 8×8 RGB patch (~1,500 raw bits), a ~150× reduction. This is only possible because the encoding is lossy and judged by a perceptual loss, and the codebook tiles a low-dimensional learned manifold rather than the raw patch space — the manifold hypothesis applied to image fine detail.

Now I can see why the agent says my Continuous Token Transformer is "RQ without a codebook". The spatial-transformer + depth-transformer factorization in RQ-Transformer is structurally the same as the main transformer + in-token AR head in CTT. The codebook is redundant for my case specifically because my output is at most a 3D vector. RQ-VAE needs the codebook to discretize a high-dimensional (d=256) unstructured image-patch latent.
