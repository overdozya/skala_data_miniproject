"""Close the self-review findings with descriptive checks only (no predictor fit)."""
from pathlib import Path
import json
import h5py
import numpy as np
import pandas as pd
from scipy.stats import theilslopes, skew, spearmanr
import matplotlib.pyplot as plt
from day1_final_analysis import setup, save, raw, rho, ROOT, D, T, F, FILES, BATCHES, COL, INK, RED, TEAL, GRAY, GRID


def main():
    setup()
    m=pd.read_csv(D/'final_cell_metrics.csv')
    labeled=m[m.cycle_life.notna()].copy()
    cycles=pd.read_csv(D/'cycles.csv')
    dq=np.load(D/'dq_curves.npz')
    p=labeled[(labeled.batch=='batch1') & labeled.near_eol_088].copy()
    split=pd.read_csv(D/'planned_day2_split.csv').merge(m,on=['cell_id','policy'],validate='one_to_one')
    train=split[split.role=='train_cv']
    out={}

    # 1. Window sensitivity around the gap: this is not a causal gap correction.
    slopes=[]
    for row in labeled.itertuples():
        z=cycles[cycles.cell_id==row.cell_id]
        for a,b in [(20,100),(20,40),(80,100)]:
            v=z[z.cycle.between(a,b)&z.QD.between(.5,2)].dropna(subset=['cycle','QD'])
            slopes.append(dict(cell_id=row.cell_id,batch=row.batch,family=row.protocol_family,
                window=f'{a}-{b}',slope=-100000*theilslopes(v.QD,v.cycle)[0]))
    sl=pd.DataFrame(slopes)
    sl.to_csv(D/'review_window_slopes.csv',index=False)
    agg=sl.groupby(['batch','family','window']).slope.agg(['count','median','min','max']).reset_index()
    agg.to_csv(T/'review_window_slopes.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(8.5,3.4),gridspec_kw={'width_ratios':[1.3,1]})
    z=cycles[(cycles.cell_id=='batch2_notion_c07')&cycles.cycle.between(20,100)]
    axs[0].plot(z.cycle,z.QD*1000,color=TEAL,lw=2)
    axs[0].axvspan(20,40,color='#E0EAF1',alpha=.8);axs[0].axvspan(80,100,color='#D9EEE9',alpha=.8)
    axs[0].axvline(70,color=RED,ls='--');axs[0].annotate('65시간 공백',xy=(70,1105.5),xytext=(.33,.92),textcoords='axes fraction',color=RED,arrowprops={'arrowstyle':'->','color':RED},fontsize=10)
    axs[0].set(xlabel='사이클',ylabel='QD (mAh)',title='B2 c07 · newstructure')
    b=agg[(agg.batch=='batch2_notion')&(agg.family=='newstructure')].set_index('window')
    vals=[b.loc[w,'median'] for w in ['20-100','20-40','80-100']]
    axs[1].barh(range(3),vals,color=[GRAY,COL['batch1'],TEAL],height=.5)
    axs[1].axvline(0,color=GRID);axs[1].set(yticks=range(3),yticklabels=['전체 20~100','공백 전 20~40','공백 후 80~100'],xlabel='용량 감소 기울기\n(mAh / 100사이클)',title='newstructure 9셀 중앙값',xlim=(-9,7));axs[1].invert_yaxis()
    for i,v in enumerate(vals):axs[1].text(v+(.3 if v>0 else -.3),i,f'{v:+.1f}',va='center',ha='left' if v>0 else 'right',fontweight='bold')
    save(fig,'review_gap_windows')

    # 2. Marginal support, with both the descriptive cohort and actual train set.
    features=['log10_dq_var','first_c_rate','second_c_rate','switch_soc_pct']
    sup=[]
    for refname,ref in [('B1_candidate36',p),('B1_train28',train)]:
        for b in BATCHES[1:]:
            g=labeled[labeled.batch==b];outside=(g[features]<ref[features].min())|(g[features]>ref[features].max())
            for f in features:
                sup.append(dict(reference=refname,batch=b,feature=f,n=len(g),outside=int(outside[f].sum()),low=float(ref[f].min()),high=float(ref[f].max())))
            sup.append(dict(reference=refname,batch=b,feature='any_marginal',n=len(g),outside=int(outside.any(axis=1).sum()),low=np.nan,high=np.nan))
    pd.DataFrame(sup).to_csv(T/'review_input_support.csv',index=False)
    fig,ax=plt.subplots(figsize=(8,3.0))
    groups=[('B1 학습 28',train),('B1 후보 36',p),('B2 standard 30',labeled[(labeled.batch=='batch2_notion')&(labeled.protocol_family=='standard')]),('B2 newstructure 9',labeled[(labeled.batch=='batch2_notion')&(labeled.protocol_family=='newstructure')]),('B3 44',labeled[labeled.batch=='batch3'])]
    rng=np.random.default_rng(20261001)
    ax.axvspan(train.log10_dq_var.min(),train.log10_dq_var.max(),color='#E4EEF5',label='학습 28셀 범위')
    for i,(name,g) in enumerate(groups):ax.scatter(g.log10_dq_var,i+rng.uniform(-.12,.12,len(g)),color=[COL['batch1'],GRAY,COL['batch2_notion'],TEAL,COL['batch3']][i],s=24,alpha=.85)
    ax.set(yticks=range(5),yticklabels=[x[0] for x in groups],xlabel='log10 var(ΔQ)');ax.invert_yaxis();ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(0,1.16),fontsize=10)
    save(fig,'review_input_support')
    sd=split.groupby('role').cycle_life.agg(['count','median','min','max']).reset_index();sd.to_csv(T/'review_split_distribution.csv',index=False)
    fig,ax=plt.subplots(figsize=(7.5,2.8))
    for i,(role,g) in enumerate(split.groupby('role')):
        ax.scatter(g.cycle_life,np.full(len(g),i)+rng.uniform(-.12,.12,len(g)),s=45,color=[COL['batch1'],TEAL][i]);med=g.cycle_life.median();ax.plot([med,med],[i-.23,i+.23],lw=3,color=INK);ax.text(med,i-.30,f'중앙값 {med:g}',ha='center',fontsize=12,fontweight='bold')
    ax.set(yticks=[0,1],yticklabels=['학습 28셀','홀드아웃 8셀'],xlabel='기록 수명 (사이클)',ylim=(1.5,-.65));ax.grid(axis='x',alpha=.2);save(fig,'review_split')

    # 3. Input transformation: distribution and relation, no fitted prediction.
    out['transform']={'raw_var_skew':float(skew(p.dq_var,bias=False)),'log_var_skew':float(skew(p.log10_dq_var,bias=False)),
        'raw_target_skew':float(skew(p.cycle_life,bias=False)),'log_target_skew':float(skew(np.log(p.cycle_life),bias=False))}
    fig,axs=plt.subplots(1,2,figsize=(8,3.4),sharey=True)
    for ax,x,lab in [(axs[0],p.dq_var*1e6,'ΔQ 분산 (mAh²)'),(axs[1],p.log10_dq_var,'log10 var(ΔQ) · Ah² 기준')]:
        ax.scatter(x,np.log(p.cycle_life),color=COL['batch1'],s=28,alpha=.8);ax.set(xlabel=lab);ax.grid(alpha=.15)
    axs[0].set_ylabel('log(기록 수명)');axs[0].set_title('원래 분산');axs[1].set_title('로그로 압축한 분산');save(fig,'review_transform_relation')
    fig,axs=plt.subplots(1,2,figsize=(7.8,2.7))
    for ax,x,title in [(axs[0],p.dq_var*1e6,'원래 분산 · 왜도 +1.11'),(axs[1],p.log10_dq_var,'로그 분산 · 왜도 +0.22')]:
        ax.hist(x,bins=8,color=COL['batch1'],edgecolor='white');ax.set(title=title,ylabel='셀 수')
    save(fig,'review_transform_distribution')

    # 4. Short life within an identical policy: a small case comparison.
    peers=labeled[(labeled.batch=='batch3')&(labeled.policy=='3.7C(31%)-5.9C-newstructure')].sort_values('cycle_life')
    peers[['cell_id','cycle_life','log10_dq_var','early_tavg_mean','ir_change_10_100']].to_csv(D/'review_shortest_peers.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(8.8,3.1))
    for ax,f,label,mult in [(axs[0],'log10_dq_var','log10 var(ΔQ)',1),(axs[1],'early_tavg_mean','초기 평균 온도 (°C)',1),(axs[2],'ir_change_10_100','IR100 - IR10 (mΩ)',1000)]:
        for r in peers.itertuples():
            color=RED if r.cell_id.endswith('c28') else GRAY
            ax.scatter(r.cycle_life,getattr(r,f)*mult,color=color,s=60);ax.annotate(r.cell_id[-3:],(r.cycle_life,getattr(r,f)*mult),xytext=(5,5),textcoords='offset points',fontsize=9,color=color)
        ax.set(xlabel='기록 수명',ylabel=label,xlim=(500,830));ax.grid(alpha=.15)
    save(fig,'review_shortest_signals')

    # 5. Raw time ratio at several cycles and threshold choices; raw Q(V) alignment.
    cr=[];align=[];alt=[]
    for b in BATCHES:
        with h5py.File(ROOT/'data/raw'/(FILES[b]+'_batchdata_updated_struct_errorcorrect.mat'),'r') as h:
            for row in labeled[labeled.batch==b].itertuples():
                rawq={};linq={};voltage=np.asarray(h[h['batch']['Vdlin'][int(row.source_position),0]]).ravel()
                grid=voltage[(voltage>=2.05)&(voltage<=3.45)]
                for cy in [10,20,30,40,80,100]:
                    a=raw(h,row,cy,('t','I','V','Qd','Qdlin'))
                    if cy in [10,20,30,80,100]:
                        dt=np.diff(a['t']);mid=(a['I'][1:]+a['I'][:-1])/2;neg=np.flatnonzero(a['I']<-.1);stop=int(neg[0]) if len(neg) else len(a['I']);dt=dt[:stop-1];mid=mid[:stop-1];valid=(mid>.1)&(dt>0)&(dt<1)
                        for threshold in [4.1,4.2,4.3]:
                            frac=float(dt[valid&(mid>threshold)].sum()/dt[valid].sum())
                            cr.append(dict(cell_id=row.cell_id,batch=b,cycle=cy,threshold=threshold,fraction=frac))
                    if cy in [10,40,80,100]:linq[cy]=a['Qdlin']
                    if cy in [10,100]:
                        # Largest uninterrupted negative-current segment; common interior support.
                        ids=np.flatnonzero((a['I']<-.1)&np.isfinite(a['Qd'])&np.isfinite(a['V']))
                        seg=max(np.split(ids,np.flatnonzero(np.diff(ids)>1)+1),key=len)
                        v=a['V'][seg];q=a['Qd'][seg]
                        # Some B2 Qd samples are isolated zeros after discharge has
                        # accumulated charge. Retain the record, exclude invalid
                        # zero readings only from this raw reconstruction.
                        bad_zero=(q==0)&(np.maximum.accumulate(q)>.05)
                        v=v[~bad_zero];q=q[~bad_zero]
                        order=np.argsort(v);v=v[order];q=q[order];uv,inv=np.unique(v,return_inverse=True);uq=np.bincount(inv,weights=q)/np.bincount(inv)
                        supported=bool(uv.min()<=grid.min() and uv.max()>=grid.max())
                        rawq[cy]=np.interp(grid,uv,uq)
                        stored=np.interp(grid,voltage[::-1],a['Qdlin'][::-1]);error=(stored-stored[0])-(rawq[cy]-rawq[cy][0])
                        align.append(dict(cell_id=row.cell_id,batch=b,cycle=cy,supported=supported,invalid_zero_count=int(bad_zero.sum()),origin_offset_mAh=float((stored[0]-rawq[cy][0])*1000),shape_rmse_mAh=float(np.sqrt(np.mean(error**2))*1000),shape_max_mAh=float(np.max(np.abs(error))*1000)))
                alt.append(dict(cell_id=row.cell_id,batch=b,logvar_raw_reconstruction=float(np.log10(np.var(rawq[100]-rawq[10]))),
                    logvar_stored_interior=float(np.log10(np.var(np.interp(grid,voltage[::-1],(linq[100]-linq[10])[::-1])))),
                    logvar_pre=float(np.log10(np.var(linq[40]-linq[10]))),logvar_post=float(np.log10(np.var(linq[100]-linq[80])))))
        print('raw review complete:',b,flush=True)
    cr=pd.DataFrame(cr);cr.to_csv(D/'review_current_ratios.csv',index=False)
    joined=cr.merge(labeled[['cell_id','cycle_life','early_qd_loss_robust_per_100_cycles']],on='cell_id')
    ca=[]
    for (b,cy,th),g in joined.groupby(['batch','cycle','threshold']):
        ca.append(dict(batch=b,cycle=cy,threshold=th,n=len(g),rho_life=rho(g,'fraction'),rho_slope=rho(g,'fraction','early_qd_loss_robust_per_100_cycles')))
    ca=pd.DataFrame(ca);ca.to_csv(T/'review_current_sensitivity.csv',index=False)
    stability=[]
    for b,g in cr.groupby('batch'):
        z=g[g.threshold==4.2].pivot(index='cell_id',columns='cycle',values='fraction')
        stability.append(dict(batch=b,median_within_cell_range=float((z.max(axis=1)-z.min(axis=1)).median()),max_within_cell_range=float((z.max(axis=1)-z.min(axis=1)).max())))
    pd.DataFrame(stability).to_csv(T/'review_current_stability.csv',index=False)
    al=pd.DataFrame(align);al.to_csv(D/'review_raw_alignment.csv',index=False)
    alg=al.groupby('batch').agg(n_curves=('cycle','size'),supported=('supported','sum'),median_shape_rmse_mAh=('shape_rmse_mAh','median'),max_shape_rmse_mAh=('shape_rmse_mAh','max'),median_offset_mAh=('origin_offset_mAh','median')).reset_index();alg.to_csv(T/'review_raw_alignment.csv',index=False)
    alt=pd.DataFrame(alt).merge(labeled[['cell_id','cycle_life','protocol_family','log10_dq_var']],on='cell_id');alt.to_csv(D/'review_delta_sensitivity.csv',index=False)
    altrows=[]
    for b,g in alt.groupby('batch'):
        for f in ['log10_dq_var','logvar_raw_reconstruction','logvar_stored_interior','logvar_pre','logvar_post']:
            altrows.append(dict(batch=b,feature=f,n=len(g),rho_life=rho(g,f),rho_original=1.0 if f=='log10_dq_var' else rho(g,f,'log10_dq_var')))
    pd.DataFrame(altrows).to_csv(T/'review_delta_sensitivity.csv',index=False)
    # Plot the full diagnostic range to avoid choosing a favorable cut/cycle.
    fig,axs=plt.subplots(1,2,figsize=(8,3.0),sharey=True)
    for ax,f,title in [(axs[0],'rho_life','고전류 시간 비율 ↔ 수명'),(axs[1],'rho_slope','고전류 시간 비율 ↔ QD 감소')]:
        for i,b in enumerate(BATCHES):
            g=ca[ca.batch==b];ax.plot([g[f].min(),g[f].max()],[i,i],color=COL[b],lw=7,solid_capstyle='round');ax.scatter(g[f],np.full(len(g),i),s=12,color=COL[b],zorder=3)
        ax.axvline(0,color=GRAY,ls=':');ax.set(title=title,xlim=(-.6,.6),xlabel='Spearman 상관',yticks=range(3),yticklabels=['B1','B2','B3'],ylim=(2.5,-.5))
    save(fig,'review_current_sensitivity')

    # Same sample for pooled vs policy-centered primary comparison.
    q=p[p.groupby('policy').cell_id.transform('size')>=2].copy()
    center=q.copy()
    for f in ['log10_dq_var','cycle_life']:center[f]-=center.groupby('policy')[f].transform('mean')
    out['policy_same_sample']={'n':len(q),'policies':q.policy.nunique(),'pooled':rho(q,'log10_dq_var'),'centered':rho(center,'log10_dq_var')}
    fig,axs=plt.subplots(1,2,figsize=(8.3,3.2))
    for ax,g,title in [(axs[0],q,'정책 차이까지 함께 보면'),(axs[1],center,'각 정책의 평균을 빼면')]:
        ax.scatter(g.log10_dq_var,g.cycle_life,s=32,color=COL['batch1'],alpha=.8);ax.set(xlabel='log10 var(ΔQ)'+('의 평균 대비 차이' if g is center else ''),ylabel='수명'+('의 평균 대비 차이' if g is center else ''),title=title);ax.grid(alpha=.15)
        ax.text(.97,.92,f'ρ={rho(g,"log10_dq_var"):+.2f}',ha='right',transform=ax.transAxes,fontsize=14,fontweight='bold')
    save(fig,'review_policy_centered')
    (ROOT/'results/final/review_analysis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print(alg.to_string(index=False))
    print(ca.groupby('batch')[['rho_life','rho_slope']].agg(['min','max']).to_string())
    print(pd.DataFrame(altrows).to_string(index=False))


if __name__=='__main__': main()
