"""Focused DAY 1 checks requested after review; descriptive analysis only.

The early-capacity slope is an observed 20-100 cycle QD trend, not a
measurement of irreversible degradation. Negative values mean QD rose.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, theilslopes

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"
BATCHES = ["batch1", "batch2_notion", "batch3"]
BLUE, AMBER, PURPLE = "#27679a", "#c17a29", "#83539a"
TEAL, RED, INK, GRID = "#1d806f", "#bd5860", "#253748", "#d7e0e6"
COLORS = dict(zip(BATCHES, (BLUE, AMBER, PURPLE)))


def setup():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.labelcolor": INK, "text.color": INK,
        "axes.edgecolor": GRID, "xtick.color": INK, "ytick.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def rho(frame, x, y):
    part = frame[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(part) < 4 or part[x].nunique() < 3 or part[y].nunique() < 3:
        return np.nan
    return float(spearmanr(part[x], part[y]).statistic)


def main():
    setup()
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    cells = pd.read_csv(DATA / "cells.csv")
    cycles = pd.read_csv(DATA / "cycles.csv")
    curves = np.load(DATA / "dq_curves.npz")
    parsed = cells.policy.str.extract(
        r"^(\d+(?:\.\d+)?)C\((\d+)%\)-(\d+(?:\.\d+)?)C"
    ).astype(float)
    parsed.columns = ["first_c_rate", "switch_soc_pct", "second_c_rate"]
    cells = pd.concat([cells, parsed], axis=1)

    # A smoothed 20-100 trend avoids using one potentially noisy endpoint.
    slopes = []
    for cell_id, group in cycles.groupby("cell_id", sort=False):
        part = group.loc[group.cycle.between(20, 100) &
                         group.QD.between(.5, 2), ["cycle", "QD"]].dropna()
        if len(part) < 60:
            raise ValueError(f"Too few valid early QD observations: {cell_id}")
        gradient = np.polyfit(part.cycle.to_numpy(), part.QD.to_numpy(), 1)[0]
        robust_gradient = theilslopes(part.QD.to_numpy(),
                                     part.cycle.to_numpy())[0]
        slopes.append({"cell_id": cell_id,
                       "early_qd_loss_per_100_cycles": -100 * gradient,
                       "early_qd_loss_robust_per_100_cycles": -100 * robust_gradient,
                       "n_early_qd": len(part)})
    cells = cells.merge(pd.DataFrame(slopes), on="cell_id", validate="one_to_one")
    cells.to_csv(DATA / "revised_cell_metrics.csv", index=False)
    labeled = cells.loc[cells.cycle_life.notna()].copy()

    assoc = []
    for batch, group in labeled.groupby("batch", sort=False):
        for predictor in ("first_c_rate", "switch_soc_pct", "second_c_rate"):
            for outcome in ("early_qd_loss_per_100_cycles",
                            "early_qd_loss_robust_per_100_cycles", "log10_dq_var",
                            "cycle_life"):
                assoc.append({"batch": batch, "predictor": predictor,
                              "outcome": outcome, "n": len(group),
                              "spearman_rho": rho(group, predictor, outcome)})
    pd.DataFrame(assoc).to_csv(TAB / "charging_early_degradation_associations.csv",
                                index=False)

    b2 = labeled.loc[labeled.batch == "batch2_notion"].copy()
    b2["base_policy"] = b2.policy.str.replace("-newstructure", "", regex=False)
    family = b2.groupby("protocol_family").agg(
        n=("cell_id", "size"), life_median=("cycle_life", "median"),
        early_qd_loss_median=("early_qd_loss_per_100_cycles", "median"),
        early_qd_loss_robust_median=("early_qd_loss_robust_per_100_cycles", "median"),
        log10_dq_var_median=("log10_dq_var", "median"),
        qd_change_10_100_median=("qd_change_10_100", "median"))
    family.to_csv(TAB / "batch2_family_early_metrics.csv")
    matched = b2.groupby(["base_policy", "protocol_family"]).agg(
        n=("cell_id", "size"), life_mean=("cycle_life", "mean"),
        early_qd_loss_mean=("early_qd_loss_per_100_cycles", "mean"),
        early_qd_loss_robust_mean=("early_qd_loss_robust_per_100_cycles", "mean"),
        log10_dq_var_mean=("log10_dq_var", "mean")).reset_index()
    matched = matched[matched.base_policy.isin(
        matched.groupby("base_policy").protocol_family.nunique().loc[lambda x: x == 2].index)]
    matched.to_csv(TAB / "batch2_matched_early_metrics.csv", index=False)

    # 1. Actual lifetime split, with individual cells visible.
    fig, ax = plt.subplots(figsize=(11, 4.0))
    groups = [("Batch 1", labeled[labeled.batch == "batch1"], BLUE),
              ("Batch 2 / standard", b2[b2.protocol_family == "standard"], AMBER),
              ("Batch 2 / newstructure", b2[b2.protocol_family == "newstructure"], TEAL),
              ("Batch 3", labeled[labeled.batch == "batch3"], PURPLE)]
    rng = np.random.default_rng(20261001)
    for i, (name, group, color) in enumerate(groups):
        jitter = rng.uniform(-.13, .13, len(group))
        ax.scatter(i + jitter, group.cycle_life, s=38, color=color,
                   alpha=.7, edgecolor="white", linewidth=.4, zorder=2)
        med = group.cycle_life.median()
        ax.plot([i-.24, i+.24], [med, med], lw=3.2, color=INK, zorder=3)
        ax.text(i, med+35, f"median {med:.0f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold")
    ax.axhline(534, color=RED, lw=1.4, ls="--")
    ax.text(3.43, 550, "Batch 1 minimum = 534", color=RED, ha="right", fontsize=10)
    ax.set(xticks=range(4), xticklabels=[x[0] for x in groups],
           ylabel="Recorded cycle-life label", ylim=(310, 2080))
    ax.grid(axis="y", alpha=.28)
    fig.tight_layout()
    save(fig, "r01_life_groups.png")

    # 2. Matched charging strings: life and the early curve marker move together,
    # but the observed capacity slope moves in the opposite direction.
    names = list(matched.base_policy.drop_duplicates())
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.1))
    metrics = [
        ("life_mean", "Cycle life", "+", 0),
        ("log10_dq_var_mean", "log10 var of Delta Q(V)", "", 2),
        ("early_qd_loss_mean", "20-100 QD loss (Ah / 100 cycles)", "", 4),
    ]
    for ax, (metric, ylabel, _, decimals) in zip(axes, metrics):
        for j, name in enumerate(names):
            part = matched[matched.base_policy == name].set_index("protocol_family")
            if len(part) != 2:
                continue
            standard = part.loc["standard", metric]
            new = part.loc["newstructure", metric]
            ax.plot([j-.16, j+.16], [standard, new], color=GRID, lw=2, zorder=1)
            ax.scatter(j-.16, standard, color=AMBER, s=70, zorder=3)
            ax.scatter(j+.16, new, color=TEAL, s=70, zorder=3)
            if metric == "life_mean":
                ax.text(j, max(standard, new)+34, f"+{new-standard:.0f}",
                        color=TEAL, ha="center", fontsize=9, fontweight="bold")
        ax.set(xticks=range(len(names)), xticklabels=["4.8C / 80%", "5.2C / 58%", "5.6C / 26%"],
               ylabel=ylabel)
        ax.grid(axis="y", alpha=.25)
        if metric == "early_qd_loss_mean":
            ax.axhline(0, color=RED, lw=1, ls="--")
    axes[0].scatter([], [], color=AMBER, s=55, label="standard")
    axes[0].scatter([], [], color=TEAL, s=55, label="newstructure")
    axes[0].legend(loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout(w_pad=2.4)
    save(fig, "r02_matched_three_metrics.png")

    # 3. Show the early and full-life QD trajectory evidence in Batch 2.
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.15))
    early_series = {}
    for family_name, color in (("standard", AMBER), ("newstructure", TEAL)):
        ids = set(b2.loc[b2.protocol_family == family_name, "cell_id"])
        all_series = []
        for cell_id, group in cycles[cycles.cell_id.isin(ids)].groupby("cell_id"):
            sub = group[group.cycle.between(20, 100)].copy()
            q20 = sub.iloc[(sub.cycle-20).abs().argmin()].QD
            sub["relative_mAh"] = 1000*(sub.QD-q20)
            all_series.append(sub[["cycle", "relative_mAh"]])
            full = group[group.cycle >= 20].sort_values("cycle")
            axes[1].plot(full.cycle, full.QD.rolling(9, min_periods=1).median(),
                         color=color, alpha=.23, lw=1.0)
        stack = pd.concat(all_series)
        grouped = stack.groupby("cycle").relative_mAh
        med = grouped.median()
        lo = grouped.quantile(.25).reindex(med.index)
        hi = grouped.quantile(.75).reindex(med.index)
        axes[0].plot(med.index, med.values, color=color, lw=3,
                     label=f"{family_name} (n={len(ids)})")
        axes[0].fill_between(med.index, lo.values, hi.values,
                             color=color, alpha=.15)
        early_series[family_name] = med
    axes[0].axhline(0, color=GRID, lw=1)
    axes[0].set(xlabel="Cycle", ylabel="QD minus cycle-20 QD (mAh)",
                xlim=(20, 100), ylim=(-22, 13))
    axes[0].legend(frameon=False, fontsize=10)
    axes[1].axhline(.88, color=RED, ls="--", lw=1.3)
    axes[1].text(610, .887, "0.88 Ah threshold", color=RED, fontsize=9)
    axes[1].set(xlabel="Cycle (full record; diagnostic only)",
                ylabel="Discharge capacity QD (Ah)", xlim=(20, 1220), ylim=(.81, 1.13))
    for ax in axes:
        ax.grid(alpha=.23)
    fig.tight_layout(w_pad=2.5)
    save(fig, "r03_batch2_capacity_trajectories.png")

    # 4. Scalar capacity change loses its lifetime signal in the later batches.
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.1), sharey=True)
    for ax, batch in zip(axes, BATCHES):
        group = labeled[labeled.batch == batch]
        color = COLORS[batch]
        ax.scatter(group.qd_change_10_100*1000, group.cycle_life, color=color,
                   alpha=.78, s=45, edgecolor="white", lw=.5)
        ax.text(.04, .96, f"rho = {rho(group, 'qd_change_10_100', 'cycle_life'):+.2f}",
                transform=ax.transAxes, va="top", color=color, fontsize=14,
                fontweight="bold")
        ax.axvline(0, color=GRID, lw=1)
        ax.set(title=batch.replace("batch", "Batch ").replace("_notion", ""),
               xlabel="QD100 - QD10 (mAh)")
        ax.grid(alpha=.22)
    axes[0].set_ylabel("Recorded cycle life")
    fig.tight_layout(w_pad=2.1)
    save(fig, "r04_scalar_qd_instability.png")

    # 5. Voltage-resolved curves, with a visibly marked comparison interval.
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.2), sharey=True)
    for ax, batch in zip(axes, BATCHES):
        group = labeled[labeled.batch == batch].sort_values("cycle_life")
        k = max(1, len(group)//3)
        for title, part, color in (("shortest third", group.iloc[:k], RED),
                                   ("longest third", group.iloc[-k:], TEAL)):
            stack = np.vstack([curves[f"{cid}_dq"] for cid in part.cell_id])
            voltage = curves[f"{part.cell_id.iloc[0]}_voltage"]
            ax.plot(voltage, np.median(stack, axis=0), color=color, lw=2.2,
                    label=title)
            ax.fill_between(voltage, np.quantile(stack,.25,axis=0),
                            np.quantile(stack,.75,axis=0), color=color, alpha=.13)
        ax.axvspan(2.8, 3.1, color="#f7d788", alpha=.26)
        ax.axhline(0, color=GRID, lw=.9)
        ax.set(title=batch.replace("batch", "Batch ").replace("_notion", ""),
               xlabel="Discharge voltage (V)")
        ax.grid(alpha=.18)
    axes[0].set_ylabel("Delta Q(V) = QD100(V) - QD10(V), Ah")
    axes[0].legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout(w_pad=2)
    save(fig, "r05_delta_q_shape.png")

    # 6. A pooled correlation is not a within-policy association.
    conditional = []
    for batch, group in labeled.groupby("batch", sort=False):
        centered = group.copy()
        for col in ("log10_dq_var", "cycle_life"):
            centered[col] = group[col]-group.groupby("policy")[col].transform("mean")
        conditional.append({"group": batch, "n": len(group),
                            "pooled_rho": rho(group, "log10_dq_var", "cycle_life"),
                            "policy_centered_rho": rho(centered, "log10_dq_var", "cycle_life")})
    for family_name, group in b2.groupby("protocol_family"):
        conditional.append({"group": "batch2_"+family_name, "n": len(group),
                            "pooled_rho": rho(group, "log10_dq_var", "cycle_life"),
                            "policy_centered_rho": np.nan})
    pd.DataFrame(conditional).to_csv(TAB / "dq_conditional_correlations.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.2), gridspec_kw={"width_ratios": [1.05, 1]})
    for family_name, color in (("standard", AMBER), ("newstructure", TEAL)):
        group = b2[b2.protocol_family == family_name]
        axes[0].scatter(group.log10_dq_var, group.cycle_life, s=55,
                        alpha=.78, color=color, edgecolor="white", lw=.5,
                        label=f"{family_name}: n={len(group)}, rho={rho(group,'log10_dq_var','cycle_life'):+.2f}")
    axes[0].set(xlabel="log10 var of Delta Q(V)", ylabel="Cycle life")
    axes[0].legend(frameon=False, loc="upper right", fontsize=9)
    axes[0].grid(alpha=.22)
    x = np.arange(3)
    table = pd.DataFrame(conditional).set_index("group")
    axes[1].bar(x-.18, table.loc[BATCHES, "pooled_rho"], width=.35,
                color=[BLUE, AMBER, PURPLE], alpha=.93, label="all cells")
    axes[1].bar(x+.18, table.loc[BATCHES, "policy_centered_rho"], width=.35,
                color=[BLUE, AMBER, PURPLE], alpha=.34, edgecolor=INK,
                label="within policy")
    axes[1].axhline(0, color=GRID, lw=1)
    axes[1].set(xticks=x, xticklabels=["Batch 1", "Batch 2", "Batch 3"],
                ylabel="Spearman rho: Delta Q variance vs life", ylim=(-1,.12))
    axes[1].legend(frameon=False, fontsize=9, loc="upper right")
    axes[1].grid(axis="y", alpha=.22)
    fig.tight_layout(w_pad=2.3)
    save(fig, "r06_dq_conditional.png")

    # 7. Charging program vs observed initial QD trend, with the shape marker
    # correlation shown in each panel as an alternative early-change measure.
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.1), sharey=True)
    for ax, batch in zip(axes, BATCHES):
        group = labeled[labeled.batch == batch]
        if batch == "batch2_notion":
            for family_name, color in (("standard", AMBER), ("newstructure", TEAL)):
                part = group[group.protocol_family == family_name]
                ax.scatter(part.first_c_rate, part.early_qd_loss_per_100_cycles*1000,
                           s=48, color=color, alpha=.78, edgecolor="white", lw=.5,
                           label=family_name)
            ax.legend(frameon=False, fontsize=9, loc="upper right")
        else:
            ax.scatter(group.first_c_rate, group.early_qd_loss_per_100_cycles*1000,
                       s=48, color=COLORS[batch], alpha=.76,
                       edgecolor="white", lw=.5)
        rr = rho(group, "first_c_rate", "early_qd_loss_per_100_cycles")
        vv = rho(group, "first_c_rate", "log10_dq_var")
        ax.text(.04, .97, f"QD slope rho {rr:+.2f}\nDelta Q var rho {vv:+.2f}",
                transform=ax.transAxes, va="top", color=INK, fontsize=10,
                bbox=dict(facecolor="white", edgecolor="none", alpha=.82))
        ax.axhline(0, color=RED, lw=1, ls="--")
        ax.set(title=batch.replace("batch", "Batch ").replace("_notion", ""),
               xlabel="First-stage C-rate")
        ax.grid(alpha=.22)
    axes[0].set_ylabel("Observed QD loss, cycles 20-100 (mAh / 100 cycles)")
    fig.tight_layout(w_pad=2.1)
    save(fig, "r07_charge_vs_early_change.png")

    print("Revised DAY 1 figures and tables written.")
    print(pd.DataFrame(assoc).query(
        "predictor == 'first_c_rate' and outcome != 'cycle_life'").to_string(index=False))
    print(family.to_string())


if __name__ == "__main__":
    main()
