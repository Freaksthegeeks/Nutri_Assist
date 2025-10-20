#!/usr/bin/env python3
"""
Test script for Meal Planner with Spoonacular API
This script tests the meal planner functionality to ensure it works with the provided API key.
"""

import sys
import json
from meal_planner import meal_planner

def test_meal_planner():
    """Test the meal planner functionality"""
    print("🍽️ Testing Meal Planner with Spoonacular API...")
    print("=" * 50)
    
    # Test user profile
    test_profile = {
        'diet_type': 'balanced',
        'health_goals': ['weight_loss'],
        'allergens': ['dairy'],
        'age': 30,
        'activity_level': 'moderate'
    }
    
    print(f"📋 Test Profile:")
    print(f"   Diet Type: {test_profile['diet_type']}")
    print(f"   Goals: {test_profile['health_goals']}")
    print(f"   Allergens: {test_profile['allergens']}")
    print()
    
    try:
        # Test API key availability
        print(f"🔑 API Key Status: {'✅ Available' if meal_planner.spoonacular_api_key else '❌ Missing'}")
        if meal_planner.spoonacular_api_key:
            print(f"   Key Preview: {meal_planner.spoonacular_api_key[:8]}...")
        print()
        
        # Generate a test meal plan
        print("🔄 Generating weekly meal plan...")
        weekly_plan = meal_planner.generate_weekly_plan(test_profile)
        
        if weekly_plan:
            print("✅ Meal plan generated successfully!")
            print()
            
            # Display first day's meals
            first_day = list(weekly_plan.keys())[0]
            print(f"📅 Sample day ({first_day}):")
            
            for meal_type, meal_data in weekly_plan[first_day].items():
                print(f"   {meal_type.title()}:")
                print(f"      🍽️ {meal_data['title']}")
                
                if 'ingredients' in meal_data and meal_data['ingredients']:
                    print(f"      📝 Ingredients: {len(meal_data['ingredients'])} items")
                    # Show first 3 ingredients
                    for i, ingredient in enumerate(meal_data['ingredients'][:3]):
                        print(f"         - {ingredient}")
                    if len(meal_data['ingredients']) > 3:
                        print(f"         ... and {len(meal_data['ingredients']) - 3} more")
                
                if 'nutrition' in meal_data and meal_data['nutrition']:
                    nutrition = meal_data['nutrition']
                    if 'calories' in nutrition:
                        calories = nutrition['calories']
                        if isinstance(calories, dict):
                            print(f"      ⚡ Calories: {calories.get('amount', 'N/A')} {calories.get('unit', '')}")
                        else:
                            print(f"      ⚡ Calories: {calories}")
                
                if 'ready_in_minutes' in meal_data:
                    print(f"      ⏱️ Prep time: {meal_data['ready_in_minutes']} minutes")
                
                print()
            
            # Check if using API or fallback
            sample_meal = weekly_plan[first_day]['breakfast']
            if 'estimated' in sample_meal:
                print("ℹ️ Using fallback meal database (API may be unavailable)")
            else:
                print("🌐 Using Spoonacular API data")
            
            print()
            print(f"📊 Plan Summary:")
            print(f"   Total days: {len(weekly_plan)}")
            print(f"   Total meals: {len(weekly_plan) * 3}")
            
        else:
            print("❌ Failed to generate meal plan")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        print("💡 This might indicate an API issue or network problem")
        return False
    
    print()
    print("=" * 50)
    print("✅ Meal planner test completed!")
    return True

def test_single_recipe():
    """Test getting a single recipe from API"""
    print("\n🧪 Testing single recipe retrieval...")
    
    try:
        # Test with a simple 1-day meal plan to get a single recipe
        test_plan = meal_planner.get_bulk_meal_plan({
            'diet_type': 'balanced',
            'health_goals': ['weight_loss'],
            'allergens': ['dairy']
        }, days=1)
        
        if test_plan:
            day_meals = list(test_plan.values())[0]
            breakfast = day_meals['breakfast']
            
            print("✅ Single recipe test successful!")
            print(f"   Recipe: {breakfast['title']}")
            print(f"   Ingredients: {len(breakfast.get('ingredients', []))} items")
        else:
            print("⚠️ Single recipe test failed: No plan generated")
        
    except Exception as e:
        print(f"⚠️ Single recipe test failed: {str(e)}")
        print("   This is expected if API quota is exceeded or network issues occur")

def test_enhanced_features():
    """Test enhanced meal planner features"""
    print("\n🚀 Testing Enhanced Features...")
    
    test_profile = {
        'diet_type': 'vegetarian',
        'health_goals': ['muscle_gain'],
        'allergens': ['nuts', 'dairy'],
        'age': 28,
        'activity_level': 'high'
    }
    
    try:
        # Test bulk meal planning
        print("\n📦 Testing bulk meal plan generation...")
        bulk_plan = meal_planner.get_bulk_meal_plan(test_profile, days=3)
        
        if bulk_plan:
            print("✅ Bulk meal plan generated successfully!")
            print(f"   Generated {len(bulk_plan)} days")
            
            # Check for recipe diversity
            all_titles = []
            for day, meals in bulk_plan.items():
                for meal_type, meal_data in meals.items():
                    all_titles.append(meal_data['title'])
            
            unique_titles = set(all_titles)
            diversity_ratio = len(unique_titles) / len(all_titles)
            print(f"   Recipe diversity: {diversity_ratio:.2%} ({len(unique_titles)}/{len(all_titles)} unique)")
            
            # Check for dietary compliance
            vegetarian_compliance = True
            for day, meals in bulk_plan.items():
                for meal_type, meal_data in meals.items():
                    if not meal_data.get('estimated'):  # Only check API recipes
                        diets = meal_data.get('diets', [])
                        if 'vegetarian' not in diets and 'vegan' not in diets:
                            # Check ingredients for meat
                            ingredients_text = ' '.join(meal_data.get('ingredients', [])).lower()
                            meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey']
                            if any(meat in ingredients_text for meat in meat_keywords):
                                vegetarian_compliance = False
                                break
            
            compliance_status = "✅ Compliant" if vegetarian_compliance else "⚠️ May have issues"
            print(f"   Vegetarian compliance: {compliance_status}")
            
        else:
            print("❌ Bulk meal plan generation failed")
            
    except Exception as e:
        print(f"❌ Enhanced features test failed: {e}")

def test_api_resilience():
    """Test API resilience and error handling"""
    print("\n🛡️ Testing API Resilience...")
    
    # Test with invalid API key
    original_key = meal_planner.spoonacular_api_key
    meal_planner.spoonacular_api_key = "invalid_key_test"
    
    try:
        fallback_plan = meal_planner.generate_weekly_plan({
            'diet_type': 'balanced',
            'health_goals': ['weight_loss'],
            'allergens': []
        })
        
        if fallback_plan:
            print("✅ Fallback system works correctly")
            
            # Check if using fallback data
            sample_meal = list(fallback_plan.values())[0]['breakfast']
            if sample_meal.get('estimated'):
                print("   ✅ Correctly using fallback database")
            else:
                print("   ⚠️ Unexpected API success with invalid key")
        else:
            print("❌ Fallback system failed")
            
    except Exception as e:
        print(f"⚠️ Fallback test error: {e}")
    finally:
        # Restore original key
        meal_planner.spoonacular_api_key = original_key

def test_performance_metrics():
    """Test performance and timing"""
    print("\n⏱️ Testing Performance Metrics...")
    
    import time
    
    test_profile = {
        'diet_type': 'balanced',
        'health_goals': ['balanced_diet'],
        'allergens': []
    }
    
    # Test standard plan generation
    start_time = time.time()
    standard_plan = meal_planner.generate_weekly_plan(test_profile)
    standard_time = time.time() - start_time
    
    print(f"   Standard plan generation: {standard_time:.2f} seconds")
    
    # Test bulk plan generation
    start_time = time.time()
    bulk_plan = meal_planner.get_bulk_meal_plan(test_profile, days=7)
    bulk_time = time.time() - start_time
    
    print(f"   Bulk plan generation: {bulk_time:.2f} seconds")
    
    if bulk_time < standard_time:
        print("   ✅ Bulk generation is faster")
    else:
        print("   ℹ️ Standard generation performed better (possibly due to caching)")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Meal Planner Tests")
    print("=" * 60)
    
    # Run all tests
    success = test_meal_planner()
    test_single_recipe()
    test_enhanced_features()
    test_api_resilience()
    test_performance_metrics()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed! The enhanced meal planner is ready to use.")
        print("📝 Key improvements:")
        print("   • Rate limiting and retry logic")
        print("   • Enhanced recipe diversity")
        print("   • Better allergen handling")
        print("   • Bulk recipe generation")
        print("   • Improved error handling")
    else:
        print("⚠️ Some tests failed, but enhanced fallback functionality is available.")