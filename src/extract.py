"""Extract compact, auditable tables from the Severson MATLAB v7.3 files.

Only the first 100 cycles enter the proposed prediction features. Full summary
curves are exported separately for descriptive EDA and are never model inputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

FILES = {
    "batch1": "2017-05-12_batchdata_updated_struct_errorcorrect.mat",
    "batch2_notion": "2018-02-20_batchdata_updated_struct_errorcorrect.mat",
    "batch2_official": "2017-06-30_batchdata_updated_struct_errorcorrect.mat",
    "batch3": "2018-04-12_batchdata_updated_struct_errorcorrect.mat",
}
FIELDS = ("cycle", "QDischarge", "QCharge", "IR", "Tmax", "Tavg", "Tmin", "chargetime")


def array(value) -> np.ndarray:
    return np.asarray(value).reshape(-1)


def referenced_array(file: h5py.File, reference) -> np.ndarray:
    if not reference:
        return np.array([], dtype=float)
    return array(file[reference][()])


def text_field(file: h5py.File, reference) -> str:
    if not reference:
        return ""
    raw = array(file[reference][()])
    if raw.dtype.kind in "iu":
        return "".join(chr(int(code)) for code in raw if int(code) != 0)
    return str(raw)


def finite_stat(values: np.ndarray, op, default=np.nan):
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    return float(op(vals)) if len(vals) else default


def value_at(values: np.ndarray, index: int) -> float:
    if index >= len(values):
        return np.nan
    item = float(values[index])
    return item if np.isfinite(item) else np.nan


def read_curve(file: h5py.File, cycles: h5py.Group, index: int) -> np.ndarray:
    field = cycles["Qdlin"]
    if index >= field.shape[0]:
        return np.array([], dtype=float)
    try:
        return referenced_array(file, field[index, 0]).astype(float)
    except (KeyError, ValueError, TypeError, OSError):
        return np.array([], dtype=float)


def extract_batch(batch_name: str, path: Path):
    cells, cycle_rows, curves, diagnostics = [], [], {}, []
    with h5py.File(path, "r") as file:
        batch = file["batch"]
        count = batch["summary"].shape[0]
        for index in range(count):
            cell_id = f"{batch_name}_c{index:02d}"
            descriptor_life = float(array(file[batch["cycle_life"][index, 0]][()])[0])
            policy = text_field(file, batch["policy_readable"][index, 0])
            summary = file[batch["summary"][index, 0]]
            raw = {field: array(summary[field][()]).astype(float) for field in FIELDS}
            lengths = {field: len(values) for field, values in raw.items()}
            n = min(lengths.values())
            if len(set(lengths.values())) != 1:
                diagnostics.append({"cell_id": cell_id, "issue": "summary_length_mismatch", "detail": lengths})

            for position in range(n):
                cycle_rows.append({
                    "batch": batch_name, "cell_id": cell_id,
                    "position": position, "cycle": raw["cycle"][position],
                    "cycle_life": descriptor_life,
                    "QD": raw["QDischarge"][position],
                    "QC": raw["QCharge"][position],
                    "IR": raw["IR"][position],
                    "Tmax": raw["Tmax"][position],
                    "Tavg": raw["Tavg"][position],
                    "Tmin": raw["Tmin"][position],
                    "chargetime": raw["chargetime"][position],
                })

            qd, ir, tavg, tmax, charge = (
                raw["QDischarge"], raw["IR"], raw["Tavg"], raw["Tmax"], raw["chargetime"]
            )
            cycles = file[batch["cycles"][index, 0]]
            # Summary cycle labels start at 1 and align one-to-one with Qdlin
            # references, so physical cycles 10 and 100 occupy indices 9/99.
            q10, q100 = read_curve(file, cycles, 9), read_curve(file, cycles, 99)
            voltage = referenced_array(file, batch["Vdlin"][index, 0]).astype(float)
            dq = q100 - q10 if len(q10) == len(q100) == len(voltage) and len(voltage) else np.array([])
            if len(dq):
                curves[f"{cell_id}_voltage"] = voltage.astype(np.float32)
                curves[f"{cell_id}_dq"] = dq.astype(np.float32)
            else:
                diagnostics.append({"cell_id": cell_id, "issue": "missing_dq", "detail": {
                    "q10": len(q10), "q100": len(q100), "voltage": len(voltage)}})

            early = slice(1, min(100, n))  # cycles 2..100; cycle 1 is zero in B1
            valid_cross = np.flatnonzero(
                (raw["cycle"] >= 10) & np.isfinite(qd) & (qd < 0.88))
            first_cross = float(raw["cycle"][valid_cross[0]]) if len(valid_cross) else np.nan
            protocol_family = (
                "newstructure" if "newstructure" in policy.lower() else
                "varcharge" if "varcharge" in policy.lower() else
                "slowcycle" if "slowcycle" in policy.lower() else "standard"
            )
            rec = {
                "batch": batch_name, "cell_id": cell_id, "source_position": index,
                "cycle_life": descriptor_life, "policy": policy,
                "protocol_family": protocol_family,
                "summary_n": n, "curve_n": cycles["Qdlin"].shape[0],
                "last_qd": value_at(qd, n - 1),
                "first_observed_cross_088": first_cross,
                "observed_below_088": bool(len(valid_cross)),
                # The source author used 0.885 Ah to flag unfinished Batch 3
                # records. This is an endpoint-proximity diagnostic, not proof
                # that the 0.88 Ah crossing was observed.
                "near_eol_088": bool(np.isfinite(value_at(qd, n - 1))
                                     and value_at(qd, n - 1) <= 0.885),
                "has_100_cycles": n >= 100,
                "qd_nonfinite": int(np.sum(~np.isfinite(qd))),
                "ir_nonfinite": int(np.sum(~np.isfinite(ir))),
                "qd_first": value_at(qd, 1), "qd_10": value_at(qd, 9),
                "qd_100": value_at(qd, 99),
                "qd_change_10_100": value_at(qd, 99) - value_at(qd, 9),
                "ir_10": value_at(ir, 9), "ir_100": value_at(ir, 99),
                "ir_change_10_100": value_at(ir, 99) - value_at(ir, 9),
                "early_qd_mean": finite_stat(qd[early], np.mean),
                "early_qd_std": finite_stat(qd[early], np.std),
                "early_tavg_mean": finite_stat(tavg[early], np.mean),
                "early_tmax_mean": finite_stat(tmax[early], np.mean),
                "early_charge_mean": finite_stat(charge[early], np.mean),
                "dq_mean": finite_stat(dq, np.mean),
                "dq_var": finite_stat(dq, np.var),
                "dq_min": finite_stat(dq, np.min),
                "dq_max": finite_stat(dq, np.max),
            }
            rec["log10_dq_var"] = np.log10(rec["dq_var"]) if rec["dq_var"] > 0 else np.nan
            cells.append(rec)
    return cells, cycle_rows, curves, diagnostics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch2", choices=("notion", "official", "none"), default="notion")
    args = parser.parse_args()
    names = ["batch1"]
    if args.batch2 != "none":
        names.append(f"batch2_{args.batch2}")
    names.append("batch3")
    missing = [FILES[name] for name in names if not (RAW / FILES[name]).is_file()]
    if missing:
        parser.error(f"Missing raw files: {missing}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    all_cells, all_cycles, all_curves, all_diagnostics = [], [], {}, []
    for name in names:
        cells, cycles, curves, diagnostics = extract_batch(name, RAW / FILES[name])
        all_cells.extend(cells)
        all_cycles.extend(cycles)
        all_curves.update(curves)
        all_diagnostics.extend(diagnostics)
        print(f"{name}: {len(cells)} cells; {len(cycles)} summary rows; {len(curves)//2} Delta Q curves")

    pd.DataFrame(all_cells).to_csv(PROCESSED / "cells.csv", index=False)
    pd.DataFrame(all_cycles).to_csv(PROCESSED / "cycles.csv", index=False)
    np.savez_compressed(PROCESSED / "dq_curves.npz", **all_curves)
    (PROCESSED / "diagnostics.json").write_text(
        json.dumps(all_diagnostics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Diagnostics: {len(all_diagnostics)} entries")


if __name__ == "__main__":
    main()
