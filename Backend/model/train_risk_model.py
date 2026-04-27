"""
Banking Loan Risk Model — Training Script
Generates synthetic banking data and trains a RandomForest for risk scoring.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle, os

print("=" * 50)
print("  Banking Loan Risk Model — Training")
print("=" * 50)

np.random.seed(42)
n = 6000

# ===== Generate Synthetic Banking Data =====
age = np.random.randint(22, 62, n)
previous_defaults = np.random.choice([0,0,0,0,0,0,1,1,2,3], n)

# Credit score (correlated with defaults)
credit_score = np.clip(
    np.random.normal(700, 100, n) - previous_defaults * 60,
    300, 900
).astype(int)

income_annum = np.clip(np.random.lognormal(13.5, 0.8, n), 200000, 15000000)
loan_amount = np.clip(income_annum * np.random.uniform(0.1, 2.5, n), 50000, 10000000)
loan_term = np.random.choice([12, 24, 36, 48, 60, 84, 120, 180, 240, 360], n)
existing_loans = np.random.poisson(1.2, n).clip(0, 8)
existing_emis = (existing_loans * np.random.uniform(5000, 40000, n) * (existing_loans > 0)).round(0)
collateral_value = np.clip(loan_amount * np.random.uniform(0.4, 3.0, n), 10000, 50000000)

emp_choices = np.random.choice(['Employed','Self-Employed','Unemployed'], n, p=[0.6, 0.25, 0.15])
employment_encoded = np.where(emp_choices == 'Employed', 2,
                     np.where(emp_choices == 'Self-Employed', 1, 0))

years_of_employment = np.clip((age - 21) * np.random.uniform(0.1, 0.85, n), 0, 40).astype(int)
years_of_employment = np.where(emp_choices == 'Unemployed', 0, years_of_employment)
bank_balance = np.clip(np.random.lognormal(11, 1.5, n), 0, 10000000)

# Derived features
dti_ratio = np.where(income_annum > 0, (existing_emis * 12) / income_annum, 0)
ltv_ratio = np.where(collateral_value > 0, loan_amount / collateral_value, 1.0)

# ===== Calculate Risk Score for Labels =====
risk = np.zeros(n)
risk += (900 - credit_score) / 600 * 30        # 0-30 from credit
risk += np.clip(dti_ratio * 50, 0, 20)          # 0-20 from DTI
risk += np.clip(ltv_ratio * 25, 0, 15)          # 0-15 from LTV
risk += previous_defaults * 8                    # 0-24 from defaults
risk += (employment_encoded == 0) * 12           # 12 for unemployed
risk += (employment_encoded == 1) * 3            # 3 for self-employed
risk += np.clip((loan_amount / income_annum - 1) * 5, 0, 8)
risk += np.clip((50 - years_of_employment) / 50 * 3, 0, 3)
risk = np.clip(risk + np.random.normal(0, 5, n), 0, 100)

# Labels: 0=Low Risk, 1=Medium Risk, 2=High Risk
labels = np.where(risk < 35, 0, np.where(risk < 65, 1, 2))

# ===== Build DataFrame =====
feature_names = [
    'credit_score', 'income_annum', 'loan_amount', 'loan_term',
    'existing_loans', 'existing_emis', 'dti_ratio', 'collateral_value',
    'ltv_ratio', 'age', 'employment_encoded', 'years_of_employment',
    'bank_balance', 'previous_defaults'
]

X = pd.DataFrame({
    'credit_score': credit_score,
    'income_annum': income_annum,
    'loan_amount': loan_amount,
    'loan_term': loan_term,
    'existing_loans': existing_loans,
    'existing_emis': existing_emis,
    'dti_ratio': dti_ratio,
    'collateral_value': collateral_value,
    'ltv_ratio': ltv_ratio,
    'age': age,
    'employment_encoded': employment_encoded,
    'years_of_employment': years_of_employment,
    'bank_balance': bank_balance,
    'previous_defaults': previous_defaults
})

y = labels

# ===== Train/Test Split =====
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ===== Scale =====
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ===== Train RandomForest =====
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_scaled, y_train)

# ===== Evaluate =====
train_acc = model.score(X_train_scaled, y_train)
test_acc = model.score(X_test_scaled, y_test)
print(f"\n  Train Accuracy: {train_acc:.4f}")
print(f"  Test Accuracy:  {test_acc:.4f}")

# Feature importances
importances = model.feature_importances_
sorted_idx = np.argsort(importances)[::-1]
print("\n  Top 5 Feature Importances:")
for i in range(5):
    idx = sorted_idx[i]
    print(f"    {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")

# Label distribution
unique, counts = np.unique(y, return_counts=True)
label_names = ['Low Risk', 'Medium Risk', 'High Risk']
print("\n  Label Distribution:")
for u, c in zip(unique, counts):
    print(f"    {label_names[u]}: {c} ({c/n*100:.1f}%)")

# ===== Save Model =====
pickle.dump(model, open("risk_model.pkl", "wb"))
pickle.dump(scaler, open("risk_scaler.pkl", "wb"))
pickle.dump(feature_names, open("risk_columns.pkl", "wb"))

print(f"\n  [OK] Model saved: risk_model.pkl, risk_scaler.pkl, risk_columns.pkl")
print("=" * 50)
