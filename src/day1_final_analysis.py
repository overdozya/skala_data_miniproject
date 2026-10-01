"""DAY 1: descriptive checks for a fresh, evidence-led report. No model fitting.

Every public CSV is aggregated. Cell-level traces/diagnostics stay in ignored
data/processed. Stored I is plotted without another unit conversion: matching
plateaus and charge integration suggest a C-rate scale, not amperes.
"""
from pathlib import Path
import json
import h5py
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, skew, theilslopes
from sklearn.model_selection import GroupShuffleSplit, GroupKFold
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
from eda import knee_one, policy_bootstrap

ROOT = Path(__file__).resolve().parents[1]
D = ROOT/'data/processed'
OUT = ROOT/'results/final'
F = OUT/'figures'
T = OUT/'tables'
FONT = '/System/Library/AssetsV2/com_apple_MobileAsset_Font7/bad9b4bf17cf1669dde54184ba4431c22dcad27b.asset/AssetData/NanumGothic.ttc'
BATCHES = ['batch1','batch2_notion','batch3']
NAMES = dict(zip(BATCHES,['Batch 1','Batch 2','Batch 3']))
COL = dict(zip(BATCHES,['#316C9B','#C77E29','#8360A8']))
INK='#20374B'; RED='#C5514E'; TEAL='#168579'; GRAY='#748593'; GRID='#DFE6EB'
FILES = dict(zip(BATCHES,['2017-05-12','2018-02-20','2018-04-12']))

