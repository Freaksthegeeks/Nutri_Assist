#!/usr/bin/env python3
"""
Quick test for the nlp_analyzer fix
"""

try:
    from nlp_analyzer import nlp_analyzer
    print("✅ NLP analyzer imports successfully")
    
    # Test with ingredients that might cause API issues
    test_ingredients = ['chicken breast', 'broccoli', 'rice']
    test_profile = {
        'health_goals': ['weight_loss'],
        'allergens': ['dairy']
    }
    
    print("🔄 Testing meal analysis...")
    analysis = nlp_analyzer.analyze_meal_nutrition(test_ingredients, test_profile)
    
    if analysis:
        print("✅ Analysis completed successfully")
        print(f"📊 Nutrition score: {analysis.get('nutrition_score', 'N/A')}")
        print(f"🥗 Categories: {len(analysis.get('category_analysis', {}))}")
        
        if analysis.get('detailed_nutrition'):
            print("✅ Detailed nutrition data available")
        
        if analysis.get('meal_summary'):
            summary = analysis['meal_summary']
            print(f"📋 Total calories: {summary.get('total_calories', 'N/A')}")
        
        print("🎉 NLP analyzer is working correctly!")
    else:
        print("❌ Failed to analyze meal")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()