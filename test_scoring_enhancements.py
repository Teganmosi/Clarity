"""
Test script to verify the enhanced lead scoring with explanations
"""
import sys
sys.path.append('backend')

from app.scoring import score_leads

# Test lead with comprehensive data
test_leads = [
    {
        "name": "Sarah Johnson",
        "email": "sarah.j@startupxyz.com",
        "company": "StartupXYZ",
        "phone": "+1987654321",
        "title": "VP Marketing",
        "source": "referral",
        "campaign": "decision",
        "medium": "referral",
        "past_interactions": 12,
        "pages_visited": 40,
        "time_on_site": 25.0,
        "company_size": "small",
        "industry": "SaaS",
        "budget": "high"
    },
    {
        "name": "John Doe",
        "email": "john@gmail.com",
        "company": "Unknown",
        "source": "paid_ads",
        "campaign": "awareness",
        "medium": "cpc",
        "past_interactions": 1,
        "pages_visited": 2,
        "time_on_site": 1.5,
        "budget": "low"
    }
]

print("Testing Enhanced Lead Scoring Engine\n")
print("=" * 80)

scored_leads = score_leads(test_leads)

for i, lead in enumerate(scored_leads, 1):
    print(f"\n### Lead {i}: {lead['name']}")
    print(f"Score: {lead['score']} ({lead['score_category'].upper()})")
    print(f"Confidence: {lead['confidence_label']} ({lead['confidence']*100:.0f}%)")
    print(f"Data Points: {lead['data_points']}/{lead['total_factors']}")
    
    print(f"\n📊 Score Breakdown:")
    print(f"  Base Score: {lead['explanation']['base_score']}")
    
    if lead['explanation']['top_positive_factors']:
        print(f"\n  ✅ Top Positive Factors:")
        for factor in lead['explanation']['top_positive_factors']:
            print(f"    • {factor['factor']}: +{factor['contribution']} pts ({factor['percentage']})")
    
    if lead['explanation']['top_negative_factors']:
        print(f"\n  ⚠️ Negative Factors:")
        for factor in lead['explanation']['top_negative_factors']:
            print(f"    • {factor['factor']}: {factor['contribution']} pts ({factor['percentage']})")
    
    print(f"\n💡 Recommendation:")
    rec = lead['recommendation']
    print(f"  {rec['icon']} {rec['action']}")
    print(f"  Priority: {rec['priority'].upper()}")
    print(f"  Timeline: {rec['timeline']}")
    print(f"  Reason: {rec['reason']}")
    
    print("\n" + "=" * 80)

print("\n✅ Test completed successfully!")
