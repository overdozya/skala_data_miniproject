"""Day 1 exploratory analysis. No predictive model is fitted here."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr, ks_2samp

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "results" / "figures"
TABLES = ROOT / "results" / "tables"
PALETTE = {"batch1": "#2664a5", "batch2_notion": "#c07822",
           "batch2_official": "#c07822", "batch3": "#9a4ca2"}
DISPLAY = {"batch1": "Batch 1", "batch2_notion": "Batch 2",
           "batch2_official": "Batch 2 (author)", "batch3": "Batch 3"}
FEATURES = [
    "qd_first", "qd_10", "qd_100", "qd_change_10_100",
    "ir_10", "ir_change_10_100", "early_tavg_mean",
    "early_tmax_mean", "early_charge_mean", "dq_mean",
    "dq_var", "dq_min",
]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def parse_policy(text: str):
    match = re.match(r"^(\d+(?:\.\d+)?)C\((\d+)%\)-(\d+(?:\.\d+)?)C", str(text))
    if not match:
        return np.nan, np.nan, np.nan
    return tuple(float(value) for value in match.groups())


def bootstrap_spearman(data: pd.DataFrame, feature: str, draws=1200, seed=91):
    subset = data[[feature, "cycle_life"]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(subset) < 8 or subset[feature].nunique() < 3:
        return {"n": len(subset), "rho": None, "lo": None, "hi": None}
    x, y = subset[feature].to_numpy(), subset["cycle_life"].to_numpy()
    rho = float(spearmanr(x, y).statistic)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(subset), size=(draws, len(subset)))
    boots = np.array([spearmanr(x[idx], y[idx]).statistic for idx in indices])
    boots = boots[np.isfinite(boots)]
    return {"n": len(subset), "rho": round(rho, 4),
            "lo": round(float(np.quantile(boots, 0.025)), 4),
            "hi": round(float(np.quantile(boots, 0.975)), 4)}


def policy_bootstrap(data: pd.DataFrame, feature: str, centered: bool,
                     draws=1200, seed=2026):
    """Resample whole policies; optionally remove each policy's mean first."""
    subset = data[["policy", feature, "cycle_life"]].replace(
        [np.inf, -np.inf], np.nan).dropna()
    groups = []
    for _, group in subset.groupby("policy"):
        x = group[feature].to_numpy(dtype=float)
        y = group.cycle_life.to_numpy(dtype=float)
        if centered:
            x, y = x - x.mean(), y - y.mean()
        groups.append((x, y))
    if len(groups) < 3:
        return {"n_policies": len(groups), "rho": None, "lo": None, "hi": None}
    x = np.concatenate([g[0] for g in groups])
    y = np.concatenate([g[1] for g in groups])
    rho = float(spearmanr(x, y).statistic)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(draws):
        chosen = rng.integers(0, len(groups), len(groups))
        sampled_x = np.concatenate([groups[i][0] for i in chosen])
        sampled_y = np.concatenate([groups[i][1] for i in chosen])
        value = spearmanr(sampled_x, sampled_y).statistic
        if np.isfinite(value):
            boots.append(value)
    return {"n_policies": len(groups), "rho": round(rho, 4),
            "lo": round(float(np.quantile(boots, 0.025)), 4),
            "hi": round(float(np.quantile(boots, 0.975)), 4)}


