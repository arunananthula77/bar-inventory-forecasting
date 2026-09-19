# Video Walkthrough Outline (target 4:00, within the 3-5 minute brief)

> Numbers below are generated from the notebook run. Read them off the notebook output while recording; speak at ~150 words per minute.

| Time | Section | Talking Points | Visual to Show |
|---|---|---|---|
| 0:00 - 0:45 | **Problem Statement** | Frame the tension: stockouts vs overstocking across multiple bars. | Slide with the business goal and bar landscape (bars, brands, days). |
| 0:45 - 1:45 | **Approach & Modeling** | Explain how raw bottle logs were processed into daily series, feature creation, and model choice. | Notebook: EDA plots (eda_overview.png) and the daily demand chart; model comparison table (forecast_evaluation.png). |
| 1:45 - 3:00 | **Inventory Logic & Simulation** | Walk through the Par Level math (Z x sigma x sqrt(L)) and show the back-test loop results. | Plot showing simulated stock level vs par line over time (stock_vs_par.png); trade-off curve (tradeoff_and_kpis.png). |
| 3:00 - 4:00 | **Business Impact & Scalability** | Summarize the reduction in stockouts, how managers use it daily, and production risks. | Final summary slide / KPI comparison table (simulation_results.csv). |

## 0:00 - 0:45 - Problem Statement
- **Talking points:** Frame the tension: stockouts vs overstocking across multiple bars.
- **Show:** Slide with the business goal and bar landscape (bars, brands, days).
- **Script (~124 words = ~50 s):**

  > Hi, I'm presenting my hotel bar inventory forecasting and par level solution. Bars have two opposite problems. Run out of a popular brand on a Friday night and you lose revenue and disappoint guests. Over-order slow movers and you tie up cash and backroom space, with shrinkage risk. In this data - 6 bars, 16 brands, 366 days - 5,261 bar-brand days ended at zero stock, that is 15.1%, while the median class-C brand held 50.6 days of cover against 29.2 for class A. So stock is not aligned with velocity. My goal: forecast demand for every bar and brand, turn it into a par level that adapts to demand swings, and prove with a back-test that it cuts stockouts without piling up stock.

## 0:45 - 1:45 - Approach & Modeling
- **Talking points:** Explain how raw bottle logs were processed into daily series, feature creation, and model choice.
- **Show:** Notebook: EDA plots (eda_overview.png) and the daily demand chart; model comparison table (forecast_evaluation.png).
- **Script (~182 words = ~73 s):**

  > First the data. The file arrived as a PDF, so I converted it to CSV, repairing balance cells the PDF had rounded. I parsed timestamps and checked the conservation equation - closing equals opening plus purchase minus consumed - which holds on 100.00% of rows. I aggregated to daily consumption per bar and brand with explicit zero days, and that matters: 84% of series-days have no sales, so demand is intermittent. EDA shows a Pareto pattern - 13 class-A brands carry 85% of volume - and no material weekday cycle - the busiest day is only 1.04 times average. I used a strict temporal 80/20 split, never random folds, and compared moving averages, Croston for intermittent demand, Holt-Winters, linear regression and a random forest, with lag, rolling and weekday features built only from information available at the forecast date. Daily WAPE is inflated by all those zeros, so I also report weekly-total WAPE and rank models on the RMSE of lead-time demand, which is what drives safety stock. Linear regression won: 205 ml against 230 for the seven-day moving average, 11% lower.

## 1:45 - 3:00 - Inventory Logic & Simulation
- **Talking points:** Walk through the Par Level math (Z x sigma x sqrt(L)) and show the back-test loop results.
- **Show:** Plot showing simulated stock level vs par line over time (stock_vs_par.png); trade-off curve (tradeoff_and_kpis.png).
- **Script (~223 words = ~89 s):**

  > Now the par level. Par equals forecast demand over the 2-day supplier lead time, plus safety stock: Z times the forecast-error standard deviation times the square root of the lead time. The textbook Z of 1.645 assumes normal errors; with this zero-heavy demand it served only 64% of demand events, so I calibrated Z on the training data: 3.6 for a 95% target. Because demand is intermittent, par is mostly a safety buffer against the next demand event, and it updates every day as the forecast and error estimates move, as you can see in this plot. Par is expressed in ml. To test it I built a daily simulation on the held-out test window: receive arriving orders, serve demand, count anything unserved as lost, and order up to par when inventory position drops below it. I validated my vectorised engine against the reference loop from the brief. Against the recorded history, the calibrated policy with a one-bottle minimum order had 19 stockout days versus 41 while holding 60% less stock. Against a static par held at the same average stock, dynamic par was about the same: 62 versus 59 stockout days - which makes sense, because this demand has no weekly pattern to exploit. The big win is calibrating Z: the textbook value served 64% of demand events, the calibrated one 95%.

## 3:00 - 4:00 - Business Impact & Scalability
- **Talking points:** Summarize the reduction in stockouts, how managers use it daily, and production risks.
- **Show:** Final summary slide / KPI comparison table (simulation_results.csv).
- **Script (~132 words = ~53 s):**

  > The recommended policy - calibrated dynamic par with a one-bottle minimum order - serves 98.3% of demand events with a 99.3% fill rate, and stock turns 18.0 times a year versus 7.2 in the recorded history. It uses 581 orders, against 315 recorded deliveries and 1,966 for the pure order-up-to rule. In production, a nightly job ingests the day's logs, validates them, refreshes forecasts and writes a manager dashboard: on hand, par and recommended order per bar and brand. What can break: supplier lead-time variance, holidays and events, pouring waste, new brands with no history, and demand hidden by stockouts. I would monitor rolling WAPE and bias, data drift and achieved service level. Next steps: an event calendar, a live point-of-sale feed, consolidated weekly deliveries and probabilistic forecasts. Thank you for watching.

**Total script: ~661 words = ~4.4 min at 150 wpm.**

## Recording checklist
- Restart & Run All first so every number and plot on screen matches the report.
- Screen order: slide (problem) -> notebook EDA -> model table -> par formula cell -> simulation plot -> KPI table -> slide (impact).
- Say the assumptions out loud once (constant lead time, lost sales, ml units, order-up-to daily review).
- Mention one honest limitation: model selected on the same test window; production would use rolling-origin validation.
- Keep the video between 3:00 and 5:00.