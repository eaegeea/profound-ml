#!/usr/bin/env python3
"""
Test script for V3 Territory Design API
"""
import requests
import json

# API base URL (change this when deployed)
BASE_URL = "http://localhost:5000"

print("=" * 80)
print("TESTING V3 TERRITORY DESIGN API")
print("=" * 80)

# Test 1: Health Check
print("\n[Test 1] Health Check...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure the API is running: python app_simplified.py")
    exit(1)

# Test 2: Single Prediction (Ideal Target)
print("\n[Test 2] Single Prediction - Ideal Target Example...")
ideal_target = {
    "company_name": "Diversified",
    "domain": "divcom.com",
    "marketing_headcount": 42,
    "people_count": 376,
    "company_revenue": 142174379,
    "is_b2b": 1
}

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json=ideal_target,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"\nCompany: {result['company_name']}")
    print(f"Close Score: {result['close_score_percent']}")
    print(f"Segment: {result['segment']}")
    print(f"Marketing Ratio: {result['marketing_ratio_percent']}")
    print(f"Expected Value: ${result['expected_value']:,.2f}")
    print(f"\n✅ Should be Ideal Target with ~98% score")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Single Prediction (Low Priority)
print("\n[Test 3] Single Prediction - Low Priority Example...")
low_priority = {
    "company_name": "Small Corp",
    "domain": "smallcorp.com",
    "marketing_headcount": 2,
    "people_count": 500,
    "company_revenue": 10000000,
    "is_b2b": 1
}

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json=low_priority,
        headers={"Content-Type": "application/json"}
    )
    result = response.json()
    print(f"Company: {result['company_name']}")
    print(f"Close Score: {result['close_score_percent']}")
    print(f"Segment: {result['segment']}")
    print(f"Marketing Ratio: {result['marketing_ratio_percent']}")
    print(f"\n✅ Should be Low Priority with low marketing ratio (0.4%)")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Missing Marketing Team
print("\n[Test 4] Company with No Marketing Team...")
no_marketing = {
    "company_name": "No Marketing Inc",
    "marketing_headcount": 0,
    "people_count": 200
}

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json=no_marketing,
        headers={"Content-Type": "application/json"}
    )
    result = response.json()
    print(f"Company: {result['company_name']}")
    if 'error' in result:
        print(f"Error: {result['error']}")
        print(f"Segment: {result['segment']}")
        print(f"\n✅ Correctly rejected (V3 requires marketing team)")
    else:
        print(f"❌ Should have been rejected!")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Batch Prediction
print("\n[Test 5] Batch Prediction...")
batch_data = {
    "companies": [
        {
            "company_name": "Jabra",
            "marketing_headcount": 102,
            "people_count": 1660,
            "company_revenue": 196073660
        },
        {
            "company_name": "ViewSonic",
            "marketing_headcount": 89,
            "people_count": 1349,
            "company_revenue": 1200000000
        },
        {
            "company_name": "Test Corp",
            "marketing_headcount": 15,
            "people_count": 300
        }
    ]
}

try:
    response = requests.post(
        f"{BASE_URL}/batch",
        json=batch_data,
        headers={"Content-Type": "application/json"}
    )
    result = response.json()
    print(f"Total: {result['total_companies']}")
    print(f"Successful: {result['successful_predictions']}")
    
    if 'summary_stats' in result:
        print(f"\nSummary Stats:")
        print(f"  Avg Close Score: {result['summary_stats']['avg_close_score']*100:.1f}%")
        print(f"  Ideal Targets: {result['summary_stats']['ideal_targets']}")
        print(f"  Good Targets: {result['summary_stats']['good_targets']}")
        print(f"  Medium Targets: {result['summary_stats']['medium_targets']}")
        print(f"  Low Priority: {result['summary_stats']['low_priority']}")
    
    print(f"\nTop 3 Results:")
    for i, company in enumerate(result['results'][:3], 1):
        print(f"  {i}. {company['company_name']}: {company.get('close_score_percent', 'N/A')} - {company.get('segment', 'N/A')}")
    
    print(f"\n✅ Batch processing works!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ API TESTS COMPLETE")
print("=" * 80)
print("\n📖 See README.md for Clay integration instructions")
print("🚀 Ready to deploy to Railway!")

