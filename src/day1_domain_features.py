"""Domain-informed policy representations for DAY 1; no prediction fitting.

The two CC steps span 0-80% SOC. Durations use nominal capacity/C-rate,
excluding the common 80-100% CC-CV stage, diagnostic pulses and rests.
Public tables contain group summaries; cell-level features stay ignored.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from day1_final_analysis import ROOT, OUT, T, COL, INK, setup, save, rho

RAW_POLICY = ['first_c_rate', 'second_c_rate', 'switch_soc_pct']
DOMAIN_POLICY = ['nominal_avg_c', 'max_c']


def main():
    setup()
    m = pd.read_csv(ROOT/'data/processed/final_cell_metrics.csv')
    valid = m[RAW_POLICY].notna().all(axis=1)
    assert m.loc[valid, 'switch_soc_pct'].between(0, 80).all()
    assert (m.loc[valid, ['first_c_rate', 'second_c_rate']] > 0).all().all()
    s = m.switch_soc_pct / 100
    m['nominal_time80_min'] = 60 * (s/m.first_c_rate + (0.8-s)/m.second_c_rate)
    m['nominal_avg_c'] = 48 / m.nominal_time80_min
    # Ignore a zero-length stage when describing the active current maximum.
    m['max_c'] = np.maximum(np.where(s > 0, m.first_c_rate, -np.inf),
                           np.where(s < .8, m.second_c_rate, -np.inf))
    m.loc[~valid, ['nominal_time80_min', 'nominal_avg_c', 'max_c']] = np.nan
    m.to_csv(ROOT/'data/processed/domain_cell_metrics.csv', index=False)
    labeled = m[m.cycle_life.notna() & valid].copy()
    primary = labeled[(labeled.batch=='batch1') & labeled.near_eol_088]
    b2 = labeled[labeled.batch=='batch2_notion']
    b3 = labeled[labeled.batch=='batch3']
    cohorts = [('B1 all 46', labeled[labeled.batch=='batch1']),
               ('B1 near EOL 36', primary), ('B2 all 39', b2),
               ('B2 standard 30', b2[b2.protocol_family=='standard']),
               ('B2 newstructure 9', b2[b2.protocol_family=='newstructure']),
               ('B3 44', b3)]
    rows = []
    for name, g in cohorts:
        for f in ['first_c_rate', 'second_c_rate', 'nominal_avg_c', 'max_c']:
            span = float(g[f].max()-g[f].min())
            # Tiny nominal differences in the ~10 min batches reflect printed
            # policy precision, not a useful range of charging speeds.
            interpretable = not (f=='nominal_avg_c' and span < .05)
            for target in ['cycle_life', 'log10_dq_var', 'early_qd_loss_robust_per_100_cycles']:
                rows.append(dict(cohort=name, n=len(g), policies=g.policy.nunique(),
                    feature=f, minimum=g[f].min(), maximum=g[f].max(),
                    target=target, spearman_rho=rho(g, f, target),
                    interpretable_range=interpretable))
    pd.DataFrame(rows).to_csv(T/'domain_feature_associations.csv', index=False)
    policy = pd.concat([g.assign(cohort=name) for name,g in cohorts]).groupby(
        ['cohort', 'batch', 'policy', 'protocol_family']).agg(
        n=('cell_id','size'), mean_life=('cycle_life','mean'),
        min_life=('cycle_life','min'), max_life=('cycle_life','max'),
        nominal_time80_min=('nominal_time80_min','first'),
        nominal_avg_c=('nominal_avg_c','first'), max_c=('max_c','first')).reset_index()
    policy.to_csv(T/'domain_policy_summary.csv', index=False)

    # Policy mean/range charts retain the assignment's policy-level comparison.
    fig, axs = plt.subplots(1, 2, figsize=(11.8, 3.2))
    for ax, name, cells, feat, title, xlabel, color in [
        (axs[0], 'B1 near EOL 36', primary, 'nominal_avg_c',
         'B1 · 36셀 / 20정책', '0-80% 명목 평균 C-rate (C)', COL['batch1']),
        (axs[1], 'B3 44', b3, 'max_c',
         'B3 · 44셀 / 8정책 · 명목 충전 9.97-10.01분', '최대 C-rate (C)', COL['batch3'])]:
        g = policy[policy.cohort==name]
        ax.errorbar(g[feat], g.mean_life,
                    yerr=[g.mean_life-g.min_life, g.max_life-g.mean_life],
                    fmt='o', ms=6, capsize=3, color=color, alpha=.8)
        ax.text(.04,.95,f'셀 기준 수명 상관 ρ={rho(cells,feat):+.2f}',
                transform=ax.transAxes, va='top', fontsize=12, color=color,
                fontweight='bold')
        ax.set(title=title, xlabel=xlabel)
        ax.grid(alpha=.18)
    axs[0].set(ylabel='정책별 평균 수명 (사이클)', ylim=(480,1160))
    axs[1].set(ylim=(450,2080))
    save(fig, 'domain_charging_policy')

    split = pd.read_csv(ROOT/'data/processed/planned_day2_split.csv').merge(
        m, on=['cell_id','policy'], validate='one_to_one')
    train = split[split.role=='train_cv']
    representations = {'raw_policy_3': RAW_POLICY, 'domain_policy_2': DOMAIN_POLICY,
                       'raw_plus_dq_4': ['log10_dq_var']+RAW_POLICY,
                       'domain_plus_dq_3': ['log10_dq_var']+DOMAIN_POLICY}
    support = []
    for batch, g in [('B2',b2),('B3',b3)]:
        for rep, features in representations.items():
            flags = pd.DataFrame({f:~g[f].between(train[f].min(),train[f].max()) for f in features})
            for feature in features+['any']:
                flag = flags.any(axis=1) if feature=='any' else flags[feature]
                support.append(dict(batch=batch, representation=rep, feature=feature,
                    n=len(g), outside=int(flag.sum()),
                    train_min=np.nan if feature=='any' else train[feature].min(),
                    train_max=np.nan if feature=='any' else train[feature].max()))
    pd.DataFrame(support).to_csv(T/'domain_input_support.csv', index=False)
    out = dict(formula='t80_h = s/C1 + (0.8-s)/C2; Cavg=0.8/t80_h; Cmax=max(active C1,C2)',
               interpretation='Nominal 0-80% CC duration, not measured total charge time or degradation dose.',
               b1_n=len(primary), b3_n=len(b3),
               b1_average_life_rho=rho(primary,'nominal_avg_c'),
               b1_average_dq_rho=rho(primary,'nominal_avg_c','log10_dq_var'),
               b3_maximum_life_rho=rho(b3,'max_c'),
               b3_maximum_dq_rho=rho(b3,'max_c','log10_dq_var'))
    (OUT/'domain_analysis.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False))


if __name__=='__main__':
    main()