def setup():
    F.mkdir(parents=True,exist_ok=True);T.mkdir(parents=True,exist_ok=True)
    font_manager.fontManager.addfont(FONT)
    plt.rcParams.update({'font.family':font_manager.FontProperties(fname=FONT).get_name(),
      'font.size':11,'axes.titlesize':13,'axes.labelsize':11,'axes.unicode_minus':False,
      'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':GRID,
      'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,
      'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})

def save(fig,name):
    fig.tight_layout(pad=1.2)
    fig.savefig(F/(name+'.png'),dpi=220,bbox_inches='tight')
    plt.close(fig)

def rho(g,x,y='cycle_life'):
    p=g[[x,y]].replace([np.inf,-np.inf],np.nan).dropna()
    return float(spearmanr(p[x],p[y]).statistic) if len(p)>3 and p[x].nunique()>1 and p[y].nunique()>1 else np.nan

def raw(h,row,c,keys=('t','I','Qc','Qd')):
    g=h[h['batch']['cycles'][int(row.source_position),0]]
    return {k:np.asarray(h[g[k][c-1,0]]).ravel() for k in keys}

def raw_checks(cells,cycles):
    rows=[]; traces={}
    for b in BATCHES:
        with h5py.File(ROOT/'data/raw'/(FILES[b]+'_batchdata_updated_struct_errorcorrect.mat'),'r') as h:
            for row in cells[cells.batch==b].itertuples():
                a=raw(h,row,10);t,I=a['t'],a['I']; dt=np.diff(t);mid=(I[1:]+I[:-1])/2
                charge=float(np.sum(dt[mid>0]*mid[mid>0])/60)
                # A fixed diagnostic cut at 4.2 avoids numerical noise near 4C plateaus.
                neg=np.flatnonzero(I<-.1);stop=int(neg[0]) if len(neg) else len(I)
                m=(mid[:stop-1]>.1)&(dt[:stop-1]>0)&(dt[:stop-1]<1)
                active=float(dt[:stop-1][m].sum())
                frac=float(dt[:stop-1][m&(mid[:stop-1]>4.2)].sum()/active) if active else np.nan
                firstpos=np.flatnonzero(I>.1)[0]; plateau=np.median(I[firstpos:firstpos+10])
                breaks=[]
                for c in range(20,101):
                    z=raw(h,row,c,('t',))['t']; gap=float(np.max(np.diff(z))) if len(z)>1 else 0
                    if gap>60: breaks.append((c,gap))
                rows.append({'cell_id':row.cell_id,'i_plateau10':plateau,
                    'integral_to_qc_ratio':charge/np.max(a['Qc']),
                    'high_current_fraction10':frac,'active_charge_min10':active,
                    'max_gap20_100_min':max([v for _,v in breaks],default=0),
                    'gap_cycles':';'.join(str(c) for c,_ in breaks)})
                if row.cell_id in ['batch1_c20','batch1_c24','batch2_notion_c00','batch2_notion_c07','batch3_c00']:
                    traces[row.cell_id+'_10']=a
                    for c in ([47,48,49] if row.cell_id.endswith('c00') and b=='batch2_notion' else
                              [69,70,71] if row.cell_id.endswith('c07') else []):
                        traces[row.cell_id+'_'+str(c)]=raw(h,row,c)
    q=cells.merge(pd.DataFrame(rows),on='cell_id',validate='one_to_one')
    q.to_csv(D/'final_cell_metrics.csv',index=False)
    np.savez_compressed(D/'final_raw_traces.npz',**{key+'_'+k:v for key,a in traces.items() for k,v in a.items()})
    return q,traces

def main():
    setup()
    cells=pd.read_csv(D/'revised_cell_metrics.csv');cycles=pd.read_csv(D/'cycles.csv')
    dq=np.load(D/'dq_curves.npz')
    cells,traces=raw_checks(cells,cycles)
    labeled=cells[cells.cycle_life.notna()].copy()
    labeled['base_policy']=labeled.policy.str.replace('-newstructure','',regex=False)
    b1=labeled[labeled.batch=='batch1'];primary=b1[b1.near_eol_088];b2=labeled[labeled.batch=='batch2_notion']
    out={'n_all':len(cells),'n_labeled':len(labeled),'primary_n':len(primary),'batches':{}}
    for b,g in labeled.groupby('batch',sort=False):
        out['batches'][b]={'n':len(g),'median':g.cycle_life.median(),'short':int(sum(g.cycle_life<500)),
          'long':int(sum(g.cycle_life>1000)),'min':g.cycle_life.min(),'max':g.cycle_life.max(),
          'raw_skew':float(skew(g.cycle_life,bias=False)),'log_skew':float(skew(np.log(g.cycle_life),bias=False)),
          'cells_with_time_gaps':int(sum(g.max_gap20_100_min>60)),
          'current_integral_ratio':float(g.integral_to_qc_ratio.median())}

    # Composition is a real covariate shift, not a causal structure experiment.
    comp=cells.groupby(['batch','protocol_family']).agg(total=('cell_id','size'),labeled=('cycle_life','count')).reset_index()
    comp.to_csv(T/'cohort_composition.csv',index=False)
    fig,ax=plt.subplots(figsize=(8,2.7))
    fams=['standard','newstructure','varcharge','slowcycle'];familycolors=[COL['batch1'],TEAL,'#BDCBD5','#E3E8ED']
    for y,b in enumerate(BATCHES):
        left=0
        for fam,color in zip(fams,familycolors):
            n=sum((cells.batch==b)&(cells.protocol_family==fam))
            if n:
                ax.barh(y,n,left=left,color=color,height=.55)
                ax.text(left+n/2,y,str(n),ha='center',va='center',color='white' if fam in fams[:2] else INK,fontweight='bold',fontsize=14)
                left+=n
    ax.set(yticks=range(3),yticklabels=['B1','B2','B3'],xlim=(0,50),xlabel='전체 셀 수 (수명 레이블 결측 포함)');ax.invert_yaxis()
    ax.legend(handles=[Patch(color=color,label=fam) for fam,color in zip(fams,familycolors)],loc='upper center',bbox_to_anchor=(.5,1.22),ncol=4,frameon=False,fontsize=10)
    save(fig,'composition')

    # Exact requested histogram domain, same bins in every batch.
    fig,axs=plt.subplots(1,3,figsize=(12.3,3.3),sharey=True)
    bins=np.r_[np.arange(150,2300,150),2300]
    for ax,b in zip(axs,BATCHES):
        g=labeled[labeled.batch==b]
        ax.hist(g.cycle_life,bins=bins,color=COL[b],edgecolor='white',rwidth=.98)
        ax.axvline(500,color=RED,ls='--',lw=1);ax.axvline(1000,color=TEAL,ls='--',lw=1)
        ax.set(title=f'{NAMES[b]} · n={len(g)}',xlim=(150,2300),xticks=[150,500,1000,1500,2000,2300],xlabel='기록 수명 (사이클)');ax.tick_params(axis='x',labelsize=9)
        ax.text(.97,.92,f'중앙값 {g.cycle_life.median():g}',transform=ax.transAxes,ha='right',fontsize=11)
        ax.grid(axis='y',alpha=.2)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    axs[0].set_ylabel('셀 수');save(fig,'life_histogram')

    # Same policy comparisons across batches/families expose residual shift.
    matched=labeled[labeled.base_policy=='4.8C(80%)-4.8C'].groupby(['batch','protocol_family']).agg(n=('cell_id','size'),mean=('cycle_life','mean'),minimum=('cycle_life','min'),maximum=('cycle_life','max'),logvar=('log10_dq_var','mean')).reset_index()
    matched['family_order']=matched.protocol_family.map({'standard':0,'newstructure':1})
    matched=matched.sort_values(['batch','family_order']).drop(columns='family_order')
    matched.to_csv(T/'same_policy_across_batches.csv',index=False)
    fig,ax=plt.subplots(figsize=(7.8,3.2)); labs=[]
    for i,r in enumerate(matched.itertuples()):
        color=TEAL if r.protocol_family=='newstructure' else COL[r.batch]
        ax.errorbar(i,r.mean,yerr=[[r.mean-r.minimum],[r.maximum-r.mean]],fmt='o',color=color,capsize=5,ms=9,lw=2)
        ax.text(i,r.maximum+65,f'{r.mean:.0f}  (n={r.n})',ha='center',fontsize=12,fontweight='bold')
        labs.append(NAMES[r.batch]+'\n'+r.protocol_family)
    ax.set(xticks=range(len(matched)),xticklabels=labs,ylabel='평균 수명과 관측 최솟값~최댓값',xlim=(-.6,3.6),ylim=(300,2080));ax.grid(axis='y',alpha=.2);save(fig,'same_policy')

    # Labels and sample curation.
    fig,ax=plt.subplots(figsize=(7.8,3.2))
    for b in BATCHES:
        g=labeled[labeled.batch==b]
        ax.scatter(g.cycle_life,g.last_qd,color=COL[b],s=30,alpha=.72,label=NAMES[b])
    ax.axhline(.88,color=RED,lw=1.4);ax.axhline(.885,color=RED,ls=':',lw=1)
    ax.set(xlabel='저장된 cycle_life',ylabel='기록 마지막 QD (Ah)',ylim=(.79,1.065));ax.legend(frameon=False,loc='lower right')
    ax.annotate('B1 10셀: 아직 종료에서 멀다',xy=(1177,1.043),xytext=(630,1.056),arrowprops={'arrowstyle':'->','color':RED},color=RED,fontsize=11)
    save(fig,'endpoint_labels')
    out['primary']={'n':len(primary),'policies':primary.policy.nunique(),'median':primary.cycle_life.median(),
       'raw_skew':float(skew(primary.cycle_life,bias=False)),'log_skew':float(skew(np.log(primary.cycle_life),bias=False)),
       'max':primary.cycle_life.max(),'min':primary.cycle_life.min()}

    # Shortest examples are kept; inspect their peers before calling them errors.
    shortrows=[]
    for b,g in labeled.groupby('batch',sort=False):
        r=g.nsmallest(1,'cycle_life').iloc[0];peers=g[g.policy==r.policy]
        shortrows.append({'batch':b,'cell_id':r.cell_id,'life':r.cycle_life,'policy':r.policy,
            'peers':len(peers),'peer_min':peers.cycle_life.min(),'peer_max':peers.cycle_life.max(),
            'observed_cross':r.observed_below_088})
    pd.DataFrame(shortrows).to_csv(T/'shortest_cell_context.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(12.2,3.3),sharey=True)
    for ax,b,r in zip(axs,BATCHES,shortrows):
        peers=labeled[(labeled.batch==b)&(labeled.policy==r['policy'])]
        for row in peers.itertuples():
            z=cycles[(cycles.cell_id==row.cell_id)&(cycles.cycle>=10)&(cycles.cycle<=row.cycle_life)]
            sel=row.cell_id==r['cell_id'];ax.plot(z.cycle,z.QD.rolling(7,min_periods=1).median(),color=RED if sel else GRAY,lw=2 if sel else 1,alpha=1 if sel else .4)
        ax.set(title=f"{NAMES[b]} 최단 {r['cell_id'].split('_')[-1]} · {r['life']:.0f}",xlabel='사이클',ylim=(.86,1.15),xlim=(0,1200));ax.axhline(.88,color=RED,ls=':',lw=1)
    axs[0].set_ylabel('QD (Ah)');save(fig,'shortest_peers')

    # Future curves illustrate acceleration, and cannot be prediction inputs.
    knees=[]
    for r in labeled.itertuples():
        p,gain,ratio,found=knee_one(cycles[cycles.cell_id==r.cell_id],r.cycle_life)
        knees.append({'batch':r.batch,'cell_id':r.cell_id,'knee':p,'fraction':p/r.cycle_life,'ratio':ratio,'found':found})
    kd=pd.DataFrame(knees);kd.to_csv(D/'final_knees.csv',index=False)
    ksum=kd.groupby('batch').agg(n=('cell_id','size'),found=('found','sum'),median_cycle=('knee','median'),median_fraction=('fraction','median'),median_slope_ratio=('ratio','median'))
    foundstats=kd[kd.found].groupby('batch')[['knee','fraction','ratio']].median()
    ksum[['median_cycle','median_fraction','median_slope_ratio']]=foundstats[['knee','fraction','ratio']].to_numpy()
    ksum.to_csv(T/'knee_summary.csv')
    fig,axs=plt.subplots(1,3,figsize=(12.3,3.4),sharey=True)
    for ax,b in zip(axs,BATCHES):
        g=labeled[(labeled.batch==b)&labeled.near_eol_088].sort_values('cycle_life')
        for r in g.itertuples():
            z=cycles[(cycles.cell_id==r.cell_id)&(cycles.cycle>=10)&(cycles.cycle<=r.cycle_life)]
            ax.plot(z.cycle,z.QD.rolling(7,min_periods=1).median(),color=COL[b],alpha=.13,lw=.7)
        r=g.iloc[len(g)//2];z=cycles[(cycles.cell_id==r.cell_id)&(cycles.cycle>=10)&(cycles.cycle<=r.cycle_life)]
        ax.plot(z.cycle,z.QD.rolling(7,min_periods=1).median(),color=COL[b],lw=2.5)
        k=kd[kd.cell_id==r.cell_id].iloc[0];value=z.iloc[(z.cycle-k.knee).abs().argmin()].QD
        ax.scatter(k.knee,value,color=RED,s=35,zorder=5)
        ax.annotate(f'탐색 knee {k.knee:.0f}',xy=(k.knee,value),xytext=(.39,.70),textcoords='axes fraction',arrowprops={'arrowstyle':'->','color':RED},color=RED,fontsize=10)
        ax.axvspan(0,100,color='#DBE8F1',alpha=.8);ax.axhline(.88,color=RED,ls=':',lw=1)
        ax.set(title=f'{NAMES[b]} · 종료 근접 {len(g)}셀',xlabel='사이클',xlim=(0,2000),ylim=(.86,1.14))
    axs[0].set_ylabel('QD (Ah)');save(fig,'full_trajectories')

    # Trace a suspicious step to an actual long time gap, without asserting cause.
    fig,axs=plt.subplots(1,2,figsize=(10.5,3.4))
    for ax,cid,event,color in zip(axs,['batch2_notion_c00','batch2_notion_c07'],[48,70],[COL['batch2_notion'],TEAL]):
        z=cycles[(cycles.cell_id==cid)&cycles.cycle.between(event-8,event+12)]
        ax.plot(z.cycle,z.QD*1000,'o-',ms=4,lw=1.7,color=color)
        q=float(z.loc[z.cycle==event,'QD'].iloc[0])*1000
        a=traces[cid+'_'+str(event)];gap=np.diff(a['t']).max()
        ax.axvline(event,color=RED,ls='--',lw=1)
        ax.annotate(f'기록 간격 {gap/60:.1f}시간',xy=(event,q),xytext=(.48 if event==48 else .03,.90),textcoords='axes fraction',color=RED,arrowprops={'arrowstyle':'->','color':RED},fontsize=12)
        ax.set(title=cid.replace('batch2_notion_','B2 ')+' · '+('standard' if event==48 else 'newstructure'),xlabel='사이클',ylabel='QD (mAh)');ax.grid(alpha=.2)
    save(fig,'time_gap_capacity')
    gaprows=labeled.groupby(['batch','protocol_family']).agg(n=('cell_id','size'),cells_with_gaps=('max_gap20_100_min',lambda x:sum(x>60)),max_gap_min=('max_gap20_100_min','max'))
    gaprows.to_csv(T/'time_gap_summary.csv')

    # Early scalar evidence vs voltage-resolved shape.
    fig,axs=plt.subplots(1,3,figsize=(12.2,3.2),sharey=True)
    for ax,b in zip(axs,BATCHES):
        g=labeled[labeled.batch==b];ax.scatter(g.qd_change_10_100*1000,g.cycle_life,s=32,color=COL[b],alpha=.8)
        ax.set(title=f'{NAMES[b]} · ρ={rho(g,"qd_change_10_100"):+.2f}',xlabel='QD100 - QD10 (mAh)');ax.axvline(0,color=GRID,lw=1);ax.grid(alpha=.18)
    axs[0].set_ylabel('기록 수명');save(fig,'scalar_delta')
    for fname,groups in [('dq_all',[(NAMES[b],labeled[labeled.batch==b]) for b in BATCHES]),
                         ('dq_within_b2',[(f'B2 {fam}',b2[b2.protocol_family==fam]) for fam in ['standard','newstructure']])]:
        fig,axs=plt.subplots(1,len(groups),figsize=(12.2 if len(groups)==3 else 8.2,3.3),sharey=True)
        for ax,(name,g) in zip(np.atleast_1d(axs),groups):
            g=g.sort_values('cycle_life');k=len(g)//3
            for lab,p,color in [('하위 1/3',g.iloc[:k],RED),('상위 1/3',g.iloc[-k:],TEAL)]:
                a=np.stack([dq[cid+'_dq']*1000 for cid in p.cell_id]);v=dq[p.iloc[0].cell_id+'_voltage']
                ax.plot(v,np.median(a,axis=0),color=color,lw=2,label=f'{lab} (n={len(p)})')
                ax.fill_between(v,np.quantile(a,.25,axis=0),np.quantile(a,.75,axis=0),color=color,alpha=.13)
            ax.axvspan(2.8,3.1,color='#F2D997',alpha=.22);ax.axhline(0,color=GRID,lw=1)
            ax.set(title=name,xlabel='방전 전압 (V)',xlim=(2,3.5));ax.legend(frameon=False,fontsize=9,loc='lower right');ax.grid(alpha=.15)
        np.atleast_1d(axs)[0].set_ylabel('ΔQ(V) (mAh)');save(fig,fname)

    cond=[]
    for name,g in [(NAMES[b],labeled[labeled.batch==b]) for b in BATCHES]+[('B1 종료 근접',primary)]:
        p=g[g.groupby('policy').cell_id.transform('size')>=2].copy()
        for col in ['log10_dq_var','cycle_life']:p[col]-=p.groupby('policy')[col].transform('mean')
        boot=policy_bootstrap(g[g.groupby('policy').cell_id.transform('size')>=2],'log10_dq_var',True,draws=1500,seed=20261001)
        cond.append({'group':name,'n':len(g),'within_n':len(p),'policies':p.policy.nunique(),'pooled':rho(g,'log10_dq_var'),'centered':rho(p,'log10_dq_var'),'ci_low':boot['lo'],'ci_high':boot['hi']})
    pd.DataFrame(cond).to_csv(T/'conditional_dq.csv',index=False)
    fig,ax=plt.subplots(figsize=(6.4,3.6))
    for i,r in enumerate(cond[:3]):
        ax.plot([r['pooled'],r['centered']],[i,i],color=GRID,lw=4)
        ax.scatter(r['pooled'],i,s=80,color=COL[BATCHES[i]],label='전체' if i==0 else None,zorder=3)
        ax.errorbar(r['centered'],i,xerr=[[r['centered']-r['ci_low']],[r['ci_high']-r['centered']]],fmt='o',color=INK,ms=7,capsize=3,label='정책 평균 제거 · 95% 재표집 구간' if i==0 else None)
        ax.text(r['pooled']-.02,i+.18,f"{r['pooled']:+.2f}",ha='center',color=COL[BATCHES[i]],fontsize=11)
        ax.text(r['centered'],i+.18,f"{r['centered']:+.2f}",ha='center',color=INK,fontsize=11)
    ax.axvline(0,color=GRAY,ls=':',lw=1);ax.set(yticks=range(3),yticklabels=['B1','B2','B3'],xlim=(-1,.5),ylim=(-.5,2.7),xlabel='log10 var(ΔQ) ↔ 수명 · Spearman ρ');ax.invert_yaxis();ax.legend(frameon=False,fontsize=9,loc='lower left');save(fig,'conditional_dq')

    # Full protocol summaries and current patterns.
    pol=labeled.groupby(['batch','policy','protocol_family']).agg(n=('cell_id','size'),mean=('cycle_life','mean'),minimum=('cycle_life','min'),maximum=('cycle_life','max'),first_c=('first_c_rate','first'),early_loss=('early_qd_loss_robust_per_100_cycles','mean')).reset_index()
    pol.to_csv(T/'all_policy_means.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(12.3,3.4),sharey=True)
    for ax,b in zip(axs,BATCHES):
        g=pol[pol.batch==b]
        for r in g.itertuples():
            color=TEAL if r.protocol_family=='newstructure' else COL[b]
            ax.errorbar(r.first_c,r.mean,yerr=[[r.mean-r.minimum],[r.maximum-r.mean]],fmt='o',ms=4+np.sqrt(r.n),alpha=.72,color=color,capsize=2)
        ax.set(title=NAMES[b]+' · '+str(len(g))+'개 정책',xlabel='첫 단계 C-rate',xlim=(3.2,8.4),ylim=(300,2000));ax.grid(alpha=.2)
    axs[0].set_ylabel('정책별 평균 수명 (선: 셀 최솟값~최댓값)');save(fig,'policy_mean_scatter')
    fig,axs=plt.subplots(1,3,figsize=(12.2,3.2),sharey=True)
    for ax,cid in zip(axs,['batch1_c24','batch2_notion_c00','batch3_c00']):
        a=traces[cid+'_10'];r=cells[cells.cell_id==cid].iloc[0];ix=np.flatnonzero(a['I']<-.1);stop=ix[0] if len(ix) else len(a['I'])
        ax.plot(a['t'][:stop],a['I'][:stop],color=COL[r.batch],lw=2)
        ax.set(title=NAMES[r.batch]+' · '+r.policy.replace('-newstructure',''),xlabel='사이클 내 경과 시간 (분)',xlim=(0,32),ylim=(-.2,7));ax.grid(alpha=.2)
    axs[0].set_ylabel('저장된 전류 I (정책 C-rate와 스케일 일치)');save(fig,'current_traces')
    assoc=[]
    for b,g in labeled.groupby('batch',sort=False):
        for x in ['first_c_rate','second_c_rate','switch_soc_pct','high_current_fraction10']:
            for y in ['cycle_life','early_qd_loss_robust_per_100_cycles','log10_dq_var']:
                assoc.append({'batch':b,'predictor':x,'outcome':y,'n':len(g),'rho':rho(g,x,y)})
    pd.DataFrame(assoc).to_csv(T/'charging_associations.csv',index=False)

    # Feature quality: zeros are measurements needing a rule, not valid low IR.
    qrows=[]
    for b,g in labeled.groupby('batch',sort=False):
        ir=g.ir_change_10_100.copy();ir[(g.ir_10<=0)|(g.ir_100<=0)]=np.nan
        p=g.assign(ir_clean=ir)
        qrows.append({'batch':b,'n':len(g),'zero_ir10_or100':int(sum((g.ir_10<=0)|(g.ir_100<=0))),
           'raw_ir_delta_rho':rho(g,'ir_change_10_100'),'clean_ir_delta_rho':rho(p,'ir_clean'),
           'clean_ir_n':int(ir.notna().sum())})
    pd.DataFrame(qrows).to_csv(T/'ir_quality_sensitivity.csv',index=False)
    feats={'qd_10':'初기 용량 QD10','qd_change_10_100':'QD100 - QD10','ir_10':'IR10 (0 제외)',
      'ir_change_10_100':'IR 변화 (0 제외)','early_tavg_mean':'평균 온도 (2~100)',
      'early_tmax_mean':'최고 온도의 평균','early_charge_mean':'평균 충전 시간',
      'log10_dq_var':'log10 var(ΔQ)','dq_mean':'ΔQ 평균','dq_min':'ΔQ 최솟값'}
    groups=[('B1 전체',b1),('B1 종료 근접',primary),('B2',b2),('B3',labeled[labeled.batch=='batch3'])]
    cr=[]
    for feat,label in feats.items():
        row={'feature':feat,'label':label.replace('初','초')}
        for name,g in groups:
            p=g.copy()
            if feat=='ir_10':p.loc[p.ir_10<=0,feat]=np.nan
            if feat=='ir_change_10_100':p.loc[(p.ir_10<=0)|(p.ir_100<=0),feat]=np.nan
            row[name]=rho(p,feat)
        cr.append(row)
    cor=pd.DataFrame(cr);cor.to_csv(T/'feature_life_correlations.csv',index=False)
    fig,ax=plt.subplots(figsize=(8.4,5.0));v=cor[[n for n,g in groups]].to_numpy();im=ax.imshow(v,vmin=-1,vmax=1,cmap='RdBu_r',aspect='auto')
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):ax.text(j,i,f'{v[i,j]:+.2f}',ha='center',va='center',color='white' if abs(v[i,j])>.62 else INK,fontsize=12)
    ax.set(xticks=range(4),xticklabels=[n for n,g in groups],yticks=range(len(cor)),yticklabels=cor.label)
    fig.colorbar(im,ax=ax,pad=.03,shrink=.8,label='Spearman ρ');save(fig,'feature_heatmap')
    select=['log10_dq_var','first_c_rate','second_c_rate','switch_soc_pct'];mat=primary[select].corr(method='spearman');mat.to_csv(T/'selected_input_redundancy.csv')
    fig,ax=plt.subplots(figsize=(5.2,4.0));v=mat.to_numpy();ax.imshow(v,vmin=-1,vmax=1,cmap='RdBu_r');names=['log 분산','첫 C-rate','둘째 C-rate','전환 SOC']
    for i in range(4):
        for j in range(4):ax.text(j,i,f'{v[i,j]:+.2f}',ha='center',va='center',color='white' if abs(v[i,j])>.62 else INK,fontsize=13)
    ax.set(xticks=range(4),xticklabels=names,yticks=range(4),yticklabels=names);save(fig,'selected_collinearity')

    # The Qdlin origin check matters in B3: variance is translation invariant.
    origin=[]
    for b,g in labeled.groupby('batch',sort=False):
        means=[];mins=[];variances=[];rawvars=[];offsets=[]
        for cid in g.cell_id:
            a=dq[cid+'_dq'];a0=a-a[0];means.append(a0.mean());mins.append(a0.min());variances.append(a0.var());rawvars.append(a.var());offsets.append(a[0])
        p=g.assign(dq_mean_aligned=means,dq_min_aligned=mins)
        origin.append({'batch':b,'max_abs_offset_mAh':float(np.max(np.abs(offsets))*1000),'median_offset_mAh':float(np.median(offsets)*1000),
           'var_max_abs_difference':float(np.max(np.abs(np.array(rawvars)-variances))),
           'mean_raw_rho':rho(g,'dq_mean'),'mean_aligned_rho':rho(p,'dq_mean_aligned')})
    pd.DataFrame(origin).to_csv(T/'delta_q_origin_check.csv',index=False)
    # Author's exclusion mapping is applied in the documented order.
    b3=cells[cells.batch=='batch3'].copy();b3=b3[b3.source_position!=37];b3=b3[b3.last_qd<=.885]
    noisy=b3.iloc[[2,39,40]].cell_id.tolist();b3clean=b3[~b3.cell_id.isin(noisy)]
    out['b3_author_sensitivity']={'excluded_ids':['batch3_c37']+noisy,'n_after':len(b3clean),
       'rho_all':rho(labeled[labeled.batch=='batch3'],'log10_dq_var'),'rho_clean':rho(b3clean,'log10_dq_var')}
    # B1-only target transformation comparison.
    fig,axs=plt.subplots(1,2,figsize=(8.8,3.3))
    for ax,values,label in [(axs[0],primary.cycle_life,'기록 수명'),(axs[1],np.log(primary.cycle_life),'log(기록 수명)')]:
        ax.hist(values,bins=8,color=COL['batch1'],edgecolor='white');ax.set(xlabel=label,ylabel='셀 수');ax.text(.98,.94,f'왜도 {skew(values,bias=False):+.2f}',ha='right',va='top',transform=ax.transAxes,fontsize=12)
    save(fig,'target_transform')
    # Keep descriptive checks and publication totals machine-readable.
    out['conditional']=cond;out['ir_quality']=qrows;out['dq_origin']=origin
    out['charging_associations']=assoc
    out['primary_rho_dq']=rho(primary,'log10_dq_var')
    out['primary_redundancy_rate_soc']=float(mat.loc['first_c_rate','switch_soc_pct'])
    out['primary_redundancy_dq_mean']=rho(primary,'log10_dq_var','dq_mean')
    out['primary_redundancy_dq_min']=rho(primary,'log10_dq_var','dq_min')
    train_i,valid_i=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=20261001).split(primary,groups=primary.policy))
    train,valid=primary.iloc[train_i],primary.iloc[valid_i]
    split=pd.concat([train[['cell_id','policy']].assign(role='train_cv'),valid[['cell_id','policy']].assign(role='valid_holdout')])
    split.to_csv(D/'planned_day2_split.csv',index=False)
    out['planned_split']={'train_n':len(train),'train_policies':train.policy.nunique(),'valid_n':len(valid),'valid_policies':valid.policy.nunique(),
        'cv_sizes':[(len(a),len(b)) for a,b in GroupKFold(4).split(train,groups=train.policy)],'seed':20261001}
    # 100-cycle landmark is complete; no learned processing or predictive evaluation.
    assert len(cells)==139 and len(labeled)==129 and len(primary)==36
    assert all(cells.has_100_cycles)
    (OUT/'analysis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