def knee_one(group: pd.DataFrame, life: float):
    """Exploratory two-line knee; late-life data are EDA-only."""
    sub = group.loc[
        (group["cycle"] >= 100) & (group["cycle"] <= life),
        ["cycle", "QD"],
    ].replace([np.inf, -np.inf], np.nan).dropna().sort_values("cycle")
    if len(sub) < 220:
        return np.nan, np.nan, np.nan, False
    x = sub["cycle"].to_numpy()
    y = sub["QD"].rolling(7, center=True, min_periods=1).median().to_numpy()
    base = np.polyfit(x, y, 1)
    base_sse = np.sum((y - np.polyval(base, x)) ** 2)
    candidates = np.unique(np.linspace(70, len(x) - 70, 40, dtype=int))
    best = (np.inf, None, None, None)
    for split in candidates:
        left = np.polyfit(x[:split], y[:split], 1)
        right = np.polyfit(x[split:], y[split:], 1)
        sse = np.sum((y[:split] - np.polyval(left, x[:split])) ** 2)
        sse += np.sum((y[split:] - np.polyval(right, x[split:])) ** 2)
        if sse < best[0]:
            best = (sse, x[split], left[0], right[0])
    gain = 1 - best[0] / base_sse if base_sse > 0 else np.nan
    slope_ratio = abs(best[3] / best[2]) if best[2] and np.isfinite(best[2]) else np.nan
    found = bool(
        np.isfinite(gain) and np.isfinite(slope_ratio)
        and gain >= 0.20 and slope_ratio >= 1.5 and best[3] < best[2] < 0
    )
    return float(best[1]), float(gain), float(slope_ratio), found


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    cells = pd.read_csv(PROCESSED / "cells.csv")
    cycles = pd.read_csv(PROCESSED / "cycles.csv")
    curves = np.load(PROCESSED / "dq_curves.npz")
    order = [batch for batch in ("batch1", "batch2_notion", "batch2_official", "batch3")
             if batch in set(cells["batch"])]
    cells[["c_rate_1", "switch_pct", "c_rate_2"]] = pd.DataFrame(
        cells["policy"].map(parse_policy).tolist(), index=cells.index
    )
    cells["long_1000"] = cells["cycle_life"] > 1000
    cells["short_500"] = cells["cycle_life"] < 500
    cells["class_550"] = cells["cycle_life"] >= 550

    # Q1: cell-level lifetime distributions and target balance.
    stats = {}
    for batch in order:
        sub = cells[cells.batch == batch]
        life = sub.cycle_life.dropna()
        grids = [curves[f"{cid}_voltage"] for cid in sub.cell_id
                 if f"{cid}_voltage" in curves]
        reference_grid = grids[0] if grids else np.array([])
        grid_consistent = all(
            len(grid) == len(reference_grid)
            and np.allclose(grid, reference_grid, atol=1e-6)
            for grid in grids
        )
        if not grid_consistent:
            raise ValueError(
                f"{batch}: voltage grids differ; interpolate to a common grid "
                "before aggregating Delta Q curves"
            )
        stats[batch] = {
            "n_cells": len(sub), "n_labeled": len(life),
            "n_unlabeled": int(sub.cycle_life.isna().sum()),
            "n_near_eol_labeled": int((sub.near_eol_088 & sub.cycle_life.notna()).sum()),
            "n_distant_endpoint_labeled": int((~sub.near_eol_088 & sub.cycle_life.notna()).sum()),
            "n_observed_below_088": int(sub.observed_below_088.sum()),
            "n_label_matches_observed_cross": int(np.isclose(
                sub.cycle_life, sub.first_observed_cross_088,
                equal_nan=False).sum()),
            "n_label_equals_record_length_plus1": int(
                (sub.cycle_life == sub.summary_n + 1).sum()),
            "n_policies": int(sub.policy.nunique()),
            "n_labeled_policies": int(sub.loc[sub.cycle_life.notna(), "policy"].nunique()),
            "life_min": float(life.min()), "life_q1": float(life.quantile(.25)),
            "life_median": float(life.median()), "life_q3": float(life.quantile(.75)),
            "life_max": float(life.max()), "life_mean": float(life.mean()),
            "n_short_500": int(sub.short_500.sum()),
            "n_long_1000": int(sub.long_1000.sum()),
            "n_class_550_positive": int(sub.class_550.sum()),
            "n_100_cycles": int(sub.has_100_cycles.sum()),
            "qd_nonfinite": int(sub.qd_nonfinite.sum()),
            "ir_nonfinite": int(sub.ir_nonfinite.sum()),
            "n_dq": int(sum(f"{cid}_dq" in curves for cid in sub.cell_id)),
            "voltage_grid_points": int(len(reference_grid)),
            "voltage_grid_min": float(np.min(reference_grid)) if len(reference_grid) else None,
            "voltage_grid_max": float(np.max(reference_grid)) if len(reference_grid) else None,
        }
    pd.DataFrame(stats).T.to_csv(TABLES / "batch_quality_life.csv")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    bins = np.arange(100, 2401, 150)
    for batch in order:
        life = cells.loc[cells.batch == batch, "cycle_life"].dropna()
        ax[0].hist(life, bins=bins, alpha=.50, label=f"{DISPLAY[batch]} (n={len(life)})",
                   color=PALETTE[batch])
        xs = np.sort(life)
        ax[1].step(xs, np.arange(1, len(xs) + 1) / len(xs), where="post",
                   label=DISPLAY[batch], color=PALETTE[batch], linewidth=2)
    ax[0].set(xlabel="Cycle life", ylabel="Cells", title="Lifetime distribution")
    ax[1].set(xlabel="Cycle life", ylabel="Fraction of cells", title="Empirical CDF")
    ax[0].legend(fontsize=8)
    ax[1].legend(fontsize=8)
    save(fig, "01_life_distribution.png")

    # Q2: full-life curves only for descriptive EDA; knee is a diagnostic, not a feature.
    fig, axes = plt.subplots(len(order), 1, figsize=(10, 3.1 * len(order)), sharex=True)
    axes = np.atleast_1d(axes)
    knee_rows = []
    for axis, batch in zip(axes, order):
        sub_cells = cells[(cells.batch == batch) & cells.cycle_life.notna()].sort_values("cycle_life")
        selected = list(sub_cells.iloc[np.unique(np.linspace(
            0, len(sub_cells) - 1, min(8, len(sub_cells)), dtype=int))].cell_id)
        for cell_id in selected:
            one = cycles[cycles.cell_id == cell_id]
            life = float(sub_cells.loc[sub_cells.cell_id == cell_id, "cycle_life"].iloc[0])
            one = one[one.cycle >= 10].sort_values("cycle")
            distant = not bool(sub_cells.loc[sub_cells.cell_id == cell_id,
                                             "near_eol_088"].iloc[0])
            axis.plot(one.cycle, one.QD.rolling(7, min_periods=1).median(),
                      alpha=.68, linewidth=1.1, linestyle="--" if distant else "-",
                      label=f"{cell_id.split('_')[-1]}: {life:.0f}")
        axis.axhline(.88, color="#c33438", linestyle="--", linewidth=1,
                     label="0.88 Ah EOL reference")
        axis.set(ylabel="Discharge capacity (Ah)", title=f"{DISPLAY[batch]}: representative labeled cells (dashed = endpoint far above 0.88 Ah)")
        axis.legend(ncol=3, fontsize=7, loc="lower left")
        for cell_id, one in cycles[
            cycles.cell_id.isin(sub_cells.cell_id)
        ].groupby("cell_id", sort=False):
            life = float(sub_cells.loc[sub_cells.cell_id == cell_id, "cycle_life"].iloc[0])
            point, gain, ratio, found = knee_one(one, life)
            knee_rows.append({"batch": batch, "cell_id": cell_id, "cycle_life": life,
                              "knee_cycle": point, "knee_fraction": point/life,
                              "sse_gain": gain, "slope_ratio": ratio,
                              "knee_heuristic": found})
    axes[-1].set_xlabel("Cycle")
    save(fig, "02_degradation_curves.png")
    # Landscape summary keeps the evidence readable on presentation pages.
    fig, axes = plt.subplots(1, len(order), figsize=(15.5, 4.7), sharey=True)
    axes = np.atleast_1d(axes)
    for axis, batch in zip(axes, order):
        sub = cells[(cells.batch == batch) & cells.cycle_life.notna()].sort_values("cycle_life")
        picks = np.unique(np.linspace(0, len(sub) - 1, 4, dtype=int))
        for idx in picks:
            row = sub.iloc[idx]
            one = cycles[(cycles.cell_id == row.cell_id) & (cycles.cycle >= 10) &
                         (cycles.cycle <= row.cycle_life)]
            axis.plot(one.cycle, one.QD.rolling(7, min_periods=1).median(),
                      lw=1.8, alpha=.86, linestyle="--" if not row.near_eol_088 else "-",
                      label=f"{row.cell_id.split('_')[-1]}: {row.cycle_life:.0f}")
        axis.axhline(.88, lw=1, linestyle=":", color="#b5262d")
        axis.set(title=DISPLAY[batch], xlabel="Cycle", xlim=(0, 2000))
        axis.grid(alpha=.15)
        axis.legend(fontsize=8, loc="upper right", frameon=True,
                    facecolor="white", framealpha=.95, edgecolor="#d9e2e8")
    axes[0].set_ylabel("Discharge capacity (Ah)")
    fig.suptitle("When does the capacity decline accelerate?", fontsize=15)
    save(fig, "09_degradation_landscape.png")
    knees = pd.DataFrame(knee_rows)
    knees.to_csv(TABLES / "exploratory_knees.csv", index=False)
    for batch in order:
        sub = knees[knees.batch == batch]
        stats[batch]["knee_detected"] = int(sub.knee_heuristic.sum())
        stats[batch]["knee_fraction_median"] = (
            float(sub.loc[sub.knee_heuristic, "knee_fraction"].median())
            if sub.knee_heuristic.any() else None)

    # Q3: physical cycles 100 and 10, stored at zero-based indices 99 and 9.
    fig, axes = plt.subplots(len(order), 1, figsize=(9.5, 2.9 * len(order)), sharex=True)
    axes = np.atleast_1d(axes)
    for axis, batch in zip(axes, order):
        sub = cells[(cells.batch == batch) & cells.cycle_life.notna()].sort_values("cycle_life")
        low = sub.iloc[:max(1, len(sub)//3)]
        high = sub.iloc[-max(1, len(sub)//3):]
        for label, group, color in (("shorter third", low, "#cd5c5c"),
                                    ("longer third", high, "#25765b")):
            arrays = [curves[f"{cid}_dq"] for cid in group.cell_id
                      if f"{cid}_dq" in curves]
            if not arrays:
                continue
            stack = np.vstack(arrays)
            v = curves[f"{group.cell_id.iloc[0]}_voltage"]
            axis.plot(v, np.median(stack, axis=0), color=color, label=f"{label} (n={len(stack)})")
            axis.fill_between(v, np.quantile(stack, .25, axis=0),
                              np.quantile(stack, .75, axis=0), color=color, alpha=.15)
        axis.axhline(0, color="#555", linewidth=.6)
        axis.set(ylabel="Delta Q (Ah)", title=f"{DISPLAY[batch]}: cycle 100 - cycle 10")
        axis.legend(fontsize=8)
    axes[-1].set_xlabel("Voltage (V)")
    save(fig, "03_delta_q_curves.png")
    fig, axes = plt.subplots(1, len(order), figsize=(15.5, 4.6), sharex=True)
    axes = np.atleast_1d(axes)
    for axis, batch in zip(axes, order):
        sub = cells[(cells.batch == batch) & cells.cycle_life.notna()].sort_values("cycle_life")
        groups = (("shorter third", sub.iloc[:max(1, len(sub)//3)], "#c25151"),
                  ("longer third", sub.iloc[-max(1, len(sub)//3):], "#167364"))
        for label, group, color in groups:
            stack = np.vstack([curves[f"{cid}_dq"] for cid in group.cell_id])
            voltage = curves[f"{group.cell_id.iloc[0]}_voltage"]
            axis.plot(voltage, np.median(stack, axis=0), color=color,
                      linewidth=2, label=f"{label} (n={len(group)})")
            axis.fill_between(voltage, np.quantile(stack, .25, axis=0),
                              np.quantile(stack, .75, axis=0), color=color, alpha=.14)
        axis.axhline(0, color="#777", lw=.7)
        axis.set(title=DISPLAY[batch], xlabel="Voltage (V)")
        axis.legend(fontsize=8, loc="lower right", frameon=False)
    axes[0].set_ylabel("Delta Q(V), Ah")
    fig.suptitle("Discharge-curve change from cycle 10 to 100", fontsize=15)
    save(fig, "10_delta_q_landscape.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for batch in order:
        sub = cells[cells.batch == batch]
        ax.scatter(sub.log10_dq_var, sub.cycle_life, label=DISPLAY[batch], color=PALETTE[batch],
                   alpha=.75, s=35, edgecolors="white", linewidths=.4)
    ax.set(xlabel="log10 variance of Delta Q(V)", ylabel="Cycle life",
           title="Early discharge-curve change vs lifetime")
    ax.legend()
    save(fig, "04_delta_q_life.png")

    # Q4: charging policy, parsed as a two-stage current, with sample sizes.
    policy = cells.groupby(["batch", "policy"], as_index=False).agg(
        n=("cell_id", "count"), n_labeled=("cycle_life", "count"),
        life_mean=("cycle_life", "mean"),
        life_sd=("cycle_life", "std"), c_rate_1=("c_rate_1", "first"),
        switch_pct=("switch_pct", "first"), c_rate_2=("c_rate_2", "first"))
    policy.to_csv(TABLES / "policy_summary.csv", index=False)
    family = cells.groupby(["batch", "protocol_family"], as_index=False).agg(
        n_cells=("cell_id", "size"), n_labeled=("cycle_life", "count"),
        life_median=("cycle_life", "median"), life_min=("cycle_life", "min"),
        life_max=("cycle_life", "max"), log10_dq_var_median=("log10_dq_var", "median"))
    family.to_csv(TABLES / "protocol_family_summary.csv", index=False)
    shift_features = [
        "log10_dq_var", "qd_10", "qd_change_10_100",
        "early_charge_mean", "early_tavg_mean", "ir_change_10_100",
    ]
    feature_shift = cells[cells.cycle_life.notna()].groupby("batch")[shift_features].agg(
        ["min", "median", "max"])
    feature_shift.columns = [f"{feature}_{stat}" for feature, stat in feature_shift.columns]
    feature_shift.to_csv(TABLES / "batch_feature_shift.csv")
    fig, axes = plt.subplots(1, len(order), figsize=(5.2 * len(order), 4), sharey=True)
    axes = np.atleast_1d(axes)
    for axis, batch in zip(axes, order):
        sub = cells[cells.batch == batch]
        axis.scatter(sub.c_rate_1, sub.cycle_life, s=25 + sub.switch_pct * .7,
                     alpha=.65, color=PALETTE[batch], edgecolors="white", linewidths=.4)
        axis.set(xlabel="First-stage C-rate", title=f"{DISPLAY[batch]} (size = switch %)")
        axis.grid(alpha=.15)
    axes[0].set_ylabel("Cycle life")
    save(fig, "05_policy_vs_life.png")
    if "batch2_notion" in order:
        b2 = cells[(cells.batch == "batch2_notion") & cells.cycle_life.notna()].copy()
        b2["base_policy"] = b2.policy.str.replace("-newstructure", "", regex=False)
        matched = b2.groupby(["base_policy", "protocol_family"], as_index=False).agg(
            n=("cell_id", "size"), mean_life=("cycle_life", "mean"),
            median_life=("cycle_life", "median"))
        matched.to_csv(TABLES / "batch2_matched_policies.csv", index=False)
        shared = [name for name, group in b2.groupby("base_policy")
                  if set(group.protocol_family) == {"standard", "newstructure"}]
        fig, ax = plt.subplots(figsize=(9, 4.2))
        for pos, name in enumerate(shared):
            for family_name, offset, color in (("standard", -.13, "#c07822"),
                                                ("newstructure", .13, "#247868")):
                group = b2[(b2.base_policy == name) & (b2.protocol_family == family_name)]
                ax.scatter(np.full(len(group), pos + offset), group.cycle_life,
                           color=color, alpha=.72, s=37)
                ax.scatter(pos + offset, group.cycle_life.mean(), color=color,
                           marker="_", s=420, linewidths=2.5)
        ax.set_xticks(range(len(shared)), shared)
        ax.set(ylabel="Cycle life", title="Batch 2: same base C-rate, different protocol family")
        ax.grid(axis="y", alpha=.2)
        from matplotlib.lines import Line2D
        ax.legend(handles=[Line2D([0], [0], marker="o", color="w", markerfacecolor="#c07822", label="standard", markersize=8),
                           Line2D([0], [0], marker="o", color="w", markerfacecolor="#247868", label="newstructure", markersize=8)],
                  loc="upper left")
        save(fig, "08_batch2_matched_policies.png")

    # Q5: cell-level correlations and bootstrap uncertainty by batch.
    correlations = []
    for batch in order:
        sub = cells[cells.batch == batch]
        for feature in FEATURES:
            correlations.append({"batch": batch, "feature": feature,
                                 **bootstrap_spearman(sub, feature)})
    corr = pd.DataFrame(correlations)
    corr.to_csv(TABLES / "feature_correlations.csv", index=False)
    endpoint_sensitivity = []
    for batch in order:
        sub = cells[cells.batch == batch]
        for group_name, part in (("all_recorded_labels", sub),
                                 ("near_eol_only", sub[sub.near_eol_088])):
            for feature in ("log10_dq_var", "dq_mean", "qd_10", "c_rate_1"):
                estimate = bootstrap_spearman(part, feature)
                endpoint_sensitivity.append({"batch": batch, "endpoint_group": group_name,
                                             "feature": feature, **estimate})
    pd.DataFrame(endpoint_sensitivity).to_csv(
        TABLES / "endpoint_sensitivity.csv", index=False)
    policy_uncertainty = []
    for batch in order:
        labeled = cells[(cells.batch == batch) & cells.cycle_life.notna()]
        for endpoint_group, sub in (
            ("all_recorded_labels", labeled),
            ("near_eol_only", labeled[labeled.near_eol_088]),
        ):
            for centered in (False, True):
                policy_uncertainty.append({
                    "batch": batch, "endpoint_group": endpoint_group,
                    "policy_centered": centered,
                    **policy_bootstrap(sub, "log10_dq_var", centered),
                })
    pd.DataFrame(policy_uncertainty).to_csv(
        TABLES / "policy_cluster_bootstrap.csv", index=False)
    pivot = corr.pivot(index="feature", columns="batch", values="rho")[order]
    pivot.columns = [DISPLAY[batch] for batch in order]
    fig, ax = plt.subplots(figsize=(3 + 2.2 * len(order), 6))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, ax=ax, cbar_kws={"label": "Spearman rho"})
    ax.set(title="Early-cycle features vs cycle life")
    save(fig, "06_feature_correlations.png")

    # Protocol-centered association asks whether a feature separates cells
    # within the same charging policy, rather than only between policies.
    within_rows = []
    fig, axes = plt.subplots(1, len(order), figsize=(5.2 * len(order), 4), sharey=True)
    axes = np.atleast_1d(axes)
    for axis, batch in zip(axes, order):
        sub = cells[(cells.batch == batch) & cells.cycle_life.notna()].copy()
        stats[batch]["first_c_rate_life_rho"] = float(
            spearmanr(sub.c_rate_1, sub.cycle_life).statistic)
        stats[batch]["singleton_policies"] = int((sub.policy.value_counts() == 1).sum())
        for feature in ("log10_dq_var", "dq_mean", "early_charge_mean",
                        "early_tavg_mean", "qd_100"):
            x = sub[feature] - sub.groupby("policy")[feature].transform("mean")
            y = sub.cycle_life - sub.groupby("policy").cycle_life.transform("mean")
            mask = x.notna() & y.notna()
            rho = spearmanr(x[mask], y[mask]).statistic if mask.sum() >= 8 else np.nan
            within_rows.append({"batch": batch, "feature": feature,
                                "n_cells": int(mask.sum()),
                                "n_policies": int(sub.policy.nunique()),
                                "within_policy_rho": float(rho)})
            if feature == "log10_dq_var":
                axis.scatter(x[mask], y[mask], color=PALETTE[batch],
                             alpha=.65, s=30, edgecolors="white", linewidths=.4)
                stats[batch]["within_policy_dq_rho"] = float(rho)
        axis.axhline(0, color="#777", linewidth=.6)
        axis.axvline(0, color="#777", linewidth=.6)
        axis.set(xlabel="log10 variance of Delta Q minus policy mean",
                 title=f"{DISPLAY[batch]}: within-policy comparison")
    axes[0].set_ylabel("Cycle life minus policy mean")
    save(fig, "07_within_policy.png")
    pd.DataFrame(within_rows).to_csv(TABLES / "within_policy_correlations.csv", index=False)
    cells[cells.batch == "batch1"][[
        "dq_var", "dq_mean", "dq_min", "early_tavg_mean",
        "early_tmax_mean", "early_charge_mean"
    ]].corr(method="spearman").to_csv(TABLES / "batch1_feature_redundancy.csv")

    # Sample- and protocol-level shift is a design risk, not merely a plot.
    overlap = {}
    for left in order:
        for right in order:
            if left >= right:
                continue
            a = cells[(cells.batch == left) & cells.cycle_life.notna()]
            b = cells[(cells.batch == right) & cells.cycle_life.notna()]
            overlap[f"{left}__{right}"] = {
                "shared_policy_count": len(set(a.policy) & set(b.policy)),
                "ks_life_statistic": float(ks_2samp(
                    a.cycle_life.dropna().to_numpy(),
                    b.cycle_life.dropna().to_numpy()).statistic),
                "mean_life_gap": float(b.cycle_life.mean() - a.cycle_life.mean()),
            }
    with (TABLES / "eda_summary.json").open("w", encoding="utf-8") as output:
        json.dump({"batches": stats, "batch_shift": overlap},
                  output, ensure_ascii=False, indent=2)
    print(json.dumps({"batches": stats, "batch_shift": overlap},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
