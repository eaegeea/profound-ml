#!/usr/bin/env python3
"""
Train simplified V3 model using only 4 inputs:
1. Marketing Headcount
2. People Count
3. Company Revenue
4. B2B/B2C Type
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import roc_auc_score, r2_score, accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("TRAINING SIMPLIFIED V3 MODEL (4 INPUTS ONLY)")
print("=" * 80)

# Load training data
print("\n[1/3] Loading and preparing data...")

df_train = pd.read_csv('../../dataset.csv')
df_train.columns = df_train.columns.str.strip()

print(f"  Loaded dataset: {len(df_train)} accounts")

# V3 Filter: Only companies with marketing teams
df_train = df_train[df_train['MarketingHeadcount'].notna() & (df_train['MarketingHeadcount'] > 0)].copy()
print(f"  After V3 filter: {len(df_train)} accounts")

# Store medians for imputation
medians = {
    'People Count': float(df_train['People Count'].median()),
    'Company Revenue': float(df_train['Company Revenue'].median())
}

print(f"\n  Medians for imputation:")
print(f"    People Count: {medians['People Count']:,.0f}")
print(f"    Company Revenue: ${medians['Company Revenue']:,.0f}")

# Imputation
df_train['People Count'] = df_train['People Count'].fillna(medians['People Count'])
df_train['Company Revenue'] = df_train['Company Revenue'].fillna(medians['Company Revenue'])

# Calculate Marketing-to-Headcount Ratio
df_train['Marketing_to_Headcount_Ratio'] = df_train['MarketingHeadcount'] / df_train['People Count']
df_train['Marketing_to_Headcount_Ratio'] = df_train['Marketing_to_Headcount_Ratio'].replace([np.inf, -np.inf], 0).fillna(0)

# Log transforms
df_train['log_CompanyRevenue'] = np.log1p(df_train['Company Revenue'])
df_train['log_PeopleCount'] = np.log1p(df_train['People Count'])

# B2B encoding
b2b_col = 'B2B/B2C Business Type'
df_train['is_B2B'] = (df_train[b2b_col] == 'B2B').astype(int)
df_train['is_B2B'] = df_train['is_B2B'].fillna(1)  # Default to B2B

# Define features (ONLY 5: the 4 inputs + calculated ratio)
feature_cols = [
    'log_PeopleCount',           # From input: people_count
    'log_CompanyRevenue',        # From input: company_revenue
    'MarketingHeadcount',        # From input: marketing_headcount
    'is_B2B',                    # From input: is_b2b
    'Marketing_to_Headcount_Ratio'  # Calculated from marketing_headcount / people_count
]

print(f"\n  Features used: {len(feature_cols)}")
for i, feat in enumerate(feature_cols, 1):
    print(f"    {i}. {feat}")

# Train Model A (Close Score)
print("\n[2/3] Training models...")

X_train = df_train[feature_cols]
y_train = df_train['is_customer']

X_tr, X_val, y_tr, y_val = train_test_split(
    X_train, y_train, 
    test_size=0.2, 
    random_state=42, 
    stratify=y_train
)

model_A = DecisionTreeClassifier(
    max_depth=4, 
    min_samples_leaf=25, 
    class_weight='balanced', 
    random_state=42
)
model_A.fit(X_tr, y_tr)

# Evaluate Model A
y_pred_proba = model_A.predict_proba(X_val)[:, 1]
y_pred = model_A.predict(X_val)

roc_auc = roc_auc_score(y_val, y_pred_proba)
accuracy = accuracy_score(y_val, y_pred)
cm = confusion_matrix(y_val, y_pred)

print(f"\n  Model A (Close Score Prediction):")
print(f"    ROC-AUC: {roc_auc:.3f}")
print(f"    Accuracy: {accuracy:.1%}")
print(f"    Confusion Matrix:")
print(f"      TN: {cm[0,0]:3d}  FP: {cm[0,1]:3d}")
print(f"      FN: {cm[1,0]:3d}  TP: {cm[1,1]:3d}")

# Feature importance
importances = model_A.feature_importances_
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': importances
}).sort_values('importance', ascending=False)

print(f"\n  Feature Importance:")
for i, row in feature_importance.iterrows():
    print(f"    {row['feature']:35s}: {row['importance']:.3f}")

# Train Model B (ACV Prediction)
df_customers = df_train[df_train['is_customer'] == 1].copy()
df_customers = df_customers[df_customers['ContractValue'] <= 100000].copy()

X_b_train = df_customers[feature_cols]
y_b_train = df_customers['ContractValue']

X_b_tr, X_b_val, y_b_tr, y_b_val = train_test_split(
    X_b_train, y_b_train, 
    test_size=0.2, 
    random_state=42
)

model_B = DecisionTreeRegressor(
    max_depth=4, 
    min_samples_leaf=10, 
    random_state=42
)
model_B.fit(X_b_tr, y_b_tr)

r2 = r2_score(y_b_val, model_B.predict(X_b_val))
print(f"\n  Model B (ACV Prediction):")
print(f"    R²: {r2:.3f}")

# Save models and metadata
print("\n[3/3] Saving simplified models...")

# Save Model A
with open('model_a_simplified.pkl', 'wb') as f:
    pickle.dump(model_A, f)
print(f"  ✅ Saved: model_a_simplified.pkl")

# Save Model B
with open('model_b_simplified.pkl', 'wb') as f:
    pickle.dump(model_B, f)
print(f"  ✅ Saved: model_b_simplified.pkl")

# Save preprocessing parameters
preprocessing_params = {
    'medians': medians,
    'feature_cols': feature_cols,
    'model_version': 'v3_simplified',
    'required_inputs': [
        'marketing_headcount',
        'people_count', 
        'company_revenue',
        'is_b2b'
    ]
}

with open('preprocessing_params_simplified.pkl', 'wb') as f:
    pickle.dump(preprocessing_params, f)
print(f"  ✅ Saved: preprocessing_params_simplified.pkl")

print("\n" + "=" * 80)
print("✅ SIMPLIFIED MODELS SAVED FOR API")
print("=" * 80)

print("\n📊 Model Summary:")
print(f"   • Model A ROC-AUC: {roc_auc:.3f}")
print(f"   • Model A Accuracy: {accuracy:.1%}")
print(f"   • Model B R²: {r2:.3f}")
print(f"   • Total Features: {len(feature_cols)}")

print("\n🎯 Required Inputs (4 total):")
print("   1. marketing_headcount (required, must be > 0)")
print("   2. people_count (required)")
print("   3. company_revenue (optional, will use median if missing)")
print("   4. is_b2b (optional, 1 for B2B, 0 for B2C, default 1)")

print("\n💡 Calculated Features:")
print("   • Marketing_to_Headcount_Ratio = marketing_headcount / people_count")
print("   • log transforms applied to revenue and headcount")

print("\n🚀 Ready for API deployment!")

