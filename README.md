# Hotel Bar Inventory Forecasting & Par Level Recommendation

Forecasts daily consumption per **Bar x Brand** from bottle-balance logs, converts forecasts into **dynamic par levels**
(`Par = forecast demand over lead time + Z x sigma x sqrt(L)`), and back-tests the policy against static par levels
(stockouts, lost volume in ml, average holding stock, turnover).

## Project structure
```
bar_inventory_project/
├── data/raw/bar_inventory_data.csv            <- assignment dataset (converted from the supplied PDF)
├── data/raw/pdf_to_csv.py                     <- reproducible PDF -> CSV conversion (needs poppler's pdftotext)
├── data/processed/daily_bar_consumption.csv   <- generated: daily consumption per bar/brand (with zero days)
├── notebooks/inventory_forecasting_solution.ipynb   <- main deliverable (EDA -> forecasting -> par -> simulation)
├── report/business_report.pdf                 <- generated: 1-2 page managerial summary
├── report/figures/, report/tables/            <- generated plots and result tables (CSV)
├── video_script/video_walkthrough_outline.md  <- generated: 3-5 min video outline + script
├── requirements.txt
└── README.md
```

## Data note
The dataset was supplied as a 178-page Google-Sheets PDF (6,575 rows, 6 bars, 16 brands, 2023-01-01 to 2024-01-01). `data/raw/pdf_to_csv.py` converts it to CSV.
The PDF printed 234 balance cells in rounded scientific notation (3 significant digits) and ~2,000 floating-point residuals (~1e-13); these were reconstructed
**exactly** from the conservation chain (`Closing = Opening + Purchase - Consumed`, `Opening = previous Closing`) using the exactly printed `Purchase`/`Consumed`.
After repair, the conservation equation holds on 100% of rows.

## Setup and run (macOS terminal)
```bash
cd bar_inventory_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# the dataset is already in data/raw/bar_inventory_data.csv, then either:
jupyter lab                      # open notebooks/inventory_forecasting_solution.ipynb -> Restart & Run All
# or run headless:
cd notebooks && jupyter nbconvert --to notebook --execute inventory_forecasting_solution.ipynb --inplace
```
The last notebook cells write the PDF report, the video outline and the results block below from the same numbers.
All settings (lead time, service level, split, bottle size, unit conversion) are in the **config cell** at the top of the notebook.

## Method in one paragraph
Clean and validate logs (timestamps, duplicates, conservation equation `Closing = Opening + Purchase - Consumed`) -> daily grid per observed
bar-brand with explicit zero days -> EDA (ABC velocity, weekday seasonality, stockout audit) -> strict temporal 80/20 split ->
baselines (naive seasonal, moving averages, same-weekday average), Holt-Winters, linear regression and random forest scored on MAE / RMSE / WAPE
(next day and lead-time demand) -> par level from the lead-time forecast plus safety stock from rolling forecast-error RMSE -> vectorised daily
simulation (validated against the reference loop in the brief) comparing static and dynamic par -> sensitivity to lead time and service level.

## Key assumptions
Constant lead time (default 2 days), lost sales (no backorders), quantities in ml (a bottle = 750 ml is assumed; par is kept in ml),
order-up-to par with daily review, initial stock = par. Because 84% of series-days have zero demand, the safety factor Z is **calibrated on the training window**
(target: serve 95% of demand events) instead of assuming normal errors; the textbook Z = 1.645 is reported for comparison. If the dataset has a property/hotel column or
different units, adjust `SERIES_KEYS` / `UNIT_TO_ML` in the config cell.

<!-- RESULTS:START -->
**Auto-generated from the last notebook run** (2023-01-01 to 2024-01-01, back-test 2023-10-20 onward, L=2 d, 95% service level)

| Metric | Value |
|---|---|
| Best forecaster (lead-time-demand RMSE) | Linear regression (205 ml) |
| Baseline (7-day MA) lead-time-demand RMSE | 230 ml |
| Stockout days: dynamic vs static par at equal average stock | 62 vs 59 (+5%) |
| Average stock: dynamic (order-up-to) vs recorded history | 72 L vs 270 L (-73%) |
| Recommended policy (dynamic, calibrated Z 3.59, 1-bottle min. order): stockout days vs recorded history | 19 vs 41 |
| Recommended policy: average stock vs recorded history | 108 L vs 270 L (-60%) |
| Demand events served / fill rate (dynamic 95%, calibrated Z 3.59) | 94.5% / 97.2% |
| Textbook Z 1.645: demand events served | 63.7% |
<!-- RESULTS:END -->
