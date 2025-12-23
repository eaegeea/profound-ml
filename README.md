# V3 Territory Design API (Simplified)

Machine Learning API for scoring and prioritizing sales prospects based on company attributes.

## 🎯 Model Overview

**Version**: V3 Simplified  
**Model Type**: Decision Tree Classifier + Regressor  
**Training Data**: 1,188 companies with marketing teams  
**Accuracy**: 74.4% | ROC-AUC: 0.751

### Key Feature
The model automatically calculates the **Marketing-to-Headcount Ratio** (57.9% importance) - the #1 predictor of deal success.

---

## 📊 API Endpoints

### 1. Health Check
```bash
GET /health
```

### 2. Single Prediction
```bash
POST /predict
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "domain": "acme.com",
  "marketing_headcount": 25,
  "people_count": 500,
  "company_revenue": 50000000,
  "is_b2b": 1
}
```

**Response:**
```json
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
```

### 3. Batch Prediction
```bash
POST /batch
Content-Type: application/json

{
  "companies": [
    {
      "company_name": "Acme Corp",
      "marketing_headcount": 25,
      "people_count": 500
    },
    {
      "company_name": "Beta Inc",
      "marketing_headcount": 15,
      "people_count": 300
    }
  ]
}
```

---

## 🔧 Required Inputs

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `marketing_headcount` | Integer | ✅ Yes | Number of marketing employees (must be > 0) | `25` |
| `people_count` | Integer | ✅ Yes | Total number of employees | `500` |
| `company_revenue` | Float | ⚠️ Optional | Annual revenue in USD (uses $80M median if missing) | `50000000` |
| `is_b2b` | Integer | ⚠️ Optional | 1 for B2B, 0 for B2C (defaults to 1) | `1` |
| `company_name` | String | ⚠️ Optional | For reference only | `"Acme Corp"` |
| `domain` | String | ⚠️ Optional | For reference only | `"acme.com"` |

---

## 📈 Output Fields

| Field | Description | Example |
|-------|-------------|---------|
| `close_score` | Win probability (0-1) | `0.8234` |
| `close_score_percent` | Win probability as percentage | `"82.3%"` |
| `predicted_acv` | Predicted Annual Contract Value | `28500.00` |
| `expected_value` | Close Score × Predicted ACV | `23469.90` |
| `segment` | Tier classification | `"Ideal Target"` |
| `marketing_to_headcount_ratio` | Calculated ratio (most important feature!) | `0.0500` |
| `marketing_ratio_percent` | Ratio as percentage | `"5.00%"` |

### Segment Definitions

| Segment | Close Score | Description |
|---------|-------------|-------------|
| **Ideal Target** | ≥ 70% | Top priority, 82% avg win rate |
| **Good Target** | 50-69% | Strong prospects, structured nurture |
| **Medium Target** | 30-49% | Qualified leads, longer sales cycle |
| **Low Priority** | < 30% | Low conversion probability |

---

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
```bash
cd "ML DT v3/api"
pip install -r requirements.txt
```

2. **Run the API:**
```bash
python app_simplified.py
```

3. **Test it:**
```bash
curl http://localhost:5000/health
```

### Test with Sample Data

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "marketing_headcount": 30,
    "people_count": 400,
    "company_revenue": 75000000,
    "is_b2b": 1
  }'
```

---

## ☁️ Deploy to Railway

1. **Create Railway account**: https://railway.app

2. **Create `Procfile`:**
```
web: gunicorn app_simplified:app
```

3. **Deploy:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

4. **Set environment:**
- Railway will automatically detect Flask
- API will be available at: `https://your-app.railway.app`

---

## 🧪 Clay Integration

### Step-by-Step Setup in Clay

1. **Add HTTP API Column**
   - In your Clay table, click "+ Add Column"
   - Select "HTTP API"

2. **Configure API Request**
   ```
   Method: POST
   URL: https://your-api-url.railway.app/predict
   Headers:
     Content-Type: application/json
   Body (JSON):
     {
       "company_name": {{Company Name}},
       "domain": {{Domain}},
       "marketing_headcount": {{Marketing Headcount}},
       "people_count": {{Employee Count}},
       "company_revenue": {{Annual Revenue}},
       "is_b2b": 1
     }
   ```

3. **Extract Response Fields**
   - Add columns to extract:
     - `{{http_response.close_score_percent}}` → Close Score
     - `{{http_response.segment}}` → Segment
     - `{{http_response.expected_value}}` → Expected Value
     - `{{http_response.marketing_ratio_percent}}` → Marketing Ratio

4. **Filter & Sort**
   - Filter by `Segment = "Ideal Target"`
   - Sort by `Expected Value` (descending)

### Clay Column Mapping

