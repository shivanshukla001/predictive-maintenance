# Learning Notes — Predictive Maintenance Project

A personal reference for what I learned across the 10-day build. This file consolidates the technical concepts, code patterns, and mental models behind the project — what I'd want a future-me (or another beginner) to read first.

---

## Table of Contents

- [Python fundamentals](#python-fundamentals)
- [Pandas and data exploration](#pandas-and-data-exploration)
- [Visualization (matplotlib + seaborn)](#visualization)
- [Preprocessing for ML](#preprocessing-for-ml)
- [Logistic Regression](#logistic-regression)
- [Evaluation metrics](#evaluation-metrics)
- [Random Forest](#random-forest)
- [Streamlit dashboards](#streamlit-dashboards)
- [Deployment to Streamlit Cloud](#deployment)
- [The "why" behind major decisions](#the-why-behind-major-decisions)
- [Common errors I hit and how I fixed them](#common-errors)

---

## Python fundamentals

### Variables and types
Python figures out the type from what you assign:
```python
name = "Hemant"   # str
age = 25          # int
height = 5.9      # float
is_student = True # bool
```

### Lists
Ordered collections, **0-indexed**, slicing is exclusive on the end.
```python
temps = [298, 300, 302, 305]
temps[0]      # 298 (first)
temps[0:3]    # [298, 300, 302] — three items, NOT four
temps.append(310)  # adds to end
```

### Dictionaries
Key-value pairs.
```python
machine = {"id": "M001", "type": "L", "torque": 45}
machine["torque"]   # 45
```

### Conditionals
```python
if torque > 65:
    print("Stressed")
elif torque > 40:
    print("Normal")
else:
    print("Light load")
```

### Loops
```python
for temp in temps:
    print(temp)

for i, temp in enumerate(temps):
    print(f"Reading {i}: {temp}")  # enumerate gives (index, value) pairs
```

### Functions
```python
def get_grade(average):
    if average >= 90: return "A"
    elif average >= 75: return "B"
    else: return "C"

result = get_grade(88)  # Capture the return value!
```
- `return` sends a value back to the caller. Without it, Python returns `None` automatically.
- `print` only displays text; it doesn't return anything useful.

### f-strings
```python
print(f"Torque: {torque:.2f} Nm")  # 2 decimal places
print(f"{percent:+.1f}%")           # forces +/- sign
```

---

## Pandas and data exploration

### Loading
```python
import pandas as pd
df = pd.read_csv("../data/ai4i2020.csv")
```

### Inspecting
```python
df.shape         # (rows, columns)
df.head()        # first 5 rows
df.info()        # column types + missing values
df.describe()    # numeric summary stats
df.columns       # column names
```

### Counting categorical values
```python
df["Machine failure"].value_counts()
# 0    9661
# 1     339   ← only 3.4% failures = imbalanced
```

### Filtering and selecting
```python
df[df["Machine failure"] == 1]      # only failed machines
df[["Torque [Nm]", "Tool wear [min]"]]  # only these columns
```

### Group-by aggregation
```python
df.groupby("Machine failure")[numeric_features].describe()
```

### Correlation
```python
df.corr()  # pairwise correlations between all numeric columns
```

---

## Visualization

### Histogram with class overlay
```python
import seaborn as sns
sns.histplot(
    data=df, x="Torque [Nm]",
    hue="Machine failure",
    bins=30, kde=True,
    stat="density", common_norm=False,   # normalize each class separately
    palette={0: "steelblue", 1: "crimson"}
)
```

Key flags:
- `hue="Machine failure"` — color by class
- `stat="density"` + `common_norm=False` — turn raw counts into proportions; lets you visually compare class distributions even when one class is tiny

### Box plot for outlier comparison
```python
sns.boxplot(data=df, x="Machine failure", y="Torque [Nm]")
```

### Correlation heatmap
```python
sns.heatmap(df.corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0)
```

---

## Preprocessing for ML

### Target leakage — drop columns with future info
The AI4I dataset has columns like `TWF`, `HDF`, `PWF`, `OSF`, `RNF` — these are computed AFTER a failure occurs. Using them to predict failure would be cheating. Always drop columns that are derived from the target.

```python
cols_to_drop = ["UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]
df = df.drop(columns=cols_to_drop)
```

### Separating features (X) from target (y)
```python
X = df.drop(columns=["Machine failure"])   # 6 features
y = df["Machine failure"]                  # the label
```

### One-hot encoding categorical columns
```python
X = pd.get_dummies(X, columns=["Type"], drop_first=True)
```
- ML algorithms need numbers, not text
- `drop_first=True` avoids the **dummy variable trap** — three Type categories produce only 2 binary columns; the third is implicit (when both = 0)

### Stratified train/test split
```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y    # CRITICAL for imbalanced data
)
```
- `stratify=y` preserves the failure rate in both sets — without it, a random split could put all failures in one set
- `random_state=42` makes the split reproducible

### StandardScaler — fit only on train
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # learns mean + std from train
X_test_scaled  = scaler.transform(X_test)        # uses TRAIN's mean + std
```

**The data leakage rule:** never call `fit_transform` on test data. The scaler must learn its statistics from training data only — anything else cheats by giving the model peek-access to the test distribution. This rule applies to every preprocessing step that learns from data (imputers, encoders, feature selectors).

### Saving artifacts with joblib
```python
import joblib
joblib.dump(scaler, "models/scaler.pkl")
loaded = joblib.load("models/scaler.pkl")   # restore later
```

---

## Logistic Regression

### What it does, mathematically
1. Computes a weighted sum: `z = w1*x1 + w2*x2 + ... + bias`
2. Squashes z into 0-1 via the sigmoid: `prob = 1 / (1 + e^-z)`
3. If `prob >= 0.5` predict 1, else 0 (threshold can be changed)

### Training
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_scaled, y_train)
```

### Reading the model
```python
model.coef_         # learned weights (one per feature)
model.intercept_    # the bias
```

Positive weight → higher feature value pushes toward class 1
Negative weight → higher feature value pushes toward class 0

### Important caveat: needs scaled features
Without scaling, features with large numbers (rotational speed ~1500) dominate features with small numbers (torque ~40), regardless of which is actually predictive.

---

## Evaluation metrics

### The accuracy trap on imbalanced data
With 96.6% healthy machines, a model that always predicts "healthy" gets 96.6% accuracy. **Accuracy is dangerous on imbalanced data.**

### Confusion matrix layout (sklearn convention)
|  | Pred 0 (Healthy) | Pred 1 (Failure) |
|---|---|---|
| Actual 0 | True Negative | False Positive (false alarm) |
| Actual 1 | False Negative (missed failure) | True Positive |

### The four core metrics

```
Accuracy  = (TP + TN) / Total
Precision = TP / (TP + FP)   "When I predict failure, am I right?"
Recall    = TP / (TP + FN)   "Of all real failures, how many do I catch?"
F1        = 2 * (Precision * Recall) / (Precision + Recall)
```

### When each metric matters
- **Precision matters when false alarms are expensive** (spam filters — don't want real emails marked spam)
- **Recall matters when missing positives is expensive** (medical screening, predictive maintenance — don't want to miss real cases)
- **F1 balances both** — useful when you can't decide

### Threshold tuning
The default 0.5 threshold isn't sacred. Lowering it makes the model more aggressive about predicting class 1 — recall goes up, precision goes down.

```python
y_pred_proba = model.predict_proba(X_test)[:, 1]
y_pred_custom = (y_pred_proba >= 0.3).astype(int)
```

For predictive maintenance: missing failures > false alarms, so use a low threshold (we used 0.4).

---

## Random Forest

### What it is
- An **ensemble** of many decision trees
- Each tree is trained on a random subset of rows (with replacement → "bagging")
- At each split inside each tree, only a random subset of features is considered
- Final prediction is the majority vote of all trees

### Why it usually beats Logistic Regression
- Captures **non-linear** patterns (e.g., "failure spikes when tool wear > 200" — a linear model can't represent threshold effects)
- Captures **feature interactions** (e.g., "high torque × low quality machine" together)
- The randomness across trees prevents overfitting

### Training
```python
from sklearn.ensemble import RandomForestClassifier

rf_model = RandomForestClassifier(
    n_estimators=200,        # number of trees
    max_depth=10,            # limits tree depth → prevents overfitting
    class_weight="balanced", # auto-handles class imbalance
    random_state=42,
    n_jobs=-1                # use all CPU cores in parallel
)
rf_model.fit(X_train_scaled, y_train)
```

### `class_weight="balanced"` is the magic flag
It internally weights the minority class proportionally higher. For our 3.4% failure rate, failure rows get ~28× more weight when the model decides what to optimize.

### Feature importance
```python
rf_model.feature_importances_   # sums to 1.0
```
Indicates how much each feature contributes to splits across the forest. Higher = more important.

### Doesn't need feature scaling
Trees split on thresholds (e.g., "is torque > 50?"), not distances. Scaling makes no functional difference — but it doesn't hurt either.

---

## Streamlit dashboards

### Skeleton
```python
import streamlit as st

st.set_page_config(page_title="...", page_icon="⚙️", layout="wide")
st.title("My App")
```

### Cache loaded artifacts
```python
@st.cache_resource
def load_artifacts():
    model = joblib.load("models/random_forest_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    return model, scaler

model, scaler = load_artifacts()
```
Without `@st.cache_resource`, the app reloads files from disk on every slider movement.

### Input widgets
```python
st.slider("Torque", min_value=0, max_value=80, value=40, step=0.5)
st.selectbox("Type", options=["L", "M", "H"], index=2)
```
Each widget RETURNS the current value — assign to a variable.

### Layout
```python
col1, col2 = st.columns(2)
with col1:
    # left column content
with col2:
    # right column content
```

### The prediction pipeline
```python
# 1. Build a 1-row DataFrame with the user inputs
input_df = pd.DataFrame([{...}])[feature_names]   # match training column order!

# 2. Scale using the SAME scaler from training
input_scaled = scaler.transform(input_df)

# 3. Predict probability
proba = model.predict_proba(input_scaled)[0, 1]

# 4. Apply the chosen threshold
prediction = 1 if proba >= 0.4 else 0
```

### Display elements
```python
st.success("HEALTHY")     # green box
st.error("FAILURE")        # red box
st.metric("Probability", f"{proba:.2%}", delta="...")
st.progress(float(proba))  # progress bar
st.bar_chart(df.set_index("Feature"))
```

### Sidebar
```python
with st.sidebar:
    st.header("About")
    # everything inside `with` lands in the sidebar
```

---

## Deployment

### What you need on top of your code
1. **`requirements.txt`** — list of pip packages
2. **All model files committed to git** (don't gitignore `.pkl` files for deployment)
3. **A GitHub repo** with everything pushed

### `requirements.txt` format
```
streamlit
pandas
scikit-learn
joblib
```
(Pinning versions like `streamlit==1.39.0` is safer but slower to deploy. Loose versions usually find prebuilt wheels.)

### Streamlit Cloud workflow
1. Sign in at https://share.streamlit.io with GitHub
2. Click **New app** → connect repo → choose branch → choose `app.py`
3. Streamlit Cloud builds the environment from `requirements.txt`
4. App deploys to a URL like `your-app-name.streamlit.app`
5. Future commits auto-redeploy

### First build is slow (5-15 minutes)
- Subsequent updates redeploy in under a minute
- If hung > 15 minutes, check logs for compile errors and consider unpinning `requirements.txt`

---

## The "why" behind major decisions

### Why drop UDI, Product ID, TWF, HDF, PWF, OSF, RNF?
- UDI, Product ID — identifiers, no predictive value
- TWF/HDF/PWF/OSF/RNF — calculated AFTER failure, so they leak the answer

### Why one-hot encode Type with `drop_first=True`?
- ML needs numbers, not text — must encode categories
- `drop_first=True` avoids redundancy: 3 categories need only 2 binary columns

### Why stratify the train/test split?
- With only 3.4% failures, a random split could leave the test set with 0 failures or 10% failures — variance kills evaluation
- Stratification preserves class proportions

### Why fit scaler only on training data?
- Test data simulates "the future" — the model can't see it during training
- Fitting the scaler on test data leaks future information into preprocessing
- Production deployment can't recompute statistics from one new sample, so we practice the discipline from day one

### Why pick threshold 0.4 instead of 0.5?
- Default threshold optimizes accuracy, not the metric we actually care about
- For predictive maintenance, missing a failure costs much more than a false alarm
- Lowering to 0.4 gave +12 percentage points of recall for a small precision drop

### Why pick Random Forest over Logistic Regression?
- F1 jumped from 46% to 64% — that's the recruiter-relevant number
- LR is linear; failures in this dataset live in non-linear patterns (e.g., tool wear matters only ABOVE 200 minutes)
- Trees handle feature interactions implicitly; `class_weight="balanced"` solves imbalance without aggressive threshold tuning

---

## Common errors

### `FileNotFoundError: ../data/ai4i2020.csv`
Your notebook is running from a different folder than expected.
Fix: check `os.getcwd()`. If you're in the project root, paths shouldn't have `../`. If you're in `notebooks/`, they should.

### `SyntaxError` — missing quotes around path
```python
df = pd.read_csv(../data/file.csv)   # WRONG — no quotes
df = pd.read_csv("../data/file.csv") # RIGHT
```

### `Indentation error` inside a function
Python uses indentation (4 spaces or 1 tab) to define what's inside a function. Misalign and it falls outside.

### Streamlit slider key collision
If you have two sliders with the same label, give them unique `key=` parameters:
```python
st.slider("Torque", ..., key="main_torque")
st.slider("Torque", ..., key="wif_torque")
```

### `ModuleNotFoundError` after `pip install`
You probably installed in the system Python, not your venv. Activate venv first:
```
source .venv/bin/activate
pip install <package>
```

### Streamlit Cloud build hangs
Usually a dependency conflict. Either reboot the app or unpin versions in `requirements.txt`.

### Confusion: `print` vs `return` vs implicit `None`
```python
def f():
    print(1)        # prints, returns None implicitly

def g():
    return 1        # returns 1, no output
```
If a function isn't returning what you expect, you probably forgot `return`.

---

## Resources I'd recommend (in order)

1. [StatQuest YouTube](https://www.youtube.com/@statquest) — Josh Starmer explains every ML concept clearly. Start with the videos on logistic regression and random forest.
2. [Kaggle Learn — Intro to Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning) — short, hands-on, free
3. [Hands-On Machine Learning by Aurélien Géron](https://www.oreilly.com/library/view/hands-on-machine-learning/9781098125967/) — chapters 1–7 cover what we did with more depth
4. [scikit-learn user guide](https://scikit-learn.org/stable/user_guide.html) — reference for every model and tool

---

## Personal reflection

What surprised me:
- How much of ML "engineering" is actually pipeline plumbing — paths, file formats, version compatibility — not math.
- Accuracy is one of the worst metrics on imbalanced data despite being the most natural one to think of first.
- Random Forest beat Logistic Regression by a huge margin even with default settings — and the reason was that real failure patterns are non-linear.
- Streamlit dramatically lowers the barrier from "I trained a model" to "I deployed a usable product."
- Git/GitHub is its own learning curve. Be careful with destructive operations and ALWAYS have a backup before clicking anything labeled "remove."

What I'd do differently next time:
- Set up GitHub on day one (so I never lose work again)
- Set up Time Machine on day one (same reason)
- Take screenshots of the project as I go — useful for the README later
- Use a single combined notebook for early Days 2-4 instead of separate ones — easier to revisit