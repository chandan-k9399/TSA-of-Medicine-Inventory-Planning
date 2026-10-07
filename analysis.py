"""Weekly demand forecasting and inventory planning for medical items (COVID-19 period).

Usage:  python analysis.py
Input:  data/medical_dataset.csv
Output: results.json (forecasts, model metrics, safety stock, reorder points) and a printed summary.
"""
import json
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")

DATA_PATH = "data/medical_dataset.csv"
HOLDOUT = 12                      # weeks kept aside for testing
Z = 1.645                         # 95% service level
LEAD_TIMES = {"normal": 1, "delayed": 2}   # weeks (assumption: not in the dataset)
CONTEXT_COLS = ["Government_Regulations", "Market_Trends", "Weather_Conditions", "Supply_Chain_Info"]


def load_weekly(path):
    df = pd.read_csv(path).dropna()
    df["Date"] = pd.to_datetime(df["Date"])
    weekly = df.set_index("Date").groupby("Medical_Item").Demand.resample("W").sum().unstack(0)
    return df, weekly.iloc[1:-1]   # drop partial first and last weeks


MODELS = {
    "Naive": lambda x: np.repeat(x[-1], HOLDOUT),
    "MovAvg(4)": lambda x: np.repeat(x[-4:].mean(), HOLDOUT),
    "SES": lambda x: SimpleExpSmoothing(x, initialization_method="estimated").fit().forecast(HOLDOUT),
    "Holt": lambda x: ExponentialSmoothing(
        x, trend="add", damped_trend=True, initialization_method="estimated").fit().forecast(HOLDOUT),
    "ARIMA(1,1,1)": lambda x: ARIMA(x, order=(1, 1, 1)).fit().forecast(HOLDOUT),
}


def scores(actual, pred):
    err = actual - pred
    return {"MAE": float(np.mean(abs(err))), "RMSE": float(np.sqrt(np.mean(err ** 2))),
            "MAPE": float(np.mean(abs(err) / actual) * 100)}


def analyse_item(series, years):
    s = series.values.astype(float)
    train, test = s[:-HOLDOUT], s[-HOLDOUT:]
    metrics = {name: scores(test, np.asarray(fn(train))) for name, fn in MODELS.items()}
    best = min(metrics, key=lambda k: metrics[k]["MAPE"])
    future = np.asarray(MODELS[best](s))            # refit best model on all data
    mu, sigma = float(future.mean()), metrics[best]["RMSE"]
    inventory = {}
    for label, lead in LEAD_TIMES.items():
        ss = Z * sigma * np.sqrt(lead)
        inventory[label] = {"lead_weeks": lead, "safety_stock": ss, "reorder_point": mu * lead + ss}
    return {
        "actual": s.tolist(), "future": future.tolist(), "best": best, "metrics": metrics,
        "mu": mu, "sigma": sigma, "inventory": inventory,
        "adf_p": float(adfuller(s)[1]), "adf_p_differenced": float(adfuller(np.diff(s))[1]),
        "uplift_2020_vs_2019_pct": float((s[years == 2020].mean() / s[years == 2019].mean() - 1) * 100),
    }


def main():
    df, weekly = load_weekly(DATA_PATH)
    years = weekly.index.year.values
    results = {"weeks": [d.strftime("%Y-%m-%d") for d in weekly.index], "items": {}}
    for item in weekly.columns:
        results["items"][item] = analyse_item(weekly[item], years)
    results["context_anova_p"] = {
        c: float(stats.f_oneway(*[g.Demand.values for _, g in df.groupby(c)])[1]) for c in CONTEXT_COLS}
    with open("results.json", "w") as f:
        json.dump(results, f)

    print(f"{len(df):,} clean records | {len(weekly)} weekly points per item\n")
    print(f"{'Item':22}{'Best model':14}{'MAPE':>7}{'Fcst/wk':>10}{'SS(2wk)':>10}{'ROP(2wk)':>11}")
    for item, r in results["items"].items():
        d = r["inventory"]["delayed"]
        print(f"{item:22}{r['best']:14}{r['metrics'][r['best']]['MAPE']:>6.1f}%{r['mu']:>10,.0f}"
              f"{d['safety_stock']:>10,.0f}{d['reorder_point']:>11,.0f}")


if __name__ == "__main__":
    main()
