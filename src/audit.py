"""Controlled experiments: sensitivity to tails and selective missingness."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from analyze import threshold_stats, sensitivity, ROOT


def demo_raw(seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for name,n,p in [('Synthetic A',600,.4),('Synthetic B',300,.5),('Synthetic C',180,.25)]:
        for _ in range(n):
            months = int(rng.integers(0,25))
            spend = float(rng.lognormal(3,1)) if rng.random()<p else 0.
            money = spend*max(months,1)
            if rng.random()<.15: money = np.nan
            rows.append(('Front-End Web Developer',name,money,months))
    return pd.DataFrame(rows,columns=['JobRoleInterest','CountryLive','MoneyForLearning','MonthsProgramming'])


def run(n_worlds=100, seed=2026):
    if n_worlds<1: raise ValueError('positive world count required')
    rng = np.random.default_rng(seed)
    results = []
    for _ in range(n_worlds):
        # A mostly low spend but rare legitimate high spend; B moderate spend.
        a = rng.choice([0.,20.,1000.],size=500,p=[.6,.32,.08])
        b = rng.choice([0.,80.],size=500,p=[.5,.5])
        raw = a.mean()-b.mean()
        trimmed = sensitivity(a,[500])['500']['trimmed_mean']-sensitivity(b,[500])['500']['trimmed_mean']
        winsor = sensitivity(a,[500])['500']['winsorised_mean']-sensitivity(b,[500])['500']['winsorised_mean']
        # Selectively missing high spend in A; known full realised threshold truth.
        truth = float((a>=20).mean())
        observed = a[rng.random(len(a)) < np.where(a>=20,.4,.9)]
        s = threshold_stats(observed,len(a),20)
        cc = s['complete_case_share']
        lo,hi = s['all_known_country_bounds']
        results.append({'raw_gap':float(raw),'trimmed_gap':float(trimmed),'winsorised_gap':float(winsor),
                        'true_threshold_share':truth,'complete_case_share':cc,
                        'complete_case_error':cc-truth,'bounds_lower':lo,'bounds_upper':hi,
                        'bounds_contain_truth':bool(lo<=truth<=hi)})
    def summary(key):
        q=np.quantile([r[key] for r in results],[.05,.5,.95]); return dict(zip(['p05','median','p95'],map(float,q)))
    return {'provenance':'controlled synthetic populations, not FCC survey evidence', 'seed':seed,'worlds':n_worlds,
            'raw_A_higher':sum(r['raw_gap']>0 for r in results),
            'trimmed_B_higher':sum(r['trimmed_gap']<0 for r in results),
            'rank_reversal_raw_A_trimmed_B':sum(r['raw_gap']>0 and r['trimmed_gap']<0 for r in results),
            'rank_reversal_raw_A_winsor_B':sum(r['raw_gap']>0 and r['winsorised_gap']<0 for r in results),
            'raw_A_minus_B':summary('raw_gap'),'trimmed_A_minus_B':summary('trimmed_gap'),
            'winsorised_A_minus_B':summary('winsorised_gap'),
            'complete_case_minus_truth':summary('complete_case_error'),
            'bounds_contain_truth':sum(r['bounds_contain_truth'] for r in results),
            'world_results':results}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--worlds',type=int,default=100); p.add_argument('--seed',type=int,default=2026)
    p.add_argument('--output',type=Path,default=ROOT/'reports'/'known_truth_audit.json'); a=p.parse_args()
    r=run(a.worlds,a.seed); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2,allow_nan=False)); print(json.dumps({k:v for k,v in r.items() if k!='world_results'},indent=2))
