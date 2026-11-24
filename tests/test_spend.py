import pandas as pd

from analyze import monthly_spend


def test_monthly_spend_handles_zero_months_and_nans():
    df = pd.DataFrame({
        "MoneyForLearning": [120.0, 60.0, None],
        "MonthsProgramming": [0, 6, 3],
        "CountryLive": ["A", "B", "C"],
    })
    out = monthly_spend(df)
    assert len(out) == 2                      # the NaN row is dropped
    assert out["spend_per_month"].iloc[0] == 120.0   # 0 months treated as 1
    assert out["spend_per_month"].iloc[1] == 10.0


def test_conversion_and_bootstrap_ci():
    from price_points import conversion_table, median_ci
    d = pd.DataFrame({
        "CountryLive": ["X"] * 40,
        "spend_per_month": [0] * 20 + [15] * 10 + [40] * 10,
    })
    table = conversion_table(d, prices=[10, 30], focus=["X"])
    assert table["X"]["$10"] == 0.5
    assert table["X"]["$30"] == 0.25
    med, lo, hi = median_ci(d["spend_per_month"].to_numpy(), n_boot=500)
    assert lo <= med <= hi

import numpy as np
import pytest
from analyze import select, summarize, threshold_stats, sensitivity, median_ci
from audit import run, demo_raw


def frame(rows):
    return pd.DataFrame(rows,columns=['JobRoleInterest','CountryLive','MoneyForLearning','MonthsProgramming'])


def test_selection_and_blank_country():
    d=select(frame([('web developer',' A ',2,1),('Mobile Developer',' ',2,1),('Data Scientist','B',2,1),(None,'A',2,1)]))
    assert len(d)==2 and d.CountryLive.iloc[0]=='A' and pd.isna(d.CountryLive.iloc[1])


def test_missing_schema():
    with pytest.raises(ValueError,match='Missing columns'): select(pd.DataFrame())


def test_invalid_and_zero_spend():
    d=frame([('Web Developer','A',0,2),('Web Developer','A',-1,2),('Web Developer','A',10,-1),('Web Developer','A',float('inf'),1),('Web Developer','A','bad',1)])
    assert monthly_spend(d).spend_per_month.tolist()==[0]


def test_zero_month_sensitivity():
    d=frame([('Web Developer','A',100,0)])
    assert monthly_spend(d,.5).spend_per_month.tolist()==[200]
    with pytest.raises(ValueError): monthly_spend(d,0)


def test_threshold_equality_and_bounds():
    s=threshold_stats([0,20,30],5,20)
    assert s['count_at_least']==2 and s['complete_case_share']==pytest.approx(2/3)
    assert s['all_known_country_bounds']==[.4,.8]


def test_all_missing_threshold():
    assert threshold_stats([],4,20)=={'count_at_least':0,'complete_case_share':None,'all_known_country_bounds':[0.,1.]}


def test_invalid_threshold_inputs():
    for x,n,p in [([1,2],1,2),([-1],1,2),([1],1,0),([np.nan],1,2)]:
        with pytest.raises(ValueError): threshold_stats(x,n,p)


def test_delete_vs_cap():
    s=sensitivity([0,100,1000],[500])['500']
    assert s=={'deleted':1,'trimmed_mean':50.,'winsorised_mean':200.}


def test_all_deleted_is_not_zero():
    assert sensitivity([900],[500])['500']['trimmed_mean'] is None


def test_denominators_and_consistency():
    d=select(frame([('Web Developer','A',100,1),('Web Developer','A',None,1),('Web Developer','A',0,1),('Web Developer','B',1000,1),('Web Developer',None,1,1)]))
    r=summarize(d,n_boot=10); a=r['markets']['A']; b=r['markets']['B']
    assert r['eligible_n']==5 and r['known_country_n']==4 and r['valid_spend_n']==3
    assert a['share_of_eligible_known_country']==.75 and a['valid_spend_n']==2
    assert a['price_thresholds']['$59']['complete_case_share']==.5
    assert b['price_thresholds']['$59']['complete_case_share']==1
    assert b['cap_sensitivity']['500']['deleted']==1


def test_empty_country_kept():
    d=select(frame([('Web Developer','A',None,1),('Web Developer','B',2,1)]))
    r=summarize(d,n_boot=10)
    assert list(r['markets'])==['A','B'] and r['markets']['A']['mean'] is None


def test_no_known_country_fails():
    with pytest.raises(ValueError): summarize(select(frame([('Web Developer',None,2,1)])))


def test_bootstrap_all_zero_and_reproducibility():
    assert median_ci([0]*10,n_boot=20)==(0,0,0)
    assert median_ci([0,1,2,3],n_boot=30)==median_ci([0,1,2,3],n_boot=30)
    with pytest.raises(ValueError): median_ci([])


def test_synthetic_deterministic():
    pd.testing.assert_frame_equal(demo_raw(),demo_raw())


def test_repeated_audit_truth():
    r=run(10)
    assert r['bounds_contain_truth']==10 and r['rank_reversal_raw_A_trimmed_B']==10
    assert r['complete_case_minus_truth']['median']<0
