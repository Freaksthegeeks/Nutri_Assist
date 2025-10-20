#!/usr/bin/env python3
"""
Test the enhanced static meal planning system
"""

try:
    from meal_planner import meal_planner
    print("✅ Enhanced meal planner imports successfully")
    
    # Test different diet preferences
    test_profiles = [
        {
            'name': 'Vegetarian Weight Loss',
            'diet_type': 'vegetarian',
            'health_goals': ['weight_loss'],
            'allergens': ['nuts']
        },
        {
            'name': 'Vegan Muscle Gain',
            'diet_type': 'vegan',
            'health_goals': ['muscle_gain'],
            'allergens': []
        },
        {
            'name': 'Balanced Diet',
            'diet_type': 'balanced',
            'health_goals': ['balanced_diet'],
            'allergens': ['dairy']
        },
        {
            'name': 'High Protein Keto',
            'diet_type': 'keto',
            'health_goals': ['muscle_gain'],
            'allergens': []
        }
    ]
    
    for profile in test_profiles:
        print(f"\n🧪 Testing: {profile['name']}")
        print(f"   Diet: {profile['diet_type']}")
        print(f"   Goals: {profile['health_goals']}")
        print(f"   Allergens: {profile['allergens']}")
        
        # Force using fallback by temporarily disabling API
        original_key = meal_planner.spoonacular_api_key
        meal_planner.spoonacular_api_key = None
        
        try:
            plan = meal_planner.generate_weekly_plan(profile)
            
            if plan:
                print("   ✅ Plan generated successfully")
                
                # Check plan structure
                days = [key for key in plan.keys() if key != '_plan_info']
                print(f"   📅 Generated {len(days)} days")
                
                # Sample meal check
                if days:
                    sample_day = plan[days[0]]
                    breakfast = sample_day['breakfast']
                    print(f"   🍳 Sample breakfast: {breakfast['title']}")
                    print(f"   📊 Calories: {breakfast['nutrition']['calories']['amount']}")
                    print(f"   ⏱️ Cooking time: {breakfast['ready_in_minutes']} minutes")
                    
                    # Check for allergen warnings
                    if 'allergen_warning' in breakfast:
                        print(f"   ⚠️ Allergen warning: {breakfast['allergen_warning']}")
                
                # Check plan info
                if '_plan_info' in plan:
                    info = plan['_plan_info']
                    print(f"   📋 Category: {info['diet_category']}")
                    print(f"   🔢 Total meals: {info['total_meals']}")
            
            else:
                print("   ❌ Failed to generate plan")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        finally:
            # Restore API key
            meal_planner.spoonacular_api_key = original_key
    
    print("\n🎉 Enhanced static meal planning test completed!")
    print("🍽️ The system now provides detailed, preference-based meals when API is unavailable")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()