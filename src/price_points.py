"""Compatibility entry point: emit thresholds from the same untrimmed cohort."""
import argparse
import json
from pathlib import Path
from analyze import load, summarize, median_ci, PRICES, ROOT


def conversion_table(d, prices=PRICES, focus=None):
    """Legacy function name; returns historical threshold shares, not conversion."""
    if focus is None:
        focus = sorted(d.CountryLive.dropna().unique())
    from analyze import threshold_stats
    out = {}
    for country in focus:
        x = d.loc[d.CountryLive == country, 'spend_per_month'].to_numpy()
        if len(x):
            out[country] = {f'${p}': threshold_stats(x,len(x),p)['complete_case_share'] for p in prices}
            out[country]['respondents'] = len(x)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = summarize(load(args.data))
    import hashlib
    out = {'provenance': {'kind':'user-supplied CSV; verify source', 'file':args.data.name,
                         'sha256':hashlib.sha256(args.data.read_bytes()).hexdigest()},
           'markets': {c: {'valid_spend_n':m['valid_spend_n'],
                            'price_thresholds':m['price_thresholds'],
                            'median_bootstrap_interval':m['median_bootstrap_interval']}
                       for c,m in report['markets'].items()}, 'note': report['note']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
