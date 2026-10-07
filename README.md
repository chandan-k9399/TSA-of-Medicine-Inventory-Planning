# Medicine Inventory & Supply-Chain Planning Dashboard

An interactive dashboard that forecasts weekly demand for five medical items during the COVID-19 period (2019-2020) and turns the forecasts into **safety stock** and **reorder-point** recommendations.

Built for the **Time Series Analysis (TSA)** course, Activity 2: *Inventory and supply-chain planning*.

**Live demo:** _add your GitHub Pages link here_

---

## What the dashboard shows

| Section | What it tells you |
|---|---|
| **Controls** | Choose the item, the supplier lead time (1 week normal / 2 weeks delayed) and the service level (90 / 95 / 97.5 / 99%) |
| **KPI cards** | Forecast units per week, 2020 vs 2019 growth, best model, test error (MAPE), safety stock, reorder point |
| **Demand chart** | Two years of actual weekly demand (Jan 2019 - Dec 2020) plus a 12-week forecast |
| **Model comparison** | Test error (MAPE) of the five models; the winner is highlighted |
| **Reorder-point chart** | Each item's reorder point split into expected demand during lead time and safety stock |
| **Inventory table** | Forecast, safety stock, reorder point, best model and MAPE for all items |

Everything recalculates instantly in the browser when you change a control.

## Dataset

- File: `medical_dataset.csv` (daily records of demand for medical items)
- Items: Surgical Mask, Hand Sanitizer, Thermometer, Paracetamol Tablets, Antibiotic Capsules
- Period: January 2019 - December 2020
- 38,764 clean records (1 blank row removed), aggregated into **103 weekly points per item** (partial first and last weeks dropped)
- Fields used: date, medical item, demand. The context fields (government regulation, market trend, weather, supply-chain status) were tested but had no significant effect on demand (ANOVA, all p > 0.05)

> The dataset has **no stock-level, cost or lead-time columns**, so stock figures are derived from forecasts and assumed lead times.

## Methodology

1. Aggregate daily demand into weekly totals per item.
2. Test stationarity with the Augmented Dickey-Fuller (ADF) test.
3. Split chronologically: **first 91 weeks for training, last 12 weeks for testing**.
4. Fit five models and compare them on MAE, RMSE and MAPE:
   - Naive (repeat the last value)
   - 4-week moving average
   - Simple exponential smoothing (SES)
   - Holt's method with damped trend
   - ARIMA(1,1,1)
5. Pick the model with the lowest test MAPE for each item, refit it on all data and forecast the next 12 weeks.
6. Use the forecast and its test RMSE to compute inventory parameters.

### Inventory formulas

```
Safety stock  = z x RMSE x sqrt(lead time in weeks)
Reorder point = forecast per week x lead time + safety stock
```

`z` is 1.282 / 1.645 / 1.960 / 2.326 for 90 / 95 / 97.5 / 99% service level.

## Key results

Default view: 95% service level, 2-week (delayed) lead time.

| Item | Forecast / week | Best model | Test MAPE | Safety stock | Reorder point |
|---|---|---|---|---|---|
| Antibiotic Capsules | 40,831 | MovAvg(4) | 17.1% | 22,511 | 104,174 |
| Hand Sanitizer | 90,723 | MovAvg(4) | 11.5% | 28,898 | 210,343 |
| Paracetamol Tablets | 50,640 | ARIMA(1,1,1) | 14.3% | 19,356 | 120,636 |
| Surgical Mask | 133,938 | MovAvg(4) | 12.2% | 47,634 | 315,509 |
| Thermometer | 100,753 | Holt (damped) | 8.4% | 26,681 | 228,188 |

- Average weekly demand rose roughly **10-13% in 2020** versus 2019 for every item.
- The naive baseline was the worst model for every item.
- Simple smoothing models beat ARIMA for four of five items; the data is mostly a level plus noise, with no reliable seasonal pattern.

## Assumptions and limitations

- **Lead times are assumed** (1 week normal, 2 weeks delayed); they are not in the dataset.
- Only two years of data, so yearly seasonality cannot be estimated and the forecasts are flat.
- No stock or cost data, so no EOQ or measured stockout rate.
- The model was selected and its error measured on the same 12 test weeks, so error estimates are slightly optimistic.
- ARIMA used a fixed (1,1,1) order for all items and was not tuned.
- The per-record demand values look synthetic (evenly spread between 800 and 1,499), so results illustrate the method rather than real-world supply conditions.

## Run it

The dashboard is a single self-contained HTML file.

1. Download `inventory_dashboard.html`.
2. Open it in any modern browser. An internet connection is needed because Chart.js loads from a CDN.

**Host on GitHub Pages:** rename the file to `index.html`, push it, then enable *Settings > Pages > Deploy from branch*.

## Tech stack

- Analysis: Python (pandas, statsmodels, SciPy)
- Dashboard: HTML, CSS, JavaScript and [Chart.js](https://www.chartjs.org/) 4.4.1
- Presentation: PowerPoint (`TSA_Inventory_Supply_Chain.pptx`)

## Repository contents

```
inventory_dashboard.html          Interactive dashboard
Presentation slides
medical_dataset.csv               Source data (add if sharing is allowed)
README.md
```
