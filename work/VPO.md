# VPO

## FAIR SuperCluster run

As of 2026-05-19 23:00 PDT, the work is on branch `fair-sc` in `/storage/home/hangrui/VPO`, not pushed yet. Commits: `b80bc30`, `e1d440d`, `fe3a612`, `e6d9ed6`.

Goal: run `vpo0.sh`, the 8K `Qwen/Qwen3-1.7B` VPO smoke test, on [FAIR SuperCluster](/knowledge/fair-sc.md).

Cluster/runtime assumptions are in [FAIR SuperCluster](/knowledge/fair-sc.md). VPO should use the apptainer path there unless new evidence contradicts it.

Resume:
1. Check whether the background apptainer pull finished:
   - `squeue -u $USER`
   - `tail -f /tmp/apptainer_pull.log`
   - `ls -lh /storage/home/hangrui/podman-images/slime-latest.sif`
2. If it works, rewrite `/storage/home/hangrui/VPO/env.sh`, `pull_image.sh`, `run.sh`, `sbatch_vpo.sh`, and `pull_assets.sh` for apptainer:
   - `apptainer pull slime-latest.sif docker://slimerl/slime:latest` from a compute node.
   - `apptainer exec --nv --bind $HOME:/root <sif> bash /root/VPO/<script>`.
3. Smoke test on 1 GPU: `nvidia-smi` and `python -c "import torch; print(torch.cuda.device_count())"`.
4. Run `pull_assets.sh` to download HuggingFace datasets/models and convert HF weights to Megatron `torch_dist`.
5. Submit the 8-GPU run with `sbatch sbatch_vpo.sh`.

## Codebase issues found

- Hard-coded wandb key in `vpo.sh`, `baseline.sh`, and `slurm.sh`. The repo is private, so this is not urgent, but the code should read from env.
- `cleanup_procs` used `pkill -9 python|ray` without `-u $USER`, which could kill other tenants on shared nodes.
- The retry loop had no cap, so bad configs could burn GPU-hours forever. Added `MAX_RESTARTS=3`.
- Ray dashboard was bound to `0.0.0.0`; bind to `127.0.0.1` on shared clusters.
- `PYTHONPATH=/root/Megatron-LM` and `WANDB_DIR=/data/wandb` were container-specific; parameterize them.
- Eval data used `$BASE_DIR/projects/VPO/datasets/...` while training data used `$BASE_DIR/datasets/...`; use one layout.
- `cp -r patch/* $BASE_DIR/` silently overwrites edits; prefer idempotent sync.
- `prep.sh` used a zsh micromamba hook from bash.
- `baseline.sh` always set `--ckpt-step 79`, so fresh runs crash.
