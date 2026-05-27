# FAIR SuperCluster

## Cluster

Login node: `hangrui-login-0`. SLURM cluster: `fair-sc-3`. GPU partitions `h100` (8×H100), `h200` (8×H200).

Scheduling is by QOS prefix, not `--partition` (`--partition=h100` is ignored). Available `ocp` QOSes (priority, group GPU cap, per-user GPU cap, MaxWall — `sacctmgr show qos` 2026-05-27):

| QOS | Pri | Group cap (H100/H200) | Per-user cap | MaxWall | Use |
|---|---|---|---|---|---|
| `*_dev` | 100 | 2760 / 7432 | 16, 2 nodes | 24h (`DenyOnLimit`) | smoke tests; few-sec queue (verified 2026-05-24) |
| `*_ocp_high` | 100 | 512 / 520 | — | — | real OCP runs; clear w/ Ray or Zach first |
| `*_alignment_shared` | **5** | 1432 / 3424 | 1024 | — | **default for regular experiments** |
| `*_lowest` | 1 | 2760 / 7432 | 1024 | — | fallback only; in practice rarely scheduled |

`*_alignment_shared` is the go-to over `*_lowest`. Empirically (2026-05-27 12:59 PDT):

| QOS | Running GPUs | Cap util | Pending | PD/RUN |
|---|---|---|---|---|
| `h100_alignment_shared` | 1420 | 99% | 170 | 0.12 |
| `h100_lowest` | 74 | 2.7% | 320 | 4.3 |
| `h200_alignment_shared` | 1348 | 39% | 868 | 0.64 |
| `h200_lowest` | 8 | 0.1% | 336 | 42 |

`*_lowest` has huge quota headroom but pri 1 means it almost never runs — higher-priority QOSes (`*_ram_high`, `*_dream_high`, `*_sage_high`, …) fill the cluster. `*_alignment_shared` at pri 5 is the lowest QOS that actually gets scheduled.

`/storage/home/$USER` is FSx/NFS, shared across login and compute. `/tmp` is per-node — scripts and outputs must live under `$HOME`. Other users' homes are 0700; paths referenced in their config files (e.g. `mshuaibi/micromamba/envs/…` cited in OMol25 `canonical_config.yaml`) are not reusable. Verify with `ls` before planning around them.

Wandb is self-hosted at `https://meta.wandb.io`. Set both `WANDB_API_KEY` and `WANDB_BASE_URL`; otherwise the client tries wandb.ai.

Login has internet egress (verified: arxiv, pypi, huggingface, docker.io). Compute also has egress (verified: pypi).

## Runtime status

Verified on `h100-039-027`, `h100-108-194`, and several h100 dev pool nodes between 2026-05-24 and 2026-05-25.

| Tool | Login | Compute |
|---|---|---|
| `apptainer` 1.5.0 | absent | present |
| `enroot` 3.5.0 | present | present |
| `podman` | present (unusable, no CDI/hooks) | present (same) |
| `nvidia-container-cli` | — | present |
| `/dev/fuse` | absent | present |
| `/dev/nvidia*` | absent | present |
| pyxis SPANK plugin | yes (`/etc/slurm/plugstack.conf`) | yes (broken, see below) |
| CUDA modules | `module avail` shows 11.2–12.6 | same |

Anything that needs `/dev/fuse` (apptainer pulls, enroot imports) must run inside `srun`, not on login.

## Container runtimes — use apptainer

Pyxis is currently broken on the h100 compute pool: `srun --container-image=…sqsh` fails with `slurm task_prolog can not be executed (/etc/slurm/other-scripts/task_prolog.sh) No such file or directory`. Script exists on login ("Meta @cf-patch") but missing on `h100-040-244`, `h100-073-063`, `h100-133-115`, `h100-159-211` and probably the whole h100 pool. VPO's pyxis-based pipeline also never ran end-to-end. Default to apptainer until that's fixed.

Conversion cost for the same `docker://pytorch/pytorch:2.8.0-cuda12.6-cudnn9-runtime` source on `h100_dev`, 2026-05-24:
- `enroot import` → 6.1 GB sqsh in **1m48s**.
- `apptainer pull` → 3.5 GB sif in **16m06s** (single-threaded SIF assembly is FSx-bound).

