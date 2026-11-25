# Survey-Based Market Screening & Spending Sensitivity

This project began as a Dataquest guided project. The code here is my independent rebuild and audit of it. The data source is the [freeCodeCamp 2017 New Coder Survey](https://github.com/freeCodeCamp/2017-new-coder-survey), and the hypothetical product is a course in web and mobile development. It is exploratory survey screening, so I do not treat it as an estimate of market size, conversion or current demand.

## What it does

- Selects respondents whose stated job-role interests match web or mobile development.
- Ranks up to four countries by respondent count among those with a known country of residence.
- Computes a spend proxy, money spent learning divided by months programming, and reports means, medians, an ECDF and shares at $10, $20, $30 and $59.
- Compares deleting and capping large values, and reports worst-case bounds for the threshold shares when spend is missing.
- Runs a simulation with 100 synthetic worlds to show how those choices change the conclusions.

![Synthetic demonstration ECDF](reports/synthetic_demo/spend_ecdf.png)

## Results

The simulation uses synthetic data where the answer is known, not the survey. In each world there are 500 observations per group. Group A has rare large spends and group B has moderate ones.

- The raw mean of A exceeded that of B in 100 of 100 worlds. Deleting values above $500 reversed the ranking in 100 of 100 worlds, and capping at $500 reversed it in 21 of 100.
- The median gap between A and B was $45.96 raw, -$33.12 with deletion and $6.16 with capping.
- When spend was observed more often for small values, the median complete-case threshold error was -16.67 percentage points (5th to 95th percentile: -19.49 to -14.42).
- The worst-case bounds contained the true share in 100 of 100 worlds, which follows from how they are built.

Seeds and world-level output are in `reports/known_truth_audit.json`. The original archive recorded a 45.34% US share of respondents and a trimmed mean spend of $39.73 for the US, against $24.32 for India, $26.22 for the UK and $27.90 for Canada. I keep those under `reports/legacy/` and do not present them as freshly checked. The raw CSV was missing and the download failed during my audit, so I have not rerun the real-data analysis yet and I do not quote a current number for it.

## How to run

```bash
pip install -r requirements.txt pytest
pytest -q
python src/analyze.py --synthetic
python src/audit.py
# Real survey, when network and data are available:
python src/download_data.py
python src/analyze.py --data data/raw/fcc_survey_2017.csv --output reports/real_2017
python src/price_points.py --data data/raw/fcc_survey_2017.csv --output reports/real_2017/price_points.json
```

The tests cover schema, denominators, invalid spend, thresholds, missingness bounds, sensitivity and reproducibility. The original rebuild had 2 passing tests and there are now 17. The download command fails rather than substituting synthetic data.

## Notes

The survey is from 2017, self-selected and a convenience sample. Historical spending is not willingness to pay, so I make no advertising-budget recommendation. Derivations and decisions are in `docs/METHODOLOGY.md`.

## Licence

MIT for the code. The upstream survey terms apply to the data.
