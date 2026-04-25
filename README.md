# Predictive Maintenance for Industrial Machines

A machine learning system that predicts machine failures from real-time sensor readings, deployed as an interactive Streamlit dashboard.

Built end-to-end as a hands-on portfolio project: data exploration → preprocessing → model training → evaluation → deployment.

## Live demo

🔗 *Link will be added after Day 10 deployment*

## Screenshot

*(Add a screenshot here on Day 10)*

## Problem

Industrial machines fail unpredictably. Unplanned downtime is expensive — both in repair costs and lost production. The goal of predictive maintenance is to **catch failures before they happen** by spotting patterns in sensor readings (temperature, torque, rotational speed, tool wear).

## Dataset

**AI4I 2020 Predictive Maintenance Dataset** (UCI Machine Learning Repository) — 10,000 simulated machine readings with the following features:
- Type (L / M / H quality)
- Air temperature
- Process temperature
- Rotational speed
- Torque
- Tool wear
- Failure label (binary: 0 = healthy, 1 = failed)

Class distribution: ~96.6% healthy, ~3.4% failed (heavily imbalanced).

## Approach

1. **EDA** — explored feature distributions and identified that torque, rotational speed, and tool wear are the strongest failure predictors
2. **Preprocessing** — dropped target-leakage columns, one-hot encoded the Type column, performed a stratified 80/20 train/test split, scaled numeric features with `StandardScaler` (fit on train only)
3. **Baseline model** — Logistic Regression with threshold tuning (best F1 = 0.46)
4. **Improved model** — Random Forest with `class_weight="balanced"` (best F1 = 0.64) — selected as the production model

## Results (test set, 2,000 machines, 68 real failures)

| Metric | Logistic Regression (best) | Random Forest (selected) |
|---|---|---|
| Precision | 45.7% | **56.2%** |
| Recall | 47.1% | **73.5%** |
| F1 | 46.4% | **63.7%** |
| Failures caught | 32 / 68 | **50 / 68** |

The Random Forest catches **3 out of every 4 real failures** while keeping false alarms manageable — a strong baseline for predictive maintenance where missed failures are far costlier than false alarms.

### Top features driving predictions

| Rank | Feature | Importance |
|---|---|---|
| 1 | Torque | 31.5% |
| 2 | Rotational speed | 30.0% |
| 3 | Tool wear | 20.9% |
| 4 | Air temperature | 9.7% |
| 5 | Process temperature | 6.4% |

These three operational features together account for **82% of the model's predictive power**.

## Dashboard features

The Streamlit app (`app.py`) provides:

- **Live prediction** — adjust 6 sliders representing real-time sensor readings and watch the model output a failure probability
- **Decision threshold tuning** — calibrated at 0.4 to favor recall over precision (catching more real failures)
- **Domain-aware warnings** — pre-prediction alerts for known failure patterns (high tool wear, overstrain conditions, etc.)
- **Feature importance chart** — shows which features the model relies on most
- **What-if analysis** — compare current operating conditions vs. an adjusted scenario to see if changes would reduce failure risk
- **Sidebar with model card** — performance metrics and usage instructions

## Tech stack

- **Python 3.13**
- **pandas, NumPy** — data manipulation
- **matplotlib, seaborn** — visualization (during EDA)
- **scikit-learn** — preprocessing, modeling, evaluation
- **joblib** — model persistence
- **Streamlit** — dashboard / UI
- **Jupyter** — exploratory notebooks
- **Git / GitHub** — version control

## Project structure
predictive-maintenance/
├── app.py                          # Streamlit dashboard
├── data/
│   └── ai4i2020.csv                # dataset
├── notebooks/
│   ├── day2_python_basics.ipynb    # Python fundamentals
│   ├── day3_data_intro.ipynb       # data loading
│   ├── day4_eda.ipynb              # exploratory analysis
│   ├── day5_preprocessing.ipynb    # cleaning + splits
│   ├── day6_logistic_regression.ipynb
│   └── day7_random_forest.ipynb
├── models/                         # trained artifacts (regenerable)
├── README.md
├── WORKFLOW.md                     # daily dev workflow notes
└── .gitignore

## How to run locally

1. Clone the repository:
git clone https://github.com/<your-username>/predictive-maintenance.git
cd predictive-maintenance

2. Create a virtual environment and install dependencies:
python3 -m venv .venv
source .venv/bin/activate
pip install pandas scikit-learn streamlit matplotlib seaborn jupyter

3. Re-run the notebooks in order (Day 5 → Day 7) to regenerate the model artifacts in `models/` (they're git-ignored).

4. Launch the dashboard:
streamlit run app.py

5. Open `http://localhost:8501` in your browser.

## What I learned

- Why **accuracy is misleading on imbalanced data** and the value of precision, recall, and F1
- How to avoid **target leakage** when selecting features and **data leakage** during preprocessing
- Why **stratified splits** matter for class-imbalanced problems
- The trade-off between **precision and recall** and how to tune the decision threshold
- How **tree-based ensembles** capture non-linear patterns that linear models miss
- How to package an ML model into a usable, interactive product

## Author

**Shivansh Shukla**
- Email: shiva.wdm3d@gmail.com
- GitHub: [shivanshukla001]
- Built April 2026