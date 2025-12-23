# Clay Integration Setup Guide

## 🎯 Quick Summary

**API is ready!** Only **4 inputs** needed from Clay:
1. `marketing_headcount` (required)
2. `people_count` (required)  
3. `company_revenue` (optional)
4. `is_b2b` (optional, defaults to 1)

The **Marketing-to-Headcount Ratio** (most important feature) is **automatically calculated**.

---

## 🚀 Step 1: Test Locally (Optional)

```bash
# Navigate to API folder
cd "/Users/egeayan/Desktop/Profound/1000territory/ML DT v3/api"

# Start the API
python3 app_simplified.py

# In another terminal, test it
python3 test_api.py
```

Expected output: API tests should pass with Diversified scoring ~98%.

---

## ☁️ Step 2: Deploy to Railway

### Option A: Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Navigate to API folder
cd "/Users/egeayan/Desktop/Profound/1000territory/ML DT v3/api"

# Initialize and deploy
railway init
railway up
```

### Option B: Railway Dashboard

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account
4. Push the `api` folder to a GitHub repo
5. Select the repo and Railway will auto-deploy
6. Get your API URL: `https://your-app.railway.app`

---

## 🎨 Step 3: Configure in Clay

### 1. Add HTTP API Column

In your Clay table:
1. Click "+ Add Column"
2. Select "HTTP API"
3. Name it "ML Score"

### 2. Configure Request

**Method**: `POST`

**URL**: `https://your-api-url.railway.app/predict`
(Replace with your actual Railway URL)

**Headers**:
```
Content-Type: application/json
```

**Body** (select "JSON"):
```json
{
  "company_name": {{Company Name}},
  "domain": {{Domain}},
  "marketing_headcount": {{Marketing Headcount}},
  "people_count": {{Employee Count}},
  "company_revenue": {{Annual Revenue}},
  "is_b2b": 1
}
```

**Important**: Map your Clay column names to the correct fields!

### 3. Extract Response Data

After the API call, add columns to extract:

| New Column Name | Formula / Extraction Path |
|-----------------|---------------------------|
| Close Score | `{{ML Score.close_score_percent}}` |
| Segment | `{{ML Score.segment}}` |
| Expected Value | `{{ML Score.expected_value}}` |
| Predicted ACV | `{{ML Score.predicted_acv}}` |
| Marketing Ratio | `{{ML Score.marketing_ratio_percent}}` |

### 4. Filter for Ideal Targets

Add a filter:
- `Segment` equals `"Ideal Target"`
- Or `Close Score` ≥ 70%

### 5. Sort by Priority

Sort by:
1. `Close Score` (descending) for win probability
2. Or `Expected Value` (descending) for revenue potential

---

## 📊 Example Clay Table Setup

| Company | Marketing Headcount | Employee Count | Close Score | Segment | Expected Value | Marketing Ratio |
|---------|---------------------|----------------|-------------|---------|----------------|----------------|
| Diversified | 42 | 376 | 98.1% | Ideal Target | $21,865 | 11.17% |
| Jabra | 102 | 1660 | 82.0% | Ideal Target | $31,571 | 6.14% |
| ViewSonic | 89 | 1349 | 82.0% | Ideal Target | $31,571 | 6.60% |
| Small Corp | 2 | 500 | 18.5% | Low Priority | $4,825 | 0.40% |

---

## 🔧 Clay Column Mapping

Make sure your Clay columns are mapped correctly:

| Your Clay Column Name | API Field | Type | Required |
|----------------------|-----------|------|----------|
| Marketing Headcount / Marketing Employees / Marketing Team Size | `marketing_headcount` | Integer | ✅ Yes |
| Employee Count / Headcount / People Count / Company Size | `people_count` | Integer | ✅ Yes |
| Annual Revenue / Company Revenue / Revenue | `company_revenue` | Number | ⚠️ Optional |
| Business Type | `is_b2b` | Integer (1 or 0) | ⚠️ Optional |
| Company Name | `company_name` | String | ⚠️ Optional |
| Domain / Website | `domain` | String | ⚠️ Optional |

---

## 🎯 Expected Results

### Ideal Targets (Close Score ≥ 70%)
- **Win Probability**: 82% (from training data)
- **Marketing Ratio**: Typically 7-19%
- **Action**: Immediate high-touch outreach

### Good Targets (Close Score 50-69%)
- **Win Probability**: 54% (from training data)
- **Marketing Ratio**: Typically 4-7%
- **Action**: Structured nurture campaigns

### Medium Targets (Close Score 30-49%)
- **Win Probability**: 28% (from training data)
- **Marketing Ratio**: Typically 2-4%
- **Action**: Marketing-led qualification

### Low Priority (Close Score < 30%)
- **Win Probability**: 14% (from training data)
- **Marketing Ratio**: Typically < 2%
- **Action**: Automated low-touch campaigns

---

## 🛠️ Troubleshooting

### "marketing_headcount is required"
**Problem**: Clay column isn't mapped or is empty  
**Solution**: 
1. Check column mapping in API body
2. Ensure column has numeric values
3. Use `{{Column Name}}` syntax exactly

### "V3 model requires marketing_headcount > 0"
**Problem**: Company has 0 or null marketing employees  
**Solution**: This is expected! V3 model only scores companies with marketing teams. Filter these out in Clay before calling the API.

### API Times Out
**Problem**: Request takes too long  
**Solution**:
1. Check Railway logs for errors
2. Use `/batch` endpoint for multiple companies
3. Ensure API is running (check `/health` endpoint)

### Unexpected Low Scores
**Problem**: Expected high score but got low  
**Solution**: Check the marketing ratio - if it's below 7%, the model correctly identifies this as higher risk. This is working as designed!

---

## 📈 Pro Tips

### 1. Pre-filter in Clay
Before calling the API, filter out companies with:
- No marketing headcount data
- Marketing headcount = 0
- This saves API calls and avoids errors

### 2. Batch Processing
For large lists, use the `/batch` endpoint:
```json
{
  "companies": [
    {...company 1...},
    {...company 2...},
    {...company 3...}
  ]
}
```

### 3. Cache Results
Store API results in Clay to avoid re-scoring the same companies.

### 4. Monitor the Ratio
Add a conditional format in Clay:
- Green: Marketing ratio 7-19% (ideal)
- Yellow: Marketing ratio 4-7% (good)
- Red: Marketing ratio < 4% (low priority)

---

## 🎬 Demo Accounts for Testing

Test these in Clay to verify your setup:

```json
{
  "company_name": "Diversified",
  "marketing_headcount": 42,
  "people_count": 376,
  "company_revenue": 142174379
}
```
**Expected**: 98.1% score, Ideal Target, 11.17% ratio

```json
{
  "company_name": "Test Low Priority",
  "marketing_headcount": 3,
  "people_count": 1000,
  "company_revenue": 50000000
}
```
**Expected**: Low score (~18%), Low Priority, 0.30% ratio

---

## 📞 Need Help?

1. **API not responding**: Check Railway logs
2. **Wrong scores**: Verify input data (especially people_count)
3. **Clay mapping**: Review column names match exactly

---

## ✅ Quick Checklist

- [ ] API deployed to Railway
- [ ] `/health` endpoint returns 200
- [ ] Test with sample data works
- [ ] Clay HTTP API column created
- [ ] Request body mapped correctly
- [ ] Response fields extracted
- [ ] Filter for Ideal Targets works
- [ ] Sort by Close Score or Expected Value
- [ ] Ready to score leads!

---

**🚀 You're all set! Start scoring your leads in Clay!**