| | apptainer (.sif) | enroot+pyxis (.sqsh) |
|---|---|---|
| Build cost | slow (minutes-hours for big images) | fast (minutes) |
| Run | `apptainer exec --nv $SIF cmd` from any shell | `srun --container-image=$SQSH --container-mounts=… cmd` |
| GPU injection | `--nv` mounts host CUDA + `/dev/nvidia*` | automatic when `--gres=gpu` |
| Default mounts | `$HOME`, `/tmp`, `$PWD` | none — must enumerate via `--container-mounts` |
| Use outside SLURM | yes | only via `enroot start` |
| Multi-node | wire NCCL yourself | pyxis launches per-task container, integrates with SLURM topology |

### Apptainer recipe

Pull a base image (one-time, on compute):
```bash
srun --qos=h100_dev --gres=gpu:0 -c 8 -t 0:30:00 bash -c '
export APPTAINER_CACHEDIR=$HOME/.apptainer/cache
export APPTAINER_TMPDIR=$HOME/.apptainer/tmp
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR" $HOME/podman-images
apptainer pull $HOME/podman-images/<name>.sif docker://<repo>:<tag>'
```

Run with GPU + bind mounts:
```bash
apptainer exec --nv \
  -B $HOME:$HOME -B /checkpoint:/checkpoint \
  $HOME/podman-images/<name>.sif python script.py
```

Available base SIFs in `$HOME/podman-images/`:
- `slime.sif` — Ubuntu 24.04, Python 3.12, torch 2.9.1+cu129, sglang, ray, transformers, flash_attn 2.7.4, no vllm. 16 GB. LLM / RL stack. Origin: `docker://slimerl/slime:latest`, rsync'd from Compute Canada `def-zhaolei/hangrui/`. **Do not re-pull** — the original docker→SIF conversion took ~8 h.
- `mlip-pytorch-2.8.0-cu126.sif` — pristine `pytorch/pytorch:2.8.0-cuda12.6-cudnn9-runtime`. 3.5 GB. Base for fairchem-core (which pins `torch~=2.8.0`, incompatible with slime).
- `ubuntu-base.sif` — 29 MB pristine Ubuntu 22.04, no python. Mostly useless on its own.

## FSx / NFS access patterns

`/checkpoint/*` and `$HOME` are FSx/NFS. Every filesystem op pays a network RTT.

- Don't enumerate all keys of a multi-100k-entry LMDB shard (`list(cursor.iternext(keys=True))`) — minutes per shard, often hits the inactivity timeout. Sample with `cur.first()` + `cur.next()`.
- Don't `du -sh` or `env.stat()` per shard across a big dataset. Open one shard, multiply by shard count (fairchem packs evenly; last shard may be partial → upper bound).
- Don't `find` over a deep tree without `-maxdepth`.

For real model training, stage hot data to per-node local SSD inside `srun`.

## Python environments

Constraints:
- System `python3` is 3.10 with no `numpy` and no `pip` by default. `python3 -m pip install --user` works without sudo but is tied to host 3.10.
- No conda / uv / mamba pre-installed.
- Pre-built wheels for `torch-scatter`/`torch-sparse`/`torch-cluster`/`pyg-lib` exist only for specific `(torch, CUDA, python)` triples. Building from source on this cluster = hours.

Design: two layers, separated by change rate.

A. Base layer — torch + CUDA + cuDNN, immutable, infrequent change → apptainer SIF in `$HOME/podman-images/`. One per `torch_major × cuda_major` combo.

B. Project layer — python packages, mutable, daily churn → on FSx via either:

| mechanism | how | pros | cons |
|---|---|---|---|
| `$PYTHONUSERBASE` | `PYTHONUSERBASE=$HOME/envs/<proj> pip install --user …` inside SIF | zero ceremony, survives SIF re-pulls | no lockfile |
| `uv venv` on FSx | `apptainer exec $SIF uv venv $HOME/envs/<proj>` then activate | lockfile, fast resolve, pin python | uv must match SIF python ABI; needs install |

