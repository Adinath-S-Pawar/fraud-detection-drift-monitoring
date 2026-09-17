# Fraud Detection & Automated Drift Monitoring

An end-to-end ML system for credit application fraud detection, with automated
data drift monitoring, explainability, and a human-in-the-loop retraining
workflow.

**Live demo:** [dashboard](https://fraud-detection-drift-monitoring-ebon.vercel.app) 
---

## The Idea

A fraud detection model doesn't stay accurate forever. The data it sees in
production drifts away from what it was trained on — new fraud patterns
emerge, user behavior shifts, upstream systems change. This project builds
a complete pipeline around that reality: not just a model that predicts
fraud, but a system that **notices when it can no longer trust its own
predictions**, tells someone, and gives them what they need to decide
whether to retrain.

The pipeline:

```
Transaction → FastAPI /predict → XGBoost model → fraud probability
                    ↓
              logged to SQLite
                    ↓
   Scheduled/manual drift check (Evidently AI)
   compares live traffic against training distribution
                    ↓
        Drift above threshold → Slack alert
                    ↓
     Developer reviews → retrains → compares versions
                    ↓
          Manually promotes new model → back to top
```

Every prediction can also be explained via SHAP, on demand, in a live
dashboard.

## Why this dataset

Most portfolio "drift detection" projects inject synthetic noise into a
static dataset to fake a drift signal. This project uses the
[Bank Account Fraud (BAF) Suite](https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022)
(NeurIPS 2022) instead — six datasets (`Base` + `Variant I`–`V`), each with
1 million rows and the same ~1.1% fraud rate, but **genuinely different
underlying feature distributions**, built by researchers specifically to
study realistic distribution shift and fairness in fraud models.

Training on `Base` and streaming `Variant I`–`V` as simulated "live
traffic" produces real, measurable drift, not a synthetic stand-in for it.

## Architecture

| Layer | Tech | Role |
|---|---|---|
| Model | XGBoost, tuned via Optuna | Fraud probability per transaction |
| Explainability | SHAP | Per-prediction feature attribution, computed on demand |
| API | FastAPI | `/predict`, `/predictions`, `/drift-status`, `/model-info` |
| Storage | SQLite | Logged predictions (live traffic proxy) |
| Drift detection | Evidently AI | Statistical comparison vs. training distribution |
| Alerting | Slack (Incoming Webhooks) | Notifies when drift crosses threshold |
| Dashboard | React, Vite, Tailwind, Recharts | Live predictions, drift status, SHAP explanations |
| Backend hosting | Render (free tier) | API |
| Frontend hosting | Vercel | Dashboard |

## Key design decisions

**PR-AUC over ROC-AUC as the tuning objective.** With fraud at only ~1.1% of the data, 
ROC-AUC can look great even when the model isn't actually catching much fraud. 
PR-AUC and precision/recall are the honest picture here.

**Retraining is manual, not automatic.** When drift crosses threshold, the
system sends a Slack alert recommending retraining — it does not retrain
or redeploy on its own. A new model version is trained, compared against
the live version on validation metrics, and promoted only by a human
editing a version pointer file. Automating straight from "drift detected"
to "new model live" removes the one check that catches bad training data,
temporary anomalies, or a genuinely worse model — the cost of a silently
bad model going live in fraud detection is high enough that this is a
deliberate choice, not a missing feature.

**SHAP is computed on demand, not on every prediction.** Computing a SHAP
explanation for every logged prediction is wasted work, most predictions
are never individually reviewed. `/predict` returns a fraud probability
immediately; SHAP is computed (and cached) only when a specific
prediction's explanation is requested.

**Drift results below a minimum sample size are flagged as unreliable.**
Evidently runs one statistical test per feature (31 columns). At small
sample sizes, sampling noise alone can push several columns over threshold
even with no real drift — a multiple-comparisons problem. Empirical testing
during development (61 / 311 / 511-row samples of the same variant produced
16 / 5 / 3 flagged columns respectively) showed results stabilize past
roughly 500 rows. The dashboard visibly flags any drift result computed on
fewer than 500 rows as low-confidence rather than presenting it as
equally trustworthy.

**The reference dataset is a 50,000-row sample, not the full 1M-row
`Base.csv`, in production.** The full file is impractical to ship to a
free-tier host. The sample is large enough to be a statistically stable
reference; the code falls back to it automatically when the full file
isn't present, with no behavior change locally.

## Known limitations

- **Precision/recall trade-off.**
  The current model (tuned via 40 Optuna trials) catches under half of actual fraud (~44% recall), and roughly 1 in 7 flagged
  transactions are truly fraudulent (~15% precision) at a 0.5 threshold. This reflects a real trade-off, not a bug: the Optuna search favored recall — catching more fraud — at the cost of more false alarms That's a common, often deliberate choice in fraud detection, since missing real fraud (chargebacks, losses, regulatory exposure) usually costs more than a human reviewing a false alarm.
- **Multiple-comparisons noise in drift detection.**
  Each of the 31 features is tested separately for drift, so with a small sample, a few can look "drifted" just from random chance, not because anything really changed. Testing showed this settling down past roughly 500 rows. A more rigorous fix would first measure how much drift shows up naturally with no real change (by comparing Base against itself), and use that as the baseline instead of a fixed cutoff.
- **Prediction history doesn't survive restarts on Render's free tier.** predictions.db uses SQLite on local disk, which is wiped on every service restart.
- **No full authentication.**
  `/predict` requires a static API key to prevent casual abuse of the free-tier hosting; this is not equivalent to per-user authentication.
- **Drift checks run on demand, not on a recurring schedule.**
  This was a deliberate choice: the dashboard's "Check Now" button triggers a check directly, rather than a background job running automatically.
  
## Project structure

```
├── data/                    # BAF dataset variants (not committed) + reference sample
├── models/                  # Versioned trained artifacts (model, preprocessor, SHAP explainer)
├── notebooks/                # Exploratory data analysis
├── src/
│   ├── config.py            # Paths, constants, versioning
│   ├── data.py               # Loading, preprocessing, missing-value handling
│   ├── train.py               # Optuna-tuned XGBoost training + SHAP
│   ├── compare_versions.py    # Side-by-side model version comparison
│   ├── api.py                  # FastAPI service
│   ├── logging_db.py            # SQLite prediction logging
│   ├── drift_report.py          # Evidently drift detection
│   ├── alerting.py               # Slack notifications
│   └── generate_traffic.py        # Simulated live traffic for testing
├── dashboard/                # React frontend
└── requirements.txt
```

## Running locally

```bash
# Create an isolated virtual environment in a folder named venv
python -m venv venv

# Activate it — Windows
venv\Scripts\activate

# Activate it — macOS / Linux
source venv/bin/activate

# Install all required packages into the activated environment
pip install -r requirements.txt
```

1. Download the [BAF Suite](https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022)
   and place `Base.csv` + `Variant I.csv`–`Variant V.csv` in `data/`
2. Train the model:
   ```bash
   python -m src.train v1
   ```
3. Set the live version:
   ```bash
   python -c "from src import config; open(config.CURRENT_VERSION_FILE, 'w').write('v1')"
   ```
4. Add a `.env` file:
   ```
   SLACK_WEBHOOK_URL=<your webhook URL>
   ADMIN_API_KEY=<a password of your choice>
   ```
5. Run the API:
   ```bash
   python -m src.api
   ```
6. Run the dashboard:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
7. Generate test traffic:
   ```bash
   python -m src.generate_traffic "Variant I.csv" 500
   ```
8. Check for drift:
   ```bash
   python -m src.drift_report
   ```

