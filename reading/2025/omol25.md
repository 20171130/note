---
title: "The Open Molecules 2025 (OMol25) Dataset, Evaluations, and Models"
arxiv: 2505.08762
---
# The Open Molecules 2025 (OMol25) Dataset, Evaluations, and Models

Levine et al. 2025, FAIR Chem. First arxiv release date unchecked; latest version Mar 2026.

## Dataset
~140M DFT calculations at the ωB97M-V/def2-TZVPD level of theory, systems up to 350 atoms, billions of CPU core-hours. Molecules only — isolated systems with explicit solvation, no periodic boundary conditions. FAIR Chem's PBC datasets (OC20 catalysts, OC22 oxides, OMat24 materials) are separate. Coverage spans small molecules, biomolecules, metal complexes, and electrolytes; varying charge and spin; 83 elements.

## On-disk format (FAIR-SC release)

Each split is 80–200 `*.aselmdb` shards. **Format is LMDB + zlib + JSON, mixed; not binary npz, not plain text.** No fairchem install needed to read — `lmdb` + `zlib` + `json` is enough.

Layers (outermost first), probed on `val/data0000.aselmdb`:

1. **LMDB** B-tree key-value store, one file per shard. This shard has 36,187 records.
2. **Keys**: short ASCII byte strings `b'1'`, `b'2'`, … (no metadata key).
3. **Values**: `zlib.compress(bytes)` — header `78 9c …`, default compression. Ratio ≈ 2× (7 KB → 15 KB on a 112-atom record).
4. **Payload**: UTF-8 **JSON text** of an ASE-dict.
5. **Numeric arrays inside the JSON** use ASE's envelope `{"__ndarray__": [shape, dtype, flat_list]}` — values are JSON numbers, so float64 is stored as decimal text. That's why a single record is ~15 KB instead of ~3 KB raw bytes.

### Top-level JSON keys
```
numbers, positions, unique_id, calculator, calculator_parameters,
energy, forces, cell, pbc, ctime, user, mtime, data
```
- `numbers` int64[N], `positions` float64[N,3], `forces` float64[N,3], `energy` float, `cell` float64[3,3], `pbc` bool[3].
- `cell` / `pbc` are present but meaningless (molecules-only; `pbc` always all-False).

### `data` sub-dict (OMol-specific)
```
source, reference_source, data_id, charge, spin, num_atoms, num_electrons,
num_ecp_electrons, n_scf_steps, n_basis, core_hours, unrestricted, nl_energy,
integrated_densities, homo_energy, homo_lumo_gap, s_squared, s_squared_dev,
warnings, fmax, mulliken_charges, lowdin_charges, composition
```
- `data_id` ∈ {`ani2x`, `metal_complexes`, `elytes`, `biomolecules`, `geom_orca6`, `orbnet_denali`, `spice`, `trans1x`, `rgd`, `reactivity`}.
- `charge` int, `spin` int multiplicity, `composition` string like `B1Br1C39F3H47N5O14P1Sb1`.
- `mulliken_charges` / `lowdin_charges` / `homo_lumo_gap` are usable secondary targets.
- Other DFT fields (`n_scf_steps`, `n_basis`, `core_hours`, ...) are training metadata.

### Reader
```python
import lmdb, zlib, json, numpy as np
env = lmdb.open(path, subdir=False, readonly=True, lock=False,
                readahead=False, meminit=False, max_readers=128)
with env.begin() as txn:
    rec = json.loads(zlib.decompress(txn.get(b'1')))
def ndarr(v):
    if isinstance(v, dict) and "__ndarray__" in v:
        s, d, dat = v["__ndarray__"]
        return np.asarray(dat, dtype=d).reshape(s)
    return np.asarray(v)
```
Working example: `CTT/omol25_eval/eval_baseline.py:44` (`iter_aselmdb`) + `:77` (`record_to_atoms`).

See [work/multimodal.md](../../work/multimodal.md#omol25-on-disk) for per-split statistics from this dataset on `fair-sc-3`.

## Baselines

eSEN, GemNet-OC, MACE, UMA — all message-passing GNNs where nodes are atoms and edges are neighbor interactions.

## Findings
- Conserving variants (`cons.`, energy-gradient forces) outperform direct (`d.`) counterparts on every split and metric.
- Within a family, larger wins: eSEN-md > eSEN-sm.
- Across families, GemNet-OC > eSEN-sm on every split and is roughly comparable to eSEN-md, except on the out-of-distribution compositions ("Comp") split where eSEN-md wins.
- Shrinking GemNet-OC's cutoff radius to eSEN's 6Å generally hurts.
- Training on the full dataset yields 50–100% better metrics than training on the 4M subset, but model trends on the two correlate well — model development can be done on 4M safely.
- No single clear winner across eSEN / GemNet-OC / MACE / UMA in the reported numbers; conserving eSEN-md and GemNet-OC are the top of the pack, with eSEN-md edging on OOD compositions. Head-to-head numbers for UMA and MACE vs the leaders are not summarized here.
