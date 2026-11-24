"""Descriptive survey screening, not conversion or market-size estimation."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ['JobRoleInterest', 'CountryLive', 'MoneyForLearning', 'MonthsProgramming']
PRICES = (10, 20, 30, 59)
CAPS = (100, 250, 500, 1000)


def load(path):
    return select(pd.read_csv(path, low_memory=False))


def select(raw):
    missing = set(COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    mask = raw.JobRoleInterest.astype('string').str.contains(
        r'Web Developer|Mobile Developer', case=False, regex=True, na=False)
    d = raw.loc[mask, COLUMNS].copy()
    d['CountryLive'] = d.CountryLive.astype('string').str.strip().replace('', pd.NA)
    return d


def monthly_spend(df, zero_months=1):
    """Return valid complete cases; zero-month convention is configurable."""
    if not np.isfinite(zero_months) or zero_months <= 0:
        raise ValueError('zero_months must be positive and finite')
    d = df.copy()
    d['CountryLive'] = d.CountryLive.astype('string').str.strip().replace('', pd.NA)
    money = pd.to_numeric(d.MoneyForLearning, errors='coerce')
    months = pd.to_numeric(d.MonthsProgramming, errors='coerce')
    valid = (d.CountryLive.notna() & np.isfinite(money) & np.isfinite(months)
             & (money >= 0) & (months >= 0))
    d = d.loc[valid].copy()
    d['spend_per_month'] = money[valid] / months[valid].replace(0, zero_months)
    return d.loc[np.isfinite(d.spend_per_month)].copy()


def values_checked(values):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all() or (x < 0).any():
        raise ValueError('Expected nonempty finite nonnegative one-dimensional spend')
    return x


def median_ci(values, n_boot=2000, seed=0, level=.95):
    x = values_checked(values)
    if not isinstance(n_boot, int) or n_boot < 1 or not 0 < level < 1:
        raise ValueError('Invalid bootstrap settings')
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(x, size=len(x))) for _ in range(n_boot)]
    lo, hi = np.quantile(meds, [(1-level)/2, (1+level)/2])
    return float(np.median(x)), float(lo), float(hi)


def threshold_stats(values, total, price):
    """Complete-case threshold share and worst-case missing-data bounds."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all() or (x < 0).any():
        raise ValueError('Invalid spend')
    if not isinstance(total, (int, np.integer)) or total < len(x) or total < 1:
        raise ValueError('Invalid denominator')
    if not np.isfinite(price) or price <= 0:
        raise ValueError('Price must be positive and finite')
    k = int(np.sum(x >= price))
    return {'count_at_least': k, 'complete_case_share': k/len(x) if len(x) else None,
            'all_known_country_bounds': [k/total, (k+total-len(x))/total]}


def sensitivity(values, caps=CAPS):
    x = values_checked(values)
    out = {}
    for cap in caps:
        if not np.isfinite(cap) or cap <= 0:
            raise ValueError('Invalid cap')
        y = x[x <= cap]
        out[str(cap)] = {'deleted': int(len(x)-len(y)),
                         'trimmed_mean': float(y.mean()) if len(y) else None,
                         'winsorised_mean': float(np.minimum(x, cap).mean())}
    return out


def summarize(eligible, top_n=4, prices=PRICES, n_boot=2000, seed=0):
    if top_n < 1:
        raise ValueError('top_n must be positive')
    counts = eligible.CountryLive.value_counts().sort_index().sort_values(ascending=False, kind='stable')
    known = int(counts.sum())
    if not known:
        raise ValueError('No eligible respondents with known country')
    d = monthly_spend(eligible)
    alternative = monthly_spend(eligible, zero_months=.5)
    markets = {}
    for c, n in counts.head(top_n).items():
        n = int(n)
        group = d[d.CountryLive == c]
        x = group.spend_per_month.to_numpy()
        y = alternative.loc[alternative.CountryLive == c, 'spend_per_month'].to_numpy()
        markets[str(c)] = {'eligible_known_country_n': n,
            'share_of_eligible_known_country': n/known,
            'valid_spend_n': len(x), 'invalid_or_missing_spend_n': n-len(x),
            'zero_month_n_valid': int((pd.to_numeric(group.MonthsProgramming)==0).sum()),
            'mean': float(x.mean()) if len(x) else None,
            'median': float(np.median(x)) if len(x) else None,
            'zero_spend_share': float((x==0).mean()) if len(x) else None,
            'median_bootstrap_interval': list(median_ci(x, n_boot, seed)[1:]) if len(x) else None,
            'cap_sensitivity': sensitivity(x) if len(x) else {},
            'zero_month_half_month_mean': float(y.mean()) if len(y) else None,
            'price_thresholds': {f'${p}': threshold_stats(x,n,p) for p in prices}}
    return {'eligible_n': len(eligible), 'known_country_n': known,
            'missing_country_n': len(eligible)-known, 'valid_spend_n': len(d),
            'selection': 'top countries by eligible known-country respondent count; ties alphabetical',
            'screening_only': True, 'markets': markets,
            'note': 'Historical expenditure proxy, not willingness to pay, conversion, TAM or ROI. Bootstrap intervals conditional on observed complete cases; missingness bounds are not confidence intervals.'}


def plot_spend(eligible, report, path):
    d = monthly_spend(eligible)
    fig, ax = plt.subplots(figsize=(8,5))
    # Right-continuous empirical CDF with zero mass and exact steps.
    for c in report['markets']:
        x = np.sort(d.loc[d.CountryLive == c, 'spend_per_month'].to_numpy())
        if len(x):
            unique, counts = np.unique(x, return_counts=True)
            ax.step(np.r_[0, unique], np.r_[0, np.cumsum(counts)/len(x)], where='post', label=c)
    ax.set(xlabel='Historical spend proxy (USD/month)', ylabel='Fraction with spend ≤ x',
           title=f"Complete-case spend ECDF (untrimmed) — {report.get('provenance', {}).get('kind', 'unspecified input')}", ylim=(0,1.03))
    ax.set_xscale('symlog', linthresh=10)
    if ax.lines:
        ax.legend()
    ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(path,dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path)
    ap.add_argument('--synthetic', action='store_true')
    ap.add_argument('--output', type=Path, default=None)
    args = ap.parse_args()
    if args.synthetic == (args.data is not None):
        ap.error('Specify exactly one of --data or --synthetic')
    if args.data is not None and args.output is None:
        ap.error('--output is required for real/user-supplied data')
    if args.output is None:
        args.output = ROOT/'reports'/'synthetic_demo'
    if args.synthetic:
        from audit import demo_raw
        raw = demo_raw()
        provenance = {'kind':'synthetic demonstration', 'seed':42}
    else:
        raw = pd.read_csv(args.data, low_memory=False)
        provenance = {'kind':'user-supplied CSV; verify source', 'file':args.data.name,
                      'sha256': hashlib.sha256(args.data.read_bytes()).hexdigest()}
    eligible = select(raw)
    report = summarize(eligible)
    report.update(provenance=provenance, input_rows=len(raw))
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'screening.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    plot_spend(eligible,report,args.output/'spend_ecdf.png')
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
