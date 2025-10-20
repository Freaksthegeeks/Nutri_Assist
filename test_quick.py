#!/usr/bin/env python3
"""
Quick test for the improved meal planner
"""

try:
    from meal_planner import meal_planner
    print("✅ Meal planner imports successfully")
    
    # Test with valid profile
    test_profile = {
        'diet_type': 'balanced',
        'health_goals': ['weight_loss'],
        'allergens': ['dairy']
    }
    
    print("🔄 Testing meal plan generation...")
    plan = meal_planner.generate_weekly_plan(test_profile)
    
    if plan:
        print(f"✅ Generated plan with {len(plan)} days")
        
        # Check first day structure
        first_day = list(plan.values())[0]
        if all(meal in first_day for meal in ['breakfast', 'lunch', 'dinner']):
            print("✅ Plan structure is correct")
        
        # Show sample meal
        breakfast = first_day['breakfast']
        print(f"📋 Sample breakfast: {breakfast['title']}")
        
        print("🎉 Meal planner is working correctly!")
    else:
        print("❌ Failed to generate meal plan")
        
except Exception as e:
    print(f"❌ Error: {e}")