#!/usr/bin/env python3
"""
Simplified Flask API for V3 Territory Design Model
Only requires 4 inputs from Clay:
1. marketing_headcount
2. people_count
3. company_revenue (optional)
4. is_b2b (optional)
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
print("=" * 80)
print("LOADING SIMPLIFIED V3 MODEL API")
print("=" * 80)

with open('model_a_simplified.pkl', 'rb') as f:
    model_a = pickle.load(f)
print("✅ Model A loaded (Close Score)")

with open('model_b_simplified.pkl', 'rb') as f:
    model_b = pickle.load(f)
print("✅ Model B loaded (ACV Prediction)")

with open('preprocessing_params_simplified.pkl', 'rb') as f:
    params = pickle.load(f)
print("✅ Preprocessing params loaded")

medians = params['medians']
feature_cols = params['feature_cols']
required_inputs = params['required_inputs']

print(f"\n📊 Model Info:")
print(f"   Version: {params['model_version']}")
print(f"   Features: {len(feature_cols)}")
print(f"   Required inputs: {len(required_inputs)}")
print(f"\n🚀 API ready at http://0.0.0.0:5000")
print("=" * 80)


def preprocess_input(data):
    """
    Preprocess input data (SIMPLIFIED - only 4 inputs needed)
    
    Required:
    - marketing_headcount: Number of marketing employees (must be > 0)
    - people_count: Total number of employees
    
    Optional:
    - company_revenue: Annual revenue in dollars (uses median if missing)
    - is_b2b: 1 for B2B, 0 for B2C (defaults to 1)
    """
    # Create dataframe
    df = pd.DataFrame([data])
    
    # Handle people_count
    if 'people_count' not in df.columns or pd.isna(df['people_count'].iloc[0]) or df['people_count'].iloc[0] <= 0:
        df['people_count'] = medians['People Count']
    
    # Handle company_revenue
    if 'company_revenue' not in df.columns or pd.isna(df['company_revenue'].iloc[0]):
        df['company_revenue'] = medians['Company Revenue']
    
    # Handle is_b2b (default to 1 = B2B)
    if 'is_b2b' not in df.columns or pd.isna(df['is_b2b'].iloc[0]):
        df['is_b2b'] = 1
    
    # Calculate Marketing-to-Headcount Ratio
    df['Marketing_to_Headcount_Ratio'] = df['marketing_headcount'] / df['people_count']
    df['Marketing_to_Headcount_Ratio'] = df['Marketing_to_Headcount_Ratio'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Log transforms
    df['log_CompanyRevenue'] = np.log1p(df['company_revenue'])
    df['log_PeopleCount'] = np.log1p(df['people_count'])
    
    # Rename for model
    df['MarketingHeadcount'] = df['marketing_headcount']
    df['is_B2B'] = df['is_b2b']
    
    # Select features in correct order
    X = df[[
        'log_PeopleCount',
        'log_CompanyRevenue',
        'MarketingHeadcount',
        'is_B2B',
        'Marketing_to_Headcount_Ratio'
    ]]
    
    return X, df


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


@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'name': 'V3 Territory Design API (Simplified)',
        'version': '1.0',
        'model': 'Decision Tree (V3 - Companies with Marketing Teams)',
        'endpoints': {
            '/health': 'GET - Health check',
            '/predict': 'POST - Predict single company',
            '/batch': 'POST - Predict multiple companies'
        },
        'required_inputs': required_inputs,
        'optional_inputs': ['company_revenue'],
        'features_used': len(feature_cols),
        'most_important_feature': 'Marketing_to_Headcount_Ratio (57.9%)',
        'documentation': 'https://github.com/eaegeea/profound-ml'
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'V3 Territory Design (Simplified)',
        'version': params['model_version'],
        'features': len(feature_cols),
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    
    Example request:
    POST /predict
    {
        "company_name": "Acme Corp",
        "domain": "acme.com",
        "marketing_headcount": 25,
        "people_count": 500,
        "company_revenue": 50000000,
        "is_b2b": 1
    }
    
    Example response:
    {
        "company_name": "Acme Corp",
        "domain": "acme.com",
        "close_score": 0.8234,
        "close_score_percent": "82.3%",
        "predicted_acv": 28500.00,
        "expected_value": 23469.90,
        "segment": "Ideal Target",
        "marketing_to_headcount_ratio": 0.0500,
        "marketing_ratio_percent": "5.00%"
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
        
        marketing_headcount = data.get('marketing_headcount')
        
        # V3 filter: Reject if no marketing team
        if marketing_headcount is None or marketing_headcount <= 0:
            return jsonify({
                'company_name': data.get('company_name', 'Unknown'),
                'domain': data.get('domain', ''),
                'error': 'V3 model requires marketing_headcount > 0',
                'message': 'This model is designed for companies with marketing teams',
                'close_score': None,
                'segment': 'Not Applicable - No Marketing Team'
            }), 200
        
        # Preprocess input
        X, df_processed = preprocess_input(data)
        
        # Make predictions
        close_score = float(model_a.predict_proba(X)[0, 1])
        predicted_acv = float(model_b.predict(X)[0])
        predicted_acv = max(0, predicted_acv)  # Ensure non-negative
        
        expected_value = close_score * predicted_acv
        segment = assign_segment(close_score)
        marketing_ratio = float(X['Marketing_to_Headcount_Ratio'].iloc[0])
        
        # Prepare response
        response = {
            'company_name': data.get('company_name', 'Unknown'),
            'domain': data.get('domain', ''),
            'close_score': round(close_score, 4),
            'close_score_percent': f"{close_score * 100:.1f}%",
            'predicted_acv': round(predicted_acv, 2),
            'expected_value': round(expected_value, 2),
            'segment': segment,
            'marketing_to_headcount_ratio': round(marketing_ratio, 4),
            'marketing_ratio_percent': f"{marketing_ratio * 100:.2f}%",
            'inputs_used': {
                'marketing_headcount': int(data.get('marketing_headcount')),
                'people_count': int(df_processed['people_count'].iloc[0]),
                'company_revenue': float(df_processed['company_revenue'].iloc[0]),
                'is_b2b': int(df_processed['is_b2b'].iloc[0])
            },
            'model_info': {
                'version': 'v3_simplified',
                'primary_factor': 'Marketing-to-Headcount Ratio (57.9% importance)',
                'ideal_ratio_range': '7-19%'
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error processing request',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/batch', methods=['POST'])
def batch_predict():
    """
    Batch prediction endpoint for multiple companies
    
    Example request:
    POST /batch
    {
        "companies": [
            {
                "company_name": "Acme Corp",
                "marketing_headcount": 25,
                "people_count": 500,
                "company_revenue": 50000000
            },
            {
                "company_name": "Beta Inc",
                "marketing_headcount": 15,
                "people_count": 300
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'companies' not in data:
            return jsonify({'error': 'companies array is required'}), 400
        
        companies = data['companies']
        results = []
        
        for idx, company in enumerate(companies):
            try:
                # Check for marketing headcount
                marketing_headcount = company.get('marketing_headcount')
                
                if marketing_headcount is None or marketing_headcount <= 0:
                    results.append({
                        'company_name': company.get('company_name', f'Company {idx+1}'),
                        'domain': company.get('domain', ''),
                        'error': 'V3 model requires marketing_headcount > 0',
                        'segment': 'Not Applicable - No Marketing Team'
                    })
                    continue
                
                # Preprocess and predict
                X, df_processed = preprocess_input(company)
                
                close_score = float(model_a.predict_proba(X)[0, 1])
                predicted_acv = float(model_b.predict(X)[0])
                predicted_acv = max(0, predicted_acv)
                
                expected_value = close_score * predicted_acv
                segment = assign_segment(close_score)
                marketing_ratio = float(X['Marketing_to_Headcount_Ratio'].iloc[0])
                
                results.append({
                    'company_name': company.get('company_name', f'Company {idx+1}'),
                    'domain': company.get('domain', ''),
                    'close_score': round(close_score, 4),
                    'close_score_percent': f"{close_score * 100:.1f}%",
                    'predicted_acv': round(predicted_acv, 2),
                    'expected_value': round(expected_value, 2),
                    'segment': segment,
                    'marketing_to_headcount_ratio': round(marketing_ratio, 4),
                    'marketing_ratio_percent': f"{marketing_ratio * 100:.2f}%"
                })
                
            except Exception as e:
                results.append({
                    'company_name': company.get('company_name', f'Company {idx+1}'),
                    'error': str(e)
                })
        
        # Calculate summary stats
        successful = [r for r in results if 'error' not in r]
        
        summary = {
            'total_companies': len(companies),
            'successful_predictions': len(successful),
            'failed_predictions': len(companies) - len(successful),
            'results': results
        }
        
        if successful:
            summary['summary_stats'] = {
                'avg_close_score': round(sum(r['close_score'] for r in successful) / len(successful), 4),
                'avg_expected_value': round(sum(r['expected_value'] for r in successful) / len(successful), 2),
                'ideal_targets': len([r for r in successful if r['segment'] == 'Ideal Target']),
                'good_targets': len([r for r in successful if r['segment'] == 'Good Target']),
                'medium_targets': len([r for r in successful if r['segment'] == 'Medium Target']),
                'low_priority': len([r for r in successful if r['segment'] == 'Low Priority'])
            }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error processing batch request',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Starting API on port {port}...")
    print(f"📍 Access at: http://localhost:{port}")
    print(f"📖 Docs at: http://localhost:{port}/")
    print(f"💚 Health check: http://localhost:{port}/health\n")
    app.run(host='0.0.0.0', port=port, debug=False)

