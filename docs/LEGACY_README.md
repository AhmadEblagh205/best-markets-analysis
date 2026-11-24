# Best Markets to Advertise In

[![CI](https://github.com/AhmadEblagh205/best-markets-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/AhmadEblagh205/best-markets-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A business question answered with the freeCodeCamp 2017 New Coder Survey (around 18,000 respondents): if you sell a programming e-learning subscription, which countries should get the advertising budget? I first did this as a guided Dataquest project; this rebuild adds a scripted data download, a distribution-aware view of spend, and a machine readable recommendation with the reasoning attached.

## The analysis

Respondents are filtered to those interested in web or mobile development, which is what the hypothetical product teaches. Demand is located by country of residence, then willingness to pay is sized as money spent on learning divided by months programming, with an outlier trim and both mean and median reported, because a handful of bootcamp fees drags means far above what a typical customer pays. The headline chart is an ECDF of monthly spend by country: the whole distribution on one chart, showing what fraction of each market pays at least any given price, which is exactly the question a subscription price asks.

![Spend ECDF](reports/figures/spend_ecdf.png)

On the real 2017 data the US holds about 45% of interested respondents and the highest spend. The ECDF also shows the catch: in every market most new coders spend close to nothing per month, so medians sit near zero while a paying minority carries the means. The recommendation, written to `reports/recommendation.json`, concentrates budget in the US and treats the runner up markets as a volume versus spend decision.

## Reading prices off the distribution

The roadmap item is delivered in `price_points.py`: for candidate subscription prices (10, 20, 30 and 59 dollars a month) the share of each focus market already spending at least that much, which is the upper bound conversion proxy the ECDF was drawn to answer, plus bootstrap 95 percent confidence intervals on the median spend, so the near zero medians now carry honest uncertainty instead of false precision.

## Usage

```bash
pip install -r requirements.txt
python src/download_data.py
python src/analyze.py
python src/price_points.py
```

## Tests

`pytest` covers the spend per month construction: zero months treated as one, missing values dropped, arithmetic correct. CI runs on push.

## Ideas

Weighting countries by purchasing power rather than raw dollars, and bootstrap intervals on the median spend per market.

## Licence

MIT, see [LICENSE](LICENSE). Data: freeCodeCamp 2017 New Coder Survey.
