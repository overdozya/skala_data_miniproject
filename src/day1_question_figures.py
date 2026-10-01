"""Present existing DAY 1 evidence in the order of the assignment questions.

Reads the verified aggregates/cell features; does not fit prediction models.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from day1_final_analysis import ROOT, OUT, F, T, setup, save, INK, TEAL, COL, GRID


def main():
    setup()
    cor = pd.read_csv(T/'feature_life_correlations.csv')
    values = cor[['B1 전체', 'B2', 'B3']].to_numpy()
    fig, ax = plt.subplots(figsize=(7.3, 4.7))
    im = ax.imshow(values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    for i in range(len(cor)):
        for j in range(3):
            v = values[i, j]
            ax.text(j, i, f'{v:+.2f}', ha='center', va='center', fontsize=12,
                    color='white' if abs(v)>.65 else INK,
                    fontweight='bold' if i>=7 else 'normal')
    ax.set(xticks=range(3), xticklabels=['B1 · 46셀', 'B2 · 39셀', 'B3 · 44셀'],
           yticks=range(len(cor)), yticklabels=cor.label)
    ax.axhline(6.5, color='white', lw=3)
    fig.colorbar(im, ax=ax, pad=.03, shrink=.85, label='Spearman ρ')
    save(fig, 'question_feature_correlations')

    evidence = json.loads((OUT/'analysis.json').read_text())
    pairs = [('log 분산 ↔ ΔQ 평균', evidence['primary_redundancy_dq_mean']),
             ('log 분산 ↔ ΔQ 최솟값', evidence['primary_redundancy_dq_min']),
             ('첫 C-rate ↔ 전환 SOC', evidence['primary_redundancy_rate_soc'])]
    fig, ax = plt.subplots(figsize=(7.1, 3.3))
    for i, (label, value) in enumerate(pairs):
        color = TEAL if i<2 else COL['batch1']
        ax.plot([0, value], [i, i], color=color, lw=6, alpha=.6)
        ax.scatter(value, i, s=105, color=color, zorder=3)
        ax.text(value+.035, i-.17, f'{value:+.2f}', fontsize=14,
                fontweight='bold', color=color)
    ax.set(xlim=(-1.08, .04), ylim=(2.5, -.6), yticks=range(3),
           yticklabels=[p[0] for p in pairs], xticks=[-1,-.75,-.5,-.25,0],
           xlabel='Spearman 상관')
    ax.axvline(0, color=GRID);ax.grid(axis='x', alpha=.18)
    save(fig, 'question_feature_redundancy')

    cells = pd.read_csv(ROOT/'data/processed/final_cell_metrics.csv')
    p = cells[(cells.batch=='batch1') & cells.near_eol_088]
    fig, axs = plt.subplots(1, 2, figsize=(8.7, 3.65), sharey=True)
    for ax, x, title, label in [
        (axs[0], p.dq_var*1e6, '원래 분산', 'ΔQ 분산 (mAh²)'),
        (axs[1], p.log10_dq_var, '로그로 압축한 분산', 'log10 var(ΔQ) · Ah² 기준')]:
        ax.scatter(x, p.cycle_life, color=COL['batch1'], s=32, alpha=.85)
        ax.set(title=title, xlabel=label, ylim=(500,1110));ax.grid(alpha=.18)
    axs[0].set_ylabel('기록 수명 (사이클)')
    save(fig, 'question_input_transform')
    # Compare the two inputs with the most B2 range departures, using the
    # actual fixed training pool. The four-feature union is reported in the PDF.
    split = pd.read_csv(ROOT/'data/processed/planned_day2_split.csv').merge(
        cells, on=['cell_id','policy'], validate='one_to_one')
    train = split[split.role=='train_cv']
    b2 = cells[(cells.batch=='batch2_notion') & cells.cycle_life.notna()]
    groups = [('B1 학습 · 28', train, COL['batch1']),
              ('B2 standard · 30', b2[b2.protocol_family=='standard'], COL['batch2_notion']),
              ('B2 new · 9', b2[b2.protocol_family=='newstructure'], TEAL)]
    fig, axs = plt.subplots(1, 2, figsize=(8.8, 3.7), sharey=True)
    rng = np.random.default_rng(20261001)
    offsets = [rng.uniform(-.13,.13,len(g)) for _,g,_ in groups]
    for ax, feature, title, xlabel in [
        (axs[0], 'log10_dq_var', 'ΔQ 분산 · 범위 밖 18셀', 'log10 var(ΔQ)'),
        (axs[1], 'second_c_rate', '둘째 C-rate · 범위 밖 25셀', '둘째 C-rate (C)')]:
        ax.axvspan(train[feature].min(), train[feature].max(), color='#E4EEF5')
        for i, ((_,g,color), offset) in enumerate(zip(groups, offsets)):
            ax.scatter(g[feature], i+offset, color=color, s=34, alpha=.85)
        ax.set(title=title, xlabel=xlabel, yticks=range(3),
               yticklabels=[label for label,_,_ in groups], ylim=(2.5,-.5))
        ax.tick_params(axis='both', labelsize=11)
        ax.grid(axis='x',alpha=.15)
    axs[1].axvline(4.4, color=COL['batch1'], ls=':', lw=1)
    axs[1].text(4.4,2.42,'학습 상한 4.4',ha='center',va='bottom',fontsize=10,color=COL['batch1'])
    save(fig, 'question_selected_input_support')
    print('Created four presentation figures from existing DAY 1 evidence.')


if __name__=='__main__':
    main()
