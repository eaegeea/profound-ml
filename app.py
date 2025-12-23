#!/usr/bin/env python3
"""
Flask API for V3 Territory Design Model
Accepts company data from Clay and returns predictions
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for Clay

# Load models and preprocessing params at startup
print("Loading models...")
with open('model_a.pkl', 'rb') as f:
    model_a = pickle.load(f)
print("✅ Model A loaded")

with open('model_b.pkl', 'rb') as f:
    model_b = pickle.load(f)
print("✅ Model B loaded")

with open('preprocessing_params.pkl', 'rb') as f:
    params = pickle.load(f)
print("✅ Preprocessing params loaded")

medians = params['medians']
top_industries = params['top_industries']
feature_cols = params['feature_cols']
all_industry_cols = params['all_industry_cols']

print(f"🚀 API ready with {len(feature_cols)} features")


def preprocess_input(data):
    """
    Preprocess input data to match training format
    
    Expected input fields:
    - company_name (optional, for reference)
    - domain (optional, for reference)
    - people_count (required): Number of employees
    - marketing_headcount (required): Number of marketing employees
    - company_revenue (optional): Annual revenue in dollars
    - industry (optional): Industry classification
    - is_b2b (optional): 1 for B2B, 0 for B2C, default is 1
    - prompt_volume (optional): Prompt volume metric
    """
    # Create dataframe
    df = pd.DataFrame([data])
    
    # Rename fields to match training data
    field_mapping = {
        'people_count': 'People Count',
        'marketing_headcount': 'MarketingHeadcount',
        'company_revenue': 'Company Revenue',
        'industry': 'Industry',
        'is_b2b': 'is_B2B',
        'prompt_volume': 'PromptVolume'
    }
    
    for api_field, model_field in field_mapping.items():
        if api_field in df.columns:
            df[model_field] = df[api_field]
    
    # Fill missing values with medians
    if 'People Count' not in df.columns or pd.isna(df['People Count'].iloc[0]):
        df['People Count'] = medians['People Count']
    
    if 'Company Revenue' not in df.columns or pd.isna(df['Company Revenue'].iloc[0]):
        df['Company Revenue'] = medians['Company Revenue']
    
    if 'PromptVolume' not in df.columns or pd.isna(df['PromptVolume'].iloc[0]):
        df['PromptVolume'] = medians['PromptVolume']
    
    if 'is_B2B' not in df.columns or pd.isna(df['is_B2B'].iloc[0]):
        df['is_B2B'] = 1  # Default to B2B
    
    # Calculate Marketing-to-Headcount Ratio
    df['Marketing_to_Headcount_Ratio'] = df['MarketingHeadcount'] / df['People Count']
    df['Marketing_to_Headcount_Ratio'] = df['Marketing_to_Headcount_Ratio'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Log transforms
    df['log_CompanyRevenue'] = np.log1p(df['Company Revenue'])
    df['log_PeopleCount'] = np.log1p(df['People Count'])
    df['log_PromptVolume'] = np.log1p(df['PromptVolume'])
    
    # Industry encoding
    if 'Industry' in df.columns and not pd.isna(df['Industry'].iloc[0]):
        industry = df['Industry'].iloc[0]
        if industry in top_industries:
            df['IndustryClass_grouped'] = industry
        else:
            df['IndustryClass_grouped'] = 'Other'
    else:
        df['IndustryClass_grouped'] = 'Other'
    
    # Create one-hot encoded industry columns
    for industry_col in all_industry_cols:
        industry_name = industry_col.replace('Industry_', '')
        if df['IndustryClass_grouped'].iloc[0] == industry_name:
            df[industry_col] = 1
        else:
            df[industry_col] = 0
    
    # Ensure all required features exist
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    
    # Select only the features used in training
    X = df[feature_cols]
    
    return X


def assign_segment(score):
    """Assign segment based on close score"""
    if score >= 0.70:
        return 'Ideal Target'
    elif score >= 0.50:
        return 'Good Target'
    elif score >= 0.30:
        return 'Medium Target'
    else:
        return 'Low Priority'


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'V3 Territory Design',
        'features': len(feature_cols),
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    
    Example request body:
    {
        "company_name": "Acme Corp",
        "domain": "acme.com",
        "people_count": 500,
        "marketing_headcount": 25,
        "company_revenue": 50000000,
        "industry": "Technology",
        "is_b2b": 1
    }
    """
    try:
        # Get input data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        
        # Validate required fields
        if 'marketing_headcount' not in data:
            return jsonify({'error': 'marketing_headcount is required'}), 400
        
        if data.get('marketing_headcount', 0) <= 0:
            return jsonify({
                'company_name': data.get('company_name', 'Unknown'),
                'domain': data.get('domain', ''),
                'error': 'V3 model requires marketing_headcount > 0',
                'close_score': None,
                'predicted_acv': None,
                'expected_value': None,
                'segment': 'Not Applicable'
            }), 200
        
        # Preprocess input
        X = preprocess_input(data)
        
        # Make predictions
        close_score = float(model_a.predict_proba(X)[0, 1])
        predicted_acv = float(model_b.predict(X)[0])
        predicted_acv = max(0, predicted_acv)  # Ensure non-negative
        
        expected_value = close_score * predicted_acv
        segment = assign_segment(close_score)
        
        # Prepare response
        response = {
            'company_name': data.get('company_name', 'Unknown'),
            'domain': data.get('domain', ''),
            'close_score': round(close_score, 4),
            'close_score_percent': f"{close_score * 100:.1f}%",
            'predicted_acv': round(predicted_acv, 2),
            'expected_value': round(expected_value, 2),
            'segment': segment,
            'marketing_to_headcount_ratio': round(float(X['Marketing_to_Headcount_Ratio'].iloc[0]), 4),
            'inputs': {
                'people_count': int(X['People Count'].iloc[0]) if 'People Count' in X.columns else None,
                'marketing_headcount': data.get('marketing_headcount'),
                'company_revenue': float(X['Company Revenue'].iloc[0]) if 'Company Revenue' in X.columns else None,
                'industry': data.get('industry', 'Other'),
                'is_b2b': int(X['is_B2B'].iloc[0]) if 'is_B2B' in X.columns else 1
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error processing request'
        }), 500


