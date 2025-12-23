#!/usr/bin/env python3
"""
Train and save V3 models for API deployment
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import roc_auc_score, r2_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("TRAINING AND SAVING V3 MODELS FOR API")
print("=" * 80)

# Train V3 model
print("\n[1/2] Training V3 models...")

df_train = pd.read_csv('../../dataset.csv')
df_train.columns = df_train.columns.str.strip()

print(f"  Loaded dataset: {len(df_train)} accounts")

# V3 Filter
df_train = df_train[df_train['MarketingHeadcount'].notna() & (df_train['MarketingHeadcount'] > 0)].copy()
print(f"  After V3 filter: {len(df_train)} accounts")

# Store medians for API
medians = {
    'People Count': float(df_train['People Count'].median()),
    'Company Revenue': float(df_train['Company Revenue'].median()),
    'PromptVolume': float(df_train['PromptVolume'].median())
}

# Imputation
for col, median_val in medians.items():
    df_train[col] = df_train[col].fillna(median_val)

# Feature engineering
df_train['Marketing_to_Headcount_Ratio'] = df_train['MarketingHeadcount'] / df_train['People Count']
df_train['Marketing_to_Headcount_Ratio'] = df_train['Marketing_to_Headcount_Ratio'].replace([np.inf, -np.inf], 0).fillna(0)

df_train['log_CompanyRevenue'] = np.log1p(df_train['Company Revenue'])
df_train['log_PeopleCount'] = np.log1p(df_train['People Count'])
df_train['log_PromptVolume'] = np.log1p(df_train['PromptVolume'])

# Industry encoding
industry_col = 'Industry Classification Industry Classification'
top_industries = df_train[industry_col].value_counts().head(10).index.tolist()
df_train['IndustryClass_grouped'] = df_train[industry_col].apply(
    lambda x: x if x in top_industries else 'Other'
)
industry_dummies = pd.get_dummies(df_train['IndustryClass_grouped'], prefix='Industry')
df_train = pd.concat([df_train, industry_dummies], axis=1)

# B2B encoding
b2b_col = 'B2B/B2C Business Type'
df_train['is_B2B'] = (df_train[b2b_col] == 'B2B').astype(int)

# Define features
feature_cols_A = ['log_PeopleCount', 'log_CompanyRevenue', 'log_PromptVolume', 
                  'MarketingHeadcount', 'Marketing_to_Headcount_Ratio', 'is_B2B']
industry_cols = [col for col in df_train.columns if col.startswith('Industry_')]
feature_cols_A.extend(industry_cols)

print(f"  Total features: {len(feature_cols_A)}")

# Train Model A (Close Score)
X_train = df_train[feature_cols_A]
y_train = df_train['is_customer']

X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42, stratify=y_train)

model_A = DecisionTreeClassifier(max_depth=4, min_samples_leaf=25, class_weight='balanced', random_state=42)
model_A.fit(X_tr, y_tr)

roc_auc = roc_auc_score(y_val, model_A.predict_proba(X_val)[:, 1])
print(f"  ✅ Model A trained (ROC-AUC: {roc_auc:.3f})")

# Train Model B (ACV Prediction)
df_customers = df_train[df_train['is_customer'] == 1].copy()
df_customers = df_customers[df_customers['ContractValue'] <= 100000].copy()

X_b_train = df_customers[feature_cols_A]
y_b_train = df_customers['ContractValue']

X_b_tr, X_b_val, y_b_tr, y_b_val = train_test_split(X_b_train, y_b_train, test_size=0.2, random_state=42)

model_B = DecisionTreeRegressor(max_depth=4, min_samples_leaf=10, random_state=42)
model_B.fit(X_b_tr, y_b_tr)

r2 = r2_score(y_b_val, model_B.predict(X_b_val))
print(f"  ✅ Model B trained (R²: {r2:.3f})")

# Save models and metadata
print("\n[2/2] Saving models for API...")

# Save Model A
with open('model_a.pkl', 'wb') as f:
    pickle.dump(model_A, f)
print(f"  ✅ Saved: model_a.pkl")

# Save Model B
with open('model_b.pkl', 'wb') as f:
    pickle.dump(model_B, f)
print(f"  ✅ Saved: model_b.pkl")

# Save preprocessing parameters
preprocessing_params = {
    'medians': medians,
    'top_industries': top_industries,
    'feature_cols': feature_cols_A,
    'all_industry_cols': industry_cols
}

with open('preprocessing_params.pkl', 'wb') as f:
    pickle.dump(preprocessing_params, f)
print(f"  ✅ Saved: preprocessing_params.pkl")

print("\n" + "=" * 80)
print("✅ MODELS SAVED FOR API")
print("=" * 80)

print("\n📊 Preprocessing Parameters:")
print(f"   • People Count median: {medians['People Count']:,.0f}")
print(f"   • Company Revenue median: ${medians['Company Revenue']:,.0f}")
print(f"   • PromptVolume median: {medians['PromptVolume']:,.0f}")
print(f"   • Top industries: {', '.join(top_industries[:5])}...")
print(f"   • Total features: {len(feature_cols_A)}")
print("\n🚀 Ready to launch API!")

