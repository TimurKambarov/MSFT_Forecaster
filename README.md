# MSFT Weekly Direction Forecaster

A machine-learning application that predicts the **weekly** price direction of Microsoft
(MSFT) stock — **UP**, **DOWN**, or **SAME** — and serves the prediction through a
containerised web dashboard.

This is a Year 1 Block D group project (Group 15) for the *Data Science Lifecycle
Management* course at Breda University of Applied Sciences (ADS-AI). It is an academic
prototype, **not financial advice**.

---

## What it does

Each week the model reads market data up to the most recent Friday close and classifies
the direction of MSFT for the **following** week into one of three classes:

| Class | Meaning |
| --- | --- |
| **UP** | Next-week return rises beyond the threshold |
| **DOWN** | Next-week return falls beyond the threshold |
| **SAME** | Next-week return stays within the flat band |

The result is written to a SQLite database and displayed on a Flask + vanilla-JS
dashboard with custom SVG charts.

> **Honest result.** Across the model iterations, test-set performance landed close to
> the majority-class baseline (AUCs near 0.5). Predicting next-week direction from price
> and peer features alone is, on this data, close to a coin flip. The pipeline, the
> dashboard, and the engineering around it are real and reproducible; the predictive
> signal is weak, and we report that rather than hide it. See
> [Results & honest limitations](#results--honest-limitations).

---

## Quick start

### With Docker (recommended)

```bash
docker-compose up --build
```

Then open **http://localhost:5000**.

### Without Docker

```bash
pip install -r dashboard/requirements.txt
python dashboard/server.py
```

Then open **http://localhost:5000**.

### Generate a fresh weekly prediction

Run this **after Friday market close** to score the latest completed week:

```bash
python dashboard/msft_forecaster/predict.py
```

The prediction is written to the SQLite database; the dashboard reads from there, so the
page reflects the latest run on the next request without any manual step.

---

## Repository layout

```
.
├── dashboard/                     # The web application (Task 13)
│   ├── server.py                  # Flask server, serves the dashboard + prediction API
│   ├── setup_db.py                # Initialises the SQLite database
│   ├── requirements.txt           # Runtime deps for the dashboard
│   ├── data/
│   │   ├── raw/                   # Per-ticker raw CSVs (MSFT, NVDA, AMZN, ...)
│   │   └── processed/             # modelling_dataset.csv (merged, model-ready)
│   ├── msft_forecaster/           # The package the app imports
│   │   ├── predict.py             # Generates a weekly prediction → DB
│   │   ├── data/fetch_latest.py   # Pulls the most recent market data
│   │   ├── db/                    # SQLite management (Task 8)
│   │   └── pipeline/
│   │       ├── train_xgboost.py   # Data pipeline + model training (Task 9/10)
│   │       └── models/            # Saved model + metadata
│   │           ├── xgboost_weekly.joblib
│   │           └── xgboost_weekly_metadata.json
│   └── static/                    # index.html, app.js, style.css (frontend)
│
├── datalabtasks_deliverables/     # Course deliverables, one folder per task
│   └── Task 12 Unit Testing and Documentation/
│       ├── test_data_pipeline_xgboost.py
│       └── test_database_management.py
│
├── models/                        # Per-member experiment artifacts (ensemble, etc.)
├── docker-compose.yml             # One-command build + run
├── Dockerfile                     # Container definition
├── pyproject.toml                 # Poetry project + dependency lock
└── poetry.lock
```

---

## How it works

### Data

Raw per-ticker CSVs in `dashboard/data/raw/` are merged into a single model-ready table,
`dashboard/data/processed/modelling_dataset.csv`. The MSFT trading calendar is the
reference index; everything else aligns to it.

The pipeline (`train_xgboost.py`) then:

1. **Loads** the merged dataset and filters to the project date range.
2. **Aligns** to a full daily calendar with trading-day / weekend / holiday flags.
3. **Resamples to weekly bars** anchored on Friday (`W-FRI`) using only trading days —
   MSFT OHLCV aggregates appropriately (price = last, volume = sum), and each peer's
   close/volume is carried in.
4. **Engineers features** (see below) and builds the three-class next-week target.
5. **Fills** any residual gaps (numeric → median, categorical → mode).
6. **Splits time-ordered** (no shuffle) and scales features with a `RobustScaler`
   **fit on the training slice only**, to avoid look-ahead leakage.

### Features

The model uses MSFT-derived technical features plus a small set of **peer-stock**
features for **NVDA** and **AMZN**. For each peer: weekly return, lagged return,
relative strength vs MSFT, and a volume ratio.

### Model

An XGBoost classifier (`num_class = 3`) with hyperparameters tuned via `TimeSeriesSplit`.
The trained model and its metadata (feature list, parameters, metrics) are saved to
`dashboard/msft_forecaster/pipeline/models/`. Earlier iterations
(Logistic Regression → Random Forest → XGBoost → LSTM → stacking ensemble) live under
`models/` as experiment history.

---

## Key design decisions

These are deliberate departures from the original proposal/design document. They are
documented here because the **code reflects these choices, not the earlier plan**.

### Weekly model, not daily — and three classes, not two

- Weekly (`W-FRI`) bars carry far less noise than daily moves.
- Technical indicators such as RSI and MACD are more reliable at the weekly level.
- We classify into **UP / DOWN / SAME** rather than binary UP/DOWN. Genuinely flat weeks
  were previously forced into UP or DOWN, which **inflated accuracy** by rewarding the
  model for arbitrary calls on no-movement weeks. The explicit SAME class removes that
  distortion.

### NVDA + AMZN peer features (Gold, Oil, VIX removed)

- `nvda_rel_strength` is the single most important feature (importance ≈ 0.069). It
  captures whether MSFT is leading or lagging the broader tech sector.
- Gold, crude oil, and VIX showed near-zero feature importance, so they were dropped to
  reduce overfitting.

### Flask + vanilla JS, not Streamlit

The design document specified Streamlit; we changed this deliberately.

- We needed full control over layout, custom SVG charts, and brand styling — none of
  which fit cleanly into Streamlit's widget model.
- Streamlit re-renders the whole app on every interaction. Our Flask + JS approach
  fetches only the data each request needs.

### SQLite for storage

- A single file: no separate database server to run.
- Trivial to copy between machines and to mount as a Docker volume — which keeps the
  whole app portable.

### Colour scheme (three signal colours + background)

| Colour | Hex | Used for | Why |
| --- | --- | --- | --- |
| Blue | `#009FFD` | **UP** | Positive / bullish |
| Amber | `#DBD56E` | **DOWN** | Caution, not alarm — red was avoided so non-professional users don't over-react to a weak signal |
| Navy | `#2A2A72` | **SAME** | Neutral, no directional bias |
| Dark | `#232528` | Background | Reduces eye strain and makes data elements stand out |

---

## Testing

Unit tests cover the deterministic data-pipeline functions (loading, calendar alignment,
weekly resampling, feature engineering, gap-filling, and the time-ordered split/scale).
They pin down the properties that matter — no look-ahead bias, correct class thresholds,
peer-feature synchronisation, and train-only scaler fitting — not just output shapes.

```bash
poetry run pytest "datalabtasks_deliverables/Task 12 Unit Testing and Documentation/" -v
```

To measure coverage:

```bash
poetry run pytest --cov=dashboard/msft_forecaster --cov-report=term-missing
```

> The pipeline test locates `train_xgboost.py` automatically when it sits in the package.
> If you move it, set the `TRAIN_XGBOOST_PATH` environment variable to its path.

---

## Results & honest limitations

The headline finding is a **negative result**, reported as such:

- Test-set AUCs for the tuned models sit close to **0.5** — i.e. close to the
  majority-class baseline. No model meaningfully beats "always predict the majority
  class."
- This is consistent with the **weak-form efficient-market** view: next-period direction
  is very hard to predict from price history and a handful of correlated assets.
- The three-class framing makes the evaluation **more honest**, not more accurate — it
  stops the model from being credited for guessing on flat weeks.

What this project *does* demonstrate well is the **lifecycle engineering**: a reproducible
data pipeline, leakage-safe preprocessing, an iterative modelling progression, a tested
codebase, and a containerised dashboard. The predictive task itself is hard, and we let
the numbers say so.

---

## Tech stack

Python 3.12 · pandas · scikit-learn · XGBoost · SQLite · Flask · vanilla JS · Docker /
Docker Compose · Poetry · pytest.

> **Python version:** use **3.12**. Newer versions (e.g. 3.14) lack wheels for some
> dependencies used in the wider modelling work.

---

## Team — Group 15

| Member | Primary responsibilities |
| --- | --- |
| Gergely Gádor | Scrum Master · methodology · legal compliance (Task 4.2) |
| Lucan den Dekker | Application design (Task 7) · application development (Task 13) |
| Qusai Al Qusaily | Database management (Task 8) |
| Timur Kambarov | Data processing pipelines (Task 9) |

Machine-learning development (Task 10), modular code (Task 11), and unit testing
(Task 12) were shared across all members.

---

## Disclaimer

This application is an academic prototype built for a university course. It does **not**
constitute financial advice, and its predictions are close to random — see
[Results & honest limitations](#results--honest-limitations). Do not use it to make
investment decisions.