@app.route('/batch', methods=['POST'])
def batch_predict():
    """
    Batch prediction endpoint for multiple companies
    
    Example request body:
    {
        "companies": [
            {
                "company_name": "Acme Corp",
                "people_count": 500,
                "marketing_headcount": 25,
                ...
            },
            {
                "company_name": "Beta Inc",
                "people_count": 300,
                "marketing_headcount": 15,
                ...
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'companies' not in data:
            return jsonify({'error': 'No companies data provided'}), 400
        
        companies = data['companies']
        results = []
        
        for company in companies:
            # Process each company
            try:
                if company.get('marketing_headcount', 0) <= 0:
                    results.append({
                        'company_name': company.get('company_name', 'Unknown'),
                        'domain': company.get('domain', ''),
                        'error': 'V3 model requires marketing_headcount > 0',
                        'segment': 'Not Applicable'
                    })
                    continue
                
                X = preprocess_input(company)
                
                close_score = float(model_a.predict_proba(X)[0, 1])
                predicted_acv = float(model_b.predict(X)[0])
                predicted_acv = max(0, predicted_acv)
                
                expected_value = close_score * predicted_acv
                segment = assign_segment(close_score)
                
                results.append({
                    'company_name': company.get('company_name', 'Unknown'),
                    'domain': company.get('domain', ''),
                    'close_score': round(close_score, 4),
                    'close_score_percent': f"{close_score * 100:.1f}%",
                    'predicted_acv': round(predicted_acv, 2),
                    'expected_value': round(expected_value, 2),
                    'segment': segment,
                    'marketing_to_headcount_ratio': round(float(X['Marketing_to_Headcount_Ratio'].iloc[0]), 4)
                })
                
            except Exception as e:
                results.append({
                    'company_name': company.get('company_name', 'Unknown'),
                    'error': str(e)
                })
        
        return jsonify({
            'total': len(companies),
            'successful': len([r for r in results if 'error' not in r]),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error processing batch request'
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

