# FAIR SuperCluster

## Cluster

Login node: `hangrui-login-0`.
SLURM cluster: `fair-sc-3`.

GPU partitions:
- `h100`: 8×H100 nodes.
- `h200`: 8×H200 nodes.

Scheduling is by QOS prefix, not `--partition`. `--partition=h100` is ignored.
Available `ocp` QOSes:
- `h100_dev`: smoke tests, fastest to start.
- `h100_ocp_high`: real OCP runs.
- `h100_alignment_shared`.
- `h100_lowest`: long queue.
- `h200_*` mirrors.

`/storage/home/$USER` is FSx/NFS.

Wandb is self-hosted at `https://meta.wandb.io`. Set both `WANDB_API_KEY` and `WANDB_BASE_URL`; otherwise the client tries wandb.ai.

## Runtime findings

Both login and compute nodes are containerd-managed. This affects rootless container runtimes.

Podman is not usable:
- FSx graphroot fails with `.pivot_root` permission errors.
- Login has no `/dev/fuse`.
- Compute nodes have no CDI specs or NVIDIA OCI hooks.

Enroot import is not usable for the slime image:
- `enroot import` fails on login and compute with `failed to create ovlfs whiteout: Operation not permitted`.
- Likely cause: containerd-managed environment lacks `CAP_MKNOD`.

Apptainer on compute is the current expected path:
- Use SIF images.
- Use `apptainer exec --nv` for GPU injection.
- This avoids podman CDI/hooks and enroot whiteout conversion.

## Runtime probe checklist

When using a new runtime or project on this cluster, first allocate a small interactive compute job:

```bash
srun --qos=h100_dev --gres=gpu:1 -c 4 -t 0:15:00 bash
```

Then check:

```bash
hostname
nvidia-smi
ls /dev/fuse /dev/nvidia* 2>&1
ls /etc/cdi/ /var/run/cdi/ 2>&1
ls /usr/share/containers/oci/hooks.d/ 2>&1
which apptainer enroot podman nvidia-container-cli
cat /etc/slurm/plugstack.conf
```

## Useful commands

```bash
squeue -u $USER
sacctmgr -P -n show qos format=Name | grep -E 'h100|h200'
sacctmgr -P -n show assoc where user=$USER format=Account,User,QOS
```
