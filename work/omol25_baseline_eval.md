# OMol25 baseline eval — research notes

Goal: reproduce a published OMol25 baseline number on `fair-sc-3` as a sanity check that our dataset path/parsing is right. Parent task: [multimodal eval sanity check](./multimodal.md).

Primary source for this note: a local checkout of the public fairchem repo at `/checkpoint/ocp/shared/accelerated_dynamics/code/fairchem` (the bkmi/`accelerated_dynamics` clone, world-readable for most files). It pins to the version with UMA + OMol25 release configs.

## Public baselines for OMol25

Per `docs/molecules/models.md`[^fc_molecules_models]:

| Model family | OMol25 release? | HuggingFace |
|---|---|---|
| UMA-S / UMA-M / UMA-L | yes, trained on a range of FAIR-chem datasets including OMol25 — recommended default | [`facebook/UMA`](https://huggingface.co/facebook/UMA) |
| eSEN trained ONLY on OMol25 | yes, "as a baseline for models trained only on OMol25" | [`facebook/OMol25`](https://huggingface.co/facebook/OMol25/tree/main) |
| GemNet-OC, MACE | not released as OMol25 checkpoints in this repo. The paper compares them, but the doc only lists UMA + eSEN downloads. Param counts and HF URLs for MACE/GemNet-OC OMol25 weights are not available in this fairchem snapshot.[^needs_public_source] |

Models are gated — users must accept the FAIR Chemistry License on HuggingFace[^fc_molecules_models].

I have NOT been able to enumerate the exact checkpoint names + param counts per HF release from this sandbox (no internet, no `meta` CLI). The dataset card and the arXiv paper are the right places to extract those.[^needs_public_source]

## On-cluster mirrors of those checkpoints

| HF release | on-cluster path |
|---|---|
| UMA `*.pt` (sm/md/lg, v1.1/v1.2, mpa variants, 530k/950k step counts) | `/checkpoint/ocp/shared/uma_checkpoints/*.pt` and `/checkpoint/ocp/shared/uma_checkpoints/new-models/` |
| UMA paper checkpoints | `/checkpoint/ocp/shared/uma_checkpoints/paper_models/puma_{sm,md,lg}_*.pt` |
| UMA-sm OMol-only baseline (matches `configs/uma/benchmark/checkpoint/uma_sm_omol.yaml`) | `/checkpoint/ocp/shared/uma_checkpoints/202505-0619-0026-495f/puma_sm_omol_baseline_final.pt` |
| Older non-UMA baselines (eqV2, GemNet-OC base, eSEN-30M MPtrj/OAM/OMat) | `/checkpoint/ocp/shared/uma_checkpoints/baseline_models/` |
| Internal eSEN OMol25 training runs (sm/md/lg × conserving/direct × 4M/All/simple), with `canonical_config.yaml` per run | `/checkpoint/ocp/shared/omol/omol_checkpoints/202504-*/`, `/checkpoint/ocp/shared/omol/omol_checkpoints/202505-*/` |
| Internal GemNet-OC OMol25 runs (v2, 4M/all, r6 cutoff, finetune) | `/checkpoint/ocp/shared/omol/omol_checkpoints/gemnet_oc/` |

Mapping internal eSEN run dirs to their `job.run_name`:

| dir | run_name |
|---|---|
| `202504-1100-4614-80e6` | `041025_esen_sm_conserving_all` |
| `202504-1122-0825-922d` | `041125_esen_sm_direct_all_loss_mean` |
| `202504-1220-4437-9e68` | `esen_041225_lg_direct` |
| `202504-1220-4446-6bad` | `esen_041225_md_direct` |
| `202504-1313-1953-f75e` | `041325_esen_sm_direct_4M` |
| `202504-1313-2143-f7d6` | `041325_esen_md_direct_4M` |
| `202504-1313-2630-d293` | `041325_esen_sm_conserving_4M` |
| `202505-0105-3330-675f` | `043025_esen_sm_direct_all` |
| `202505-0105-3340-6ec3` | `043025_esen_sm_conserving_all` |
| `202505-0117-3531-7627` | `043025_esen_sm_direct_4M` |
| `202505-0117-3536-b03c` | `043025_esen_md_direct_4M` |
| `202505-0117-5120-e475` | `043025_esen_sm_conserving_4M` |
| `202505-0118-2701-437b` | `043025_esen_sm_direct_simple` |
| `202505-0312-4104-3099` | `050325_esen_sm_conserving_all` |
| `202505-0413-1557-6ccd` | `050425_esen_sm_direct_all_12r` |
| `202505-0516-1520-65dc` | `043025_esen_md_direct_4M_finetune` |
| `202505-0715-0228-ac6c` | `043025_esen_md_direct_all_finetune` |

## How to run inference + eval — public `fairchem` CLI

The public CLI is the `fairchem` console script (shim in [`main.py`](../../../checkpoint/ocp/shared/accelerated_dynamics/code/fairchem/main.py): `from fairchem.core._cli import main`). It takes a single hydra YAML and optional dotted overrides[^fc_cli]:

```bash
fairchem -c <config.yaml> key=value other.key=value
```

The OMol25 eval has its own config: [`configs/uma/evaluate/omol_conserving.yaml`](../../../checkpoint/ocp/shared/accelerated_dynamics/code/fairchem/configs/uma/evaluate/omol_conserving.yaml). The README in that dir documents the invocation pattern[^fc_uma_eval_readme]:

```bash
fairchem -c configs/uma/evaluate/uma_conserving.yaml cluster=h100 checkpoint=uma_sm
```

For OMol25-specific eval, substitute `omol_conserving.yaml` and the OMol checkpoint:

```bash
fairchem -c configs/uma/evaluate/omol_conserving.yaml \
  cluster=h100_local \
  checkpoint=uma_sm_omol \
  runner.max_steps_per_epoch=20
```

Knobs in the OMol eval config:
- `checkpoint=uma_sm_omol` → `configs/uma/evaluate/checkpoint/uma_sm_omol.yaml` → `${cluster.checkpoint_root_dir}/202505-0619-0026-495f/puma_sm_omol_baseline_final.pt`.
- `cluster=h100` (8-rank SLURM job, `qos: ocp`, 8 nodes) or `cluster=h100_local` (single-process, `mode: LOCAL`, `ranks_per_node: 1`, `debug: True`). Use `h100_local` inside an `srun` allocation for a single-H100 smoke test.
- `dataset=omol` → reads from `${cluster.data_root_dir}/omol/250430-release/launch/` which on this cluster expands to `/checkpoint/ocp/shared/omol/250430-release/launch/{val,test,metal_ligand_ood}`. The launch tree only ships `val`, `test`, `metal_ligand_ood`; the other splits (`elytes_ood`, `uhs_ood`, `simple_*`, `train*`) live in sibling dirs and are NOT covered by this eval config.
- The runner is `fairchem.core.components.evaluate.eval_runner.EvalRunner`, which exposes `max_steps_per_epoch: int | None` (default None). Override that to limit to N batches for a smoke run.
- Forces key is `omol_forces`; energy key is `omol_energy`; eval cutoff 6 Å, max_neighbors 300, max_atoms 350 (eSEN settings).

What the config actually evaluates: `val`, `val_metal_complexes`, `val_electrolytes`, `val_biomolecules`, `val_neutralorganics`, `metal_ligand_ood`, plus the matching `test_*` splits, on the same checkpoint, concatenated via `mt_concat_dataset.create_concat_dataset` with temperature=1.0 sampling. That mirrors the per-split breakdown the paper reports.

## What to compare against (paper numbers)

I have NOT been able to load the arXiv PDF or HF dataset card from this sandbox, so I do not have a numeric target table for each baseline.[^needs_public_source] The existing [reading note](../reading/2025/omol25.md) captures only the qualitative findings:
- conserving variants beat direct on every split + metric,
- larger eSEN beats smaller,
- GemNet-OC ≈ eSEN-md except eSEN-md wins on OOD compositions,
- training on All gains 50–100% over 4M,
- no single winner across eSEN / GemNet-OC / MACE / UMA in the reported numbers.

The metrics the eval emits (per Wandb project `uma-evals` and `MLIPEvalUnit` defaults — verified from `eval_runner.py` and configs, exact metric names not yet read): force MAE (eV/Å), energy MAE per atom, possibly energy MAE, possibly conservation error for conserving models. To pin exact names + units, grep `MLIPEvalUnit` in the public source on a host where it's readable.

## Recommended single-H100 sanity run

The OMol25 release `val` shard 0 has roughly the same per-shard count as `test` shard 0 (≈35 k entries per shard × 80 shards ≈ 2.76 M entries per [multimodal.md](./multimodal.md#omol25-on-disk)). For a <30 min smoke run on one H100:

1. `srun --qos=h100_dev --gres=gpu:1 -c 8 -t 0:30:00 --pty bash` to get a compute node.
2. From inside the allocation, run:

```bash
fairchem -c configs/uma/evaluate/omol_conserving.yaml \
  cluster=h100_local \
  checkpoint=uma_sm_omol \
  runner.max_steps_per_epoch=50
```

(`50` batches × `max_atoms=350`-bucketed sampler ≈ a few thousand structures — fast, but enough for the force MAE to be within a few % of the population value.) Then read the metrics from stdout/wandb.

3. Cross-check the reported force MAE against the published table for UMA-sm-OMol on `val`. If they match within a few %, the dataset path is correct.

Caveats:
- The OMol25 paper reports per-baseline numbers across many models (eSEN-sm/md, GemNet-OC, MACE, UMA-S/M/L) and many splits. The single sanity check above only validates UMA-sm-OMol on the full `val` (subsampled by `max_steps_per_epoch`). Picking eSEN-sm-conserving-4M instead (smaller model, faster) requires using an eSEN-specific eval config — not in `configs/uma/evaluate/`. Eval configs for the OMol-only eSEN baselines live elsewhere; not yet located in this repo snapshot. Need to find them or build one mirroring the eSEN training config's dataloader block.
- `runner.max_steps_per_epoch` overrides at the CLI work because `EvalRunner` accepts it as a kwarg — but the omol_conserving.yaml does not set it explicitly, so the override has to be passed as `runner.max_steps_per_epoch=50` (hydra dotted form).
- For multi-GPU on `fair-sc-3`, the `h100` cluster preset asks for 8 nodes × 8 ranks and `qos: ocp` — substantially more than a sanity check needs. Keep `cluster=h100_local`.

## Outstanding questions to close from a host with internet

1. Public eSEN OMol25 checkpoint names + param counts + which paper-table row each corresponds to → [`facebook/OMol25` HF tree](https://huggingface.co/facebook/OMol25/tree/main).
2. Public UMA-S/M/L sizes + which UMA checkpoint is the "OMol25 paper" comparison row → [`facebook/UMA` HF tree](https://huggingface.co/facebook/UMA).
3. Exact per-baseline force MAE / energy MAE per atom / conservation error on `val`, `test`, `metal_ligand_ood` → arXiv 2505.08762.
4. Internal wiki runbook for OMol25 eval on fair-sc → `meta search.knowledge` from a devmate-enabled host.
5. Eval config for OMol-only eSEN baselines (not in `configs/uma/evaluate/` — may live under the internal `fairchem-experimental` package referenced in `omol_checkpoints/*/canonical_config.yaml`).

[^fc_molecules_models]: `/checkpoint/ocp/shared/accelerated_dynamics/code/fairchem/docs/molecules/models.md` — lists UMA + eSEN OMol25 as the two released sets, links the HF repos, recommends UMA as default. World-readable in that clone.

[^fc_cli]: `/checkpoint/ocp/shared/accelerated_dynamics/code/fairchem/main.py` and `src/fairchem/core/_cli.py` — argparse with `-c CONFIG` plus pass-through hydra overrides. Branches on `cfg.job.scheduler.mode` (SLURM/LOCAL), and in LOCAL mode either uses Ray or `local_launch` (torch elastic) to instantiate the configured `runner`.

[^fc_uma_eval_readme]: `/checkpoint/ocp/shared/accelerated_dynamics/code/fairchem/configs/uma/evaluate/README.md` — the README literally contains the `fairchem -c …yaml cluster=h100 checkpoint=…` invocations for conserving and direct eval.

[^needs_public_source]: This claim requires the public fairchem GitHub, the HuggingFace model card, or the arXiv PDF. None are reachable from the current tool sandbox (no internet, no internal `meta` CLI on `hangrui-login-0`). Verify before relying.