Verified working pattern (fairchem-core 2.20.0 + ~80 deps, 1m44s on `h100_dev`):
```bash
apptainer exec --nv -B $HOME:$HOME -B /checkpoint:/checkpoint \
  --env PYTHONUSERBASE=$HOME/envs/mlip \
  --env PATH=$HOME/envs/mlip/bin:/opt/conda/bin:/usr/bin:/bin \
  $HOME/podman-images/mlip-pytorch-2.8.0-cu126.sif \
  python -m pip install --user fairchem-core
```

### PyG / geometric DL

`fairchem-core` 2.20 does NOT transitively depend on PyG — only `e3nn`, `ase`, `numba`, `numpy`, `torch`. Skip the rest of this subsection for fairchem eval.

For stacks that DO need `torch-geometric` + extensions, never build from source. Pin to the wheel index matching the base SIF's torch + CUDA:
```bash
pip install torch-scatter torch-sparse torch-cluster pyg-lib \
  -f https://data.pyg.org/whl/torch-${TORCH_VER}+cu${CUDA_VER}.html
```
Slime SIF → `torch-2.9.0+cu129`. mlip-pytorch-2.8.0-cu126 SIF → `torch-2.8.0+cu126`. Mismatched URLs silently fall back to a multi-hour source build.

### Caches (all on FSx)
```bash
export APPTAINER_CACHEDIR=$HOME/.apptainer/cache
export APPTAINER_TMPDIR=$HOME/.apptainer/tmp
export PIP_CACHE_DIR=$HOME/.cache/pip
export UV_CACHE_DIR=$HOME/.cache/uv
export HF_HOME=$HOME/.cache/huggingface
```

### Sharing across users
If we build an env worth sharing, copy it into `/checkpoint/ocp/shared/envs/<name>/` (publicly readable). Don't leave it under `$HOME` — other users can't read.

## Shared datasets

Check shared trees before downloading from elsewhere:
- `/checkpoint/ocp/shared/` — released FAIR Chem datasets and checkpoints.
- `/checkpoint/ocp-h100-2/shared/` — h100-2 mirror, sometimes older snapshots.
- `/datasets/` — generic Meta-internal datasets (vision, multimodal, etc.).

OMol25 is at `/checkpoint/ocp/shared/omol/250430-release/` (see [multimodal progress](/work/multimodal.md#omol25-on-disk)).

## Shared code / model mirrors

When the `meta` CLI is unavailable on the cluster, before declaring a public-internet question unanswerable, grep `/checkpoint/*/code/` and `*/src/` for repo mirrors.
- `/checkpoint/ocp/shared/accelerated_dynamics/code/fairchem` — world-readable mirror of the public fairchem repo (matches PyPI source).
- `/checkpoint/ocp/shared/uma_checkpoints/paper_models/puma_{sm,md,lg}_*.pt` — internal UMA paper weights (require the internal `fairchem.experimental` / `puma` backbone package to load; not on PyPI).

## HuggingFace

All FAIR Chem HF repos (`facebook/OMol25`, `facebook/UMA`, `facebook/OC25`, `facebook/ODAC25`, `facebook/OMat24`) are `gated: manual`. README returning HTTP 200 does NOT mean weights are open — probe a real `.pt` URL or `curl https://huggingface.co/api/models/<repo>` and check the `gated` field. UMA's registry name maps to a URL inside `facebook/OMol25` (not `facebook/UMA`), so OMol25 access alone unlocks the eSEN registry; UMA models still need the separate `facebook/UMA` gate.

Approval flow: request access on the repo page → set token in `~/.cache/huggingface/token` (mode 600). Apptainer bind-mounts `$HOME` by default, so the token is visible inside containers without extra `--bind`. For containers that don't read the token file, also forward `--env HF_TOKEN`.

## Runtime probe checklist

When using a new runtime or node, allocate a small interactive job and probe inside:
```bash
srun --qos=h100_dev --gres=gpu:1 -c 4 -t 0:15:00 bash
hostname; nvidia-smi | head
ls /dev/fuse /dev/nvidia*
for x in apptainer enroot podman nvidia-container-cli; do command -v $x || echo "$x MISSING"; done
ls /etc/slurm/other-scripts/task_prolog.sh   # pyxis health check
```

## Useful commands

```bash
squeue -u $USER
sacctmgr -P -n show qos format=Name | grep -E 'h100|h200'
sacctmgr -P -n show assoc where user=$USER format=Account,User,QOS
scontrol show job $JOBID
```