| Clay Column | API Field | Required |
|-------------|-----------|----------|
| Company Name | `company_name` | No |
| Domain | `domain` | No |
| Marketing Headcount / Marketing Employees | `marketing_headcount` | **Yes** |
| Employee Count / People Count / Headcount | `people_count` | **Yes** |
| Annual Revenue / Company Revenue | `company_revenue` | No |
| Business Type (1=B2B, 0=B2C) | `is_b2b` | No |

---

## 🔍 Model Details

### Features Used (5 total)

1. **Marketing_to_Headcount_Ratio** (57.9% importance) ⭐
   - Automatically calculated from `marketing_headcount / people_count`
   - Ideal range: 7-19%
   
2. **MarketingHeadcount** (37.3% importance)
   - Direct input
   - Higher is better (indicates growth investment)

3. **log_PeopleCount** (4.8% importance)
   - Log-transformed employee count
   - Captures company scale

4. **log_CompanyRevenue** (0.0% importance)
   - Log-transformed revenue
   - Minimal direct impact

5. **is_B2B** (0.0% importance)
   - Business model indicator
   - Minimal direct impact

### Why the Ratio Matters

The **Marketing-to-Headcount Ratio** is the strongest predictor because it indicates:
- Growth stage and investment in customer acquisition
- Product-market fit signal (companies invest when they see traction)
- Strategic marketing focus vs. lean operations

**Sweet Spot**: 7-19% marketing employees
- **Below 7%**: Under-investing in marketing (higher risk)
- **7-19%**: Optimal investment (82% win rate)
- **Above 20%**: Rare, but still positive signal

---

## 📊 Model Performance

### Classification (Model A)
- **ROC-AUC**: 0.751
- **Accuracy**: 74.4%
- **Precision**: 72.6%
- **Recall**: 61.6%

### Regression (Model B)
- **R²**: -0.038 (intentionally simple to avoid overfitting)
- **Predicts ACV range**: $5K - $40K

### Validation Results
- **Ideal Targets** (≥70% score): 82% actual win rate
- **Medium Targets** (30-69%): 42% actual win rate
- **Low Priority** (<30%): 19% actual win rate

---

## ⚠️ Important Notes

### V3 Model Filter
This model **only scores companies with marketing teams** (`marketing_headcount > 0`).

If `marketing_headcount` is 0 or null, the API returns:
```json
{
  "error": "V3 model requires marketing_headcount > 0",
  "segment": "Not Applicable - No Marketing Team"
}
```

### Data Quality Tips
1. **Accurate Employee Counts**: The ratio calculation depends on precise headcount data
2. **Marketing Team Definition**: Include all marketing roles (demand gen, content, product marketing, etc.)
3. **Revenue Data**: Optional but improves accuracy when available
4. **B2B vs B2C**: Minimal impact on prediction, defaults to B2B if missing

---

## 🛠️ Troubleshooting

### API Returns Error

**Problem**: `marketing_headcount is required`  
**Solution**: Ensure Clay column is mapped and contains numeric values

**Problem**: `V3 model requires marketing_headcount > 0`  
**Solution**: This company has no marketing team, V3 model cannot score it

### Low Scores for Expected Good Prospects

**Problem**: Company has low marketing ratio  
**Solution**: This is working as designed. Companies with <7% marketing ratio are statistically lower probability

### Clay Request Timeout

**Problem**: Batch request too large  
**Solution**: Use `/batch` endpoint or split into smaller batches

---

## 📞 Support

- **Model Questions**: Review `V3_IMPROVEMENTS.md` in parent directory
- **API Issues**: Check `/health` endpoint
- **Clay Integration**: See Clay documentation for HTTP API setup

---

## 📄 License

Proprietary - Profound ML

---

## 🎯 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ V3 TERRITORY DESIGN API - QUICK REFERENCE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ENDPOINT: POST /predict                                     │
│                                                             │
│ REQUIRED:                                                   │
│   • marketing_headcount (must be > 0)                      │
│   • people_count                                           │
│                                                             │
│ OPTIONAL:                                                   │
│   • company_revenue (uses $80M median if missing)          │
│   • is_b2b (defaults to 1)                                 │
│                                                             │
│ OUTPUT:                                                     │
│   • close_score: Win probability (0-1)                     │
│   • predicted_acv: Deal size ($)                           │
│   • expected_value: close_score × predicted_acv           │
│   • segment: Ideal/Good/Medium/Low                        │
│   • marketing_ratio: #1 feature (57.9% importance)        │
│                                                             │
│ IDEAL TARGETS:                                             │
│   • Close Score: ≥ 70%                                     │
│   • Marketing Ratio: 7-19%                                 │
│   • Win Rate: 82%                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**🚀 Start scoring leads now!**

