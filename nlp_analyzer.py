import spacy
import nltk
from textblob import TextBlob
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import json
import os
import warnings

# Set environment variables to suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logging

# Suppress PyTorch warnings more comprehensively
warnings.filterwarnings("ignore", message=".*Tried to instantiate class.*")
warnings.filterwarnings("ignore", message=".*FutureWarning.*")
warnings.filterwarnings("ignore", message=".*UserWarning.*")

# Handle transformers imports more gracefully
TRANSFORMERS_AVAILABLE = False

# Suppress TensorFlow warnings
try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
except ImportError:
    pass

import nltk
from textblob import TextBlob
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class NLPNutritionAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Initialize models
        self.nlp = self._load_spacy_model()
        
        # Try to load transformers
        self._load_transformers()
        
        self.nutritionix_headers = {
            'x-app-id': os.getenv('NUTRITIONIX_APP_ID'),
            'x-app-key': os.getenv('NUTRITIONIX_API_KEY'),
            'Content-Type': 'application/json'
        }
        
        # CalorieNinja API setup
        self.calorie_ninja_api_key = os.getenv('CALORIE_NINJA_API_KEY')
        self.calorie_ninja_headers = {
            'X-Api-Key': self.calorie_ninja_api_key,
            'Content-Type': 'application/json'
        }
        self.calorie_ninja_url = 'https://api.calorieninjas.com/v1/nutrition'
        
        # Nutrition knowledge base
        self.nutrition_knowledge = self._build_nutrition_knowledge()
        
        # Enhanced ingredient categories with international foods
        self.ingredient_categories = {
            'proteins': [
                'chicken', 'beef', 'fish', 'salmon', 'tuna', 'eggs', 'tofu', 'beans', 'lentils', 'quinoa',
                'pork', 'duck', 'lamb', 'shrimp', 'crab', 'lobster', 'squid', 'octopus', 'tempeh', 'seitan',
                'paneer', 'kefir', 'greek yogurt', 'cottage cheese', 'turkey', 'venison'
            ],
            'carbs': [
                'rice', 'pasta', 'bread', 'potato', 'oats', 'quinoa', 'barley', 'wheat',
                'noodles', 'soba', 'udon', 'rice noodles', 'couscous', 'bulgur', 'farro', 'millet',
                'plantain', 'taro', 'yam', 'corn', 'polenta', 'breadfruit', 'chapati', 'naan'
            ],
            'vegetables': [
                'broccoli', 'spinach', 'carrot', 'tomato', 'onion', 'pepper', 'cucumber', 'lettuce',
                'kale', 'arugula', 'bok choy', 'napa cabbage', 'shiitake mushroom', 'enoki mushroom',
                'okra', 'eggplant', 'zucchini', 'daikon', 'lotus root', 'bamboo shoots', 'seaweed',
                'kimchi', 'sauerkraut', 'jalapeno', 'habanero', 'poblano', 'bell pepper'
            ],
            'fruits': [
                'apple', 'banana', 'orange', 'berry', 'grape', 'mango', 'pineapple', 'avocado',
                'papaya', 'guava', 'lychee', 'rambutan', 'durian', 'mangosteen', 'dragon fruit',
                'passion fruit', 'persimmon', 'feijoa', 'ackee', 'soursop', 'longan', 'pomegranate'
            ],
            'dairy': [
                'milk', 'cheese', 'yogurt', 'butter', 'cream', 'ghee', 'paneer', 'ricotta',
                'parmesan', 'mozzarella', 'feta', 'blue cheese', 'camembert', 'brie', 'cheddar'
            ],
            'fats': [
                'oil', 'butter', 'nuts', 'seeds', 'avocado', 'olive', 'coconut oil', 'sesame oil',
                'olive oil', 'canola oil', 'sunflower oil', 'flaxseed oil', 'walnut oil', 'peanut oil',
                'almonds', 'cashews', 'pistachios', 'pecans', 'macadamia', 'hazelnuts', 'pine nuts',
                'chia seeds', 'flax seeds', 'pumpkin seeds', 'sunflower seeds', 'sesame seeds'
            ]
        }
    
    def _load_transformers(self):
        """Load transformer models with proper error handling"""
        global TRANSFORMERS_AVAILABLE
        try:
            from transformers import pipeline
            from sentence_transformers import SentenceTransformer
            # type: ignore
            self.sentiment_analyzer = pipeline("sentiment-analysis")  # type: ignore
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')  # type: ignore
            TRANSFORMERS_AVAILABLE = True
            print("✅ Transformers and sentence-transformers loaded successfully!")
        except ImportError as e:
            print("⚠️ Transformers and sentence-transformers not available. Using fallback NLP methods.")
            print(f"Import error: {e}")
            self.sentiment_analyzer = None
            self.sentence_model = None
            TRANSFORMERS_AVAILABLE = False
        except Exception as e:
            print(f"⚠️ Warning: Transformers available but encountered an issue: {e}")
            self.sentiment_analyzer = None
            self.sentence_model = None
            TRANSFORMERS_AVAILABLE = False

    def _load_spacy_model(self):
        """Load spaCy model, download if not available"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            return spacy.load("en_core_web_sm")
    
    def _build_nutrition_knowledge(self):
        """Build nutrition knowledge base"""
        return {
            'high_protein': ['chicken', 'fish', 'eggs', 'tofu', 'beans', 'lentils', 'quinoa', 'greek yogurt'],
            'low_carb': ['spinach', 'broccoli', 'cauliflower', 'zucchini', 'avocado', 'nuts', 'fish'],
            'high_fiber': ['beans', 'lentils', 'oats', 'quinoa', 'broccoli', 'apple', 'berries'],
            'heart_healthy': ['salmon', 'avocado', 'nuts', 'olive oil', 'oats', 'berries'],
            'muscle_gain': ['chicken breast', 'eggs', 'greek yogurt', 'quinoa', 'sweet potato'],
            'weight_loss': ['spinach', 'broccoli', 'chicken breast', 'fish', 'berries', 'cucumber'],
            'anti_inflammatory': ['turmeric', 'ginger', 'berries', 'fatty fish', 'leafy greens']
        }
    
    def extract_ingredients(self, text):
        """Extract ingredients from text using NLP with enhanced international food recognition"""
        doc = self.nlp(text.lower())
        ingredients = []
        
        # Extract named entities with FOOD label
        for ent in doc.ents:
            if ent.label_ == 'FOOD':
                ingredients.append(ent.text)
        
        # Extract potential ingredients from noun chunks (more accurate than individual nouns)
        for chunk in doc.noun_chunks:
            # Clean the chunk text
            cleaned_chunk = re.sub(r'[^\w\s]', '', chunk.text).strip()
            if (len(cleaned_chunk) > 2 and 
                not any(stopword in cleaned_chunk for stopword in ['tablespoon', 'teaspoon', 'cup', 'ounce', 'pound', 'gram', 'liter', 'piece', 'slice'])):
                ingredients.append(cleaned_chunk)
        
        # Also check individual tokens for food-related terms
        for token in doc:
            if (token.pos_ == 'NOUN' and 
                not token.is_stop and 
                len(token.text) > 2 and
                self._is_likely_ingredient(token.text)):
                ingredients.append(token.text)
        
        # Remove duplicates and clean
        ingredients = list(set([ing.strip() for ing in ingredients]))
        
        # Validate ingredients against known food items and common international foods
        validated_ingredients = []
        for ing in ingredients:
            if self._validate_ingredient(ing):
                validated_ingredients.append(ing)
        
        return validated_ingredients
    
    def _is_likely_ingredient(self, word):
        """Check if a word is likely an ingredient"""
        # Check against known ingredient categories
        for category, items in self.ingredient_categories.items():
            if any(word in item or item in word for item in items):
                return True
        
        # Additional heuristics
        food_keywords = ['meat', 'vegetable', 'fruit', 'grain', 'spice', 'herb']
        return any(keyword in word for keyword in food_keywords)
    
    def _validate_ingredient(self, ingredient):
        """Validate if text is actually an ingredient"""
        # Simple validation - could be enhanced with ML model
        non_ingredients = ['cup', 'tablespoon', 'teaspoon', 'pound', 'ounce', 'gram', 'liter']
        return ingredient not in non_ingredients and len(ingredient) > 2
    
    def _get_nutrition_data_from_calorie_ninja(self, ingredient):
        """Get nutrition data for an ingredient from CalorieNinja API with fallback to local data"""
        try:
            params = {'query': ingredient}
            response = requests.get(
                self.calorie_ninja_url,
                headers=self.calorie_ninja_headers,
                params=params,
                timeout=15  # Increased timeout from 5 to 15 seconds
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    item = data['items'][0]
                    return {
                        'calories': item.get('calories', 0),
                        'protein_g': item.get('protein_g', 0),
                        'fat_total_g': item.get('fat_total_g', 0),
                        'carbohydrates_total_g': item.get('carbohydrates_total_g', 0),
                        'fiber_g': item.get('fiber_g', 0),
                        'sugar_g': item.get('sugar_g', 0)
                    }
            # If API returns no data, fall back to local estimation
            return self._estimate_nutrition_locally(ingredient)
        except Exception as e:
            print(f"Error fetching data from CalorieNinja for {ingredient}: {e}")
            # On any error, use local estimation as fallback
            return self._estimate_nutrition_locally(ingredient)
    
    def _estimate_nutrition_locally(self, ingredient):
        """Estimate nutrition values based on ingredient category as fallback"""
        # Default values
        base_values = {
            'calories': 0,
            'protein_g': 0,
            'fat_total_g': 0,
            'carbohydrates_total_g': 0,
            'fiber_g': 0,
            'sugar_g': 0
        }
        
        ingredient_lower = ingredient.lower()
        
        # Estimate based on category
        for category, items in self.ingredient_categories.items():
            if any(item in ingredient_lower for item in items):
                if category == 'proteins':
                    base_values.update({'calories': 150, 'protein_g': 25, 'fat_total_g': 7, 'carbohydrates_total_g': 0})
                elif category == 'carbs':
                    base_values.update({'calories': 200, 'protein_g': 4, 'fat_total_g': 1, 'carbohydrates_total_g': 45, 'fiber_g': 3})
                elif category == 'vegetables':
                    base_values.update({'calories': 25, 'protein_g': 1, 'fat_total_g': 0, 'carbohydrates_total_g': 5, 'fiber_g': 2})
                elif category == 'fruits':
                    base_values.update({'calories': 60, 'protein_g': 1, 'fat_total_g': 0, 'carbohydrates_total_g': 15, 'fiber_g': 2, 'sugar_g': 10})
                elif category == 'dairy':
                    base_values.update({'calories': 100, 'protein_g': 8, 'fat_total_g': 6, 'carbohydrates_total_g': 10})
                elif category == 'fats':
                    base_values.update({'calories': 120, 'protein_g': 0, 'fat_total_g': 14, 'carbohydrates_total_g': 0})
                break
        
        return base_values
    
    def _enrich_ingredient_with_api_data(self, ingredient, api_data):
        """Enrich ingredient analysis with API nutrition data"""
        if not api_data:
            # Return fallback analysis for ingredient
            return self._get_fallback_nutrition_data(ingredient)
        
        try:
            # Safely extract values with defaults
            calories = api_data.get('calories', 0)
            protein_g = api_data.get('protein_g', 0)
            fat_g = api_data.get('fat_total_g', 0)
            carbs_g = api_data.get('carbohydrates_total_g', 0)
            fiber_g = api_data.get('fiber_g', 0)
            sugar_g = api_data.get('sugar_g', 0)
            
            # Calculate nutritional score based on macronutrients
            total_macros = protein_g + fat_g + carbs_g
            protein_ratio = protein_g / (total_macros + 1) if total_macros > 0 else 0
            
            return {
                'calories': calories,
                'protein_g': protein_g,
                'fat_g': fat_g,
                'carbs_g': carbs_g,
                'fiber_g': fiber_g,
                'sugar_g': sugar_g,
                'protein_ratio': protein_ratio,
                'is_high_protein': protein_ratio > 0.3,
                'is_low_carb': carbs_g < 10,
                'is_healthy_fat': self._calculate_healthy_fat_ratio(api_data)
            }
            
        except (KeyError, TypeError, ValueError) as e:
            # Log error and return fallback data
            print(f"Error processing API data for {ingredient}: {e}")
            return self._get_fallback_nutrition_data(ingredient)
    
    def _get_fallback_nutrition_data(self, ingredient):
        """Provide fallback nutrition data when API fails"""
        # Get basic categorization
        base_values = {'calories': 50, 'protein_g': 2, 'fat_total_g': 1, 'carbohydrates_total_g': 8, 'fiber_g': 1, 'sugar_g': 2}
        
        # Adjust based on ingredient category
        for category, items in self.ingredient_categories.items():
            if any(item in ingredient.lower() for item in items):
                if category == 'proteins':
                    base_values.update({'calories': 150, 'protein_g': 25, 'fat_total_g': 5, 'carbohydrates_total_g': 0, 'fiber_g': 0, 'sugar_g': 0})
                elif category in ['carbs', 'grains']:
                    base_values.update({'calories': 100, 'protein_g': 3, 'fat_total_g': 1, 'carbohydrates_total_g': 20, 'fiber_g': 2, 'sugar_g': 1})
                elif category == 'vegetables':
                    base_values.update({'calories': 25, 'protein_g': 1, 'fat_total_g': 0, 'carbohydrates_total_g': 5, 'fiber_g': 2, 'sugar_g': 3})
                elif category == 'fruits':
                    base_values.update({'calories': 60, 'protein_g': 1, 'fat_total_g': 0, 'carbohydrates_total_g': 15, 'fiber_g': 2, 'sugar_g': 10})
                elif category == 'dairy':
                    base_values.update({'calories': 100, 'protein_g': 8, 'fat_total_g': 6, 'carbohydrates_total_g': 10, 'fiber_g': 0, 'sugar_g': 8})
                elif category == 'fats':
                    base_values.update({'calories': 120, 'protein_g': 0, 'fat_total_g': 14, 'carbohydrates_total_g': 0, 'fiber_g': 0, 'sugar_g': 0})
                break
        
        # Calculate derived values
        total_macros = base_values['protein_g'] + base_values['fat_total_g'] + base_values['carbohydrates_total_g']
        protein_ratio = base_values['protein_g'] / (total_macros + 1) if total_macros > 0 else 0
        
        return {
            'calories': base_values['calories'],
            'protein_g': base_values['protein_g'],
            'fat_g': base_values['fat_total_g'],
            'carbs_g': base_values['carbohydrates_total_g'],
            'fiber_g': base_values['fiber_g'],
            'sugar_g': base_values['sugar_g'],
            'protein_ratio': protein_ratio,
            'is_high_protein': protein_ratio > 0.3,
            'is_low_carb': base_values['carbohydrates_total_g'] < 10,
            'is_healthy_fat': True,  # Default to healthy for fallback data
            'estimated': True  # Flag to indicate this is estimated data
        }
    
    def _calculate_healthy_fat_ratio(self, api_data):
        """Safely calculate if fat content is healthy (low saturated fat ratio)"""
        try:
            total_fat = api_data.get('fat_total_g', 0)
            saturated_fat = api_data.get('saturated_fat_g', 0)
            
            if total_fat <= 0:
                return True  # No fat, considered healthy
            
            # Check if saturated fat data is available
            if saturated_fat is None:
                return True  # Assume healthy if we don't have saturated fat data
            
            # Healthy if saturated fat is less than 30% of total fat
            return (saturated_fat / total_fat) < 0.3
            
        except (KeyError, TypeError, ZeroDivisionError):
            # Default to True if we can't calculate
            return True
    
    def analyze_meal_nutrition(self, ingredients, user_profile=None):
        """Analyze nutritional content of a meal with enhanced accuracy using external APIs"""
        analysis = {
            'ingredients': ingredients,
            'nutrition_score': 0,
            'category_analysis': {},
            'detailed_nutrition': {},
            'recommendations': [],
            'allergen_warnings': [],
            'nutritional_benefits': [],
            'meal_summary': {}
        }
        
        # Categorize ingredients
        categorized = self._categorize_ingredients(ingredients)
        analysis['category_analysis'] = categorized
        
        # Get detailed nutrition data from CalorieNinja API
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        
        for ingredient in ingredients:
            # First try to get data from CalorieNinja API
            api_data = self._get_nutrition_data_from_calorie_ninja(ingredient)
            
            # Enrich with API data or use basic analysis
            enriched_data = self._enrich_ingredient_with_api_data(ingredient, api_data)
            analysis['detailed_nutrition'][ingredient] = enriched_data
            
            # Accumulate totals
            total_calories += enriched_data.get('calories', 0)
            total_protein += enriched_data.get('protein_g', 0)
            total_carbs += enriched_data.get('carbs_g', 0)
            total_fat += enriched_data.get('fat_g', 0)
            total_fiber += enriched_data.get('fiber_g', 0)
        
        # Create meal summary
        analysis['meal_summary'] = {
            'total_calories': total_calories,
            'total_protein_g': total_protein,
            'total_carbs_g': total_carbs,
            'total_fat_g': total_fat,
            'total_fiber_g': total_fiber,
            'protein_percentage': (total_protein * 4 / total_calories * 100) if total_calories > 0 else 0,
            'carb_percentage': (total_carbs * 4 / total_calories * 100) if total_calories > 0 else 0,
            'fat_percentage': (total_fat * 9 / total_calories * 100) if total_calories > 0 else 0
        }
        
        # Check for nutritional balance
        balance_score = self._calculate_balance_score(categorized)
        analysis['nutrition_score'] = balance_score
        
        # Generate recommendations based on user profile
        if user_profile:
            recommendations = self._generate_recommendations(categorized, user_profile)
            analysis['recommendations'] = recommendations
            
            # Check allergens
            allergen_warnings = self._check_allergens(ingredients, user_profile.get('allergens', []))
            analysis['allergen_warnings'] = allergen_warnings
        
        # Identify nutritional benefits
        benefits = self._identify_nutritional_benefits(ingredients)
        analysis['nutritional_benefits'] = benefits
        
        return analysis
    
    def _categorize_ingredients(self, ingredients):
        """Categorize ingredients into food groups"""
        categorized = {category: [] for category in self.ingredient_categories.keys()}
        
        for ingredient in ingredients:
            for category, items in self.ingredient_categories.items():
                if any(item in ingredient.lower() for item in items):
                    categorized[category].append(ingredient)
                    break
        
        return categorized
    
    def _calculate_balance_score(self, categorized):
        """Calculate nutritional balance score"""
        score = 0
        total_categories = len([cat for cat, items in categorized.items() if items])
        
        # Bonus for having multiple food groups
        if total_categories >= 3:
            score += 30
        elif total_categories >= 2:
            score += 20
        
        # Bonus for having proteins
        if categorized['proteins']:
            score += 25
        
        # Bonus for having vegetables
        if categorized['vegetables']:
            score += 25
        
        # Bonus for variety within categories
        for category, items in categorized.items():
            if len(items) > 1:
                score += 5
        
        return min(score, 100)
    
    def _generate_recommendations(self, categorized, user_profile):
        """Generate personalized recommendations"""
        recommendations = []
        health_goals = user_profile.get('health_goals', [])
        
        # Recommendations based on health goals
        if 'muscle_gain' in health_goals:
            if not categorized['proteins']:
                recommendations.append("Add a protein source like chicken, fish, or tofu for muscle building")
        
        if 'weight_loss' in health_goals:
            if not categorized['vegetables']:
                recommendations.append("Add more vegetables for fiber and nutrients while keeping calories low")
        
        if 'balanced_diet' in health_goals:
            missing_groups = [group for group, items in categorized.items() if not items]
            if missing_groups:
                recommendations.append(f"Consider adding {', '.join(missing_groups[:2])} for better balance")
        
        # General recommendations
        if not categorized['vegetables']:
            recommendations.append("Add vegetables for essential vitamins and minerals")
        
        if not categorized['proteins']:
            recommendations.append("Include a protein source for satiety and muscle maintenance")
        
        return recommendations
    
    def _check_allergens(self, ingredients, user_allergens):
        """Check for allergen conflicts"""
        warnings = []
        allergen_map = {
            'nuts': ['almond', 'peanut', 'walnut', 'cashew', 'pistachio'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'gluten': ['wheat', 'bread', 'pasta', 'barley', 'rye'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'oyster'],
            'eggs': ['egg'],
            'soy': ['soy', 'tofu', 'tempeh']
        }
        
        for allergen in user_allergens:
            if allergen.lower() in allergen_map:
                allergen_ingredients = allergen_map[allergen.lower()]
                for ingredient in ingredients:
                    if any(ai in ingredient.lower() for ai in allergen_ingredients):
                        warnings.append(f"Warning: {ingredient} may contain {allergen}")
        
        return warnings
    
    def _identify_nutritional_benefits(self, ingredients):
        """Identify nutritional benefits of ingredients"""
        benefits = []
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Check against nutrition knowledge
            for benefit, beneficial_foods in self.nutrition_knowledge.items():
                if any(food in ingredient_lower for food in beneficial_foods):
                    benefits.append(f"{ingredient}: Good for {benefit.replace('_', ' ')}")
        
        return list(set(benefits))
    
    def process_natural_language_query(self, query):
        """Process natural language nutrition queries"""
        doc = self.nlp(query.lower())
        
        # Extract intent
        intent = self._extract_intent(query)
        
        # Extract entities
        entities = {
            'diet_type': self._extract_diet_type(query),
            'meal_type': self._extract_meal_type(query),
            'goal': self._extract_goal(query),
            'ingredients': self.extract_ingredients(query)
        }
        
        return {
            'intent': intent,
            'entities': entities,
            'original_query': query
        }
    
    def _extract_intent(self, query):
        """Extract user intent from query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['suggest', 'recommend', 'need', 'want']):
            return 'recommendation'
        elif any(word in query_lower for word in ['analyze', 'check', 'review']):
            return 'analysis'
        elif any(word in query_lower for word in ['plan', 'schedule', 'week']):
            return 'meal_planning'
        else:
            return 'general_inquiry'
    
    def _extract_diet_type(self, query):
        """Extract diet type from query"""
        diet_types = ['vegan', 'vegetarian', 'keto', 'paleo', 'mediterranean']
        for diet in diet_types:
            if diet in query.lower():
                return diet
        return None
    
    def _extract_meal_type(self, query):
        """Extract meal type from query"""
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        for meal in meal_types:
            if meal in query.lower():
                return meal
        return None
    
    def _extract_goal(self, query):
        """Extract health goal from query"""
        goals = ['muscle gain', 'weight loss', 'protein', 'energy', 'recovery']
        for goal in goals:
            if goal in query.lower():
                return goal
        return None
    
    def generate_meal_suggestions(self, parsed_query, user_profile=None):
        """Generate meal suggestions based on parsed natural language query"""
        suggestions = []
        
        entities = parsed_query['entities']
        
        # Base suggestions on extracted entities
        if entities['goal'] == 'muscle gain' or 'protein' in parsed_query['original_query']:
            suggestions.extend([
                "Grilled chicken breast with quinoa and steamed broccoli",
                "Greek yogurt with berries and almonds",
                "Salmon with sweet potato and asparagus"
            ])
        
        if entities['diet_type'] == 'vegan':
            suggestions.extend([
                "Tofu stir-fry with mixed vegetables and brown rice",
                "Lentil curry with whole grain naan",
                "Quinoa salad with chickpeas and avocado"
            ])
        
        if entities['meal_type'] == 'breakfast':
            suggestions.extend([
                "Oatmeal with banana and nuts",
                "Scrambled eggs with spinach and whole grain toast",
                "Greek yogurt parfait with berries"
            ])
        
        # Personalize based on user profile
        if user_profile:
            health_goals = user_profile.get('health_goals', [])
            allergens = user_profile.get('allergens', [])
            
            # Filter out allergens
            filtered_suggestions = []
            for suggestion in suggestions:
                safe = True
                for allergen in allergens:
                    if allergen.lower() in suggestion.lower():
                        safe = False
                        break
                if safe:
                    filtered_suggestions.append(suggestion)
            suggestions = filtered_suggestions
        
        return suggestions[:5]  # Return top 5 suggestions

# Initialize the analyzer
nlp_analyzer = NLPNutritionAnalyzer()