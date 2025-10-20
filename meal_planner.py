import requests
import json
import random
import time
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MealPlanGenerator:
    def __init__(self):
        # API configuration - prioritize environment variable for security
        self.spoonacular_api_key: str = os.getenv('SPOONACULAR_API_KEY', '')
        
        # Only show warning if we're trying to use API features
        if not self.spoonacular_api_key:
            print("⚠️  Note: SPOONACULAR_API_KEY not found in .env file. Using fallback meal database.")
        
        self.base_url = "https://api.spoonacular.com"
        
        # Rate limiting configuration
        self.last_request_time = 0.0
        self.min_request_interval = 0.1  # 100ms between requests
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.request_timeout = 15  # seconds
        
        # Enhanced fallback meals database with more variety and nutrition info
        self.fallback_meals = {
            'breakfast': {
                'high_protein': [
                    {
                        'title': "Greek Yogurt Protein Bowl",
                        'ingredients': ['greek yogurt', 'mixed berries', 'almonds', 'honey', 'chia seeds'],
                        'calories': 320, 'protein': 25, 'carbs': 28, 'fat': 12
                    },
                    {
                        'title': "Scrambled Eggs with Spinach", 
                        'ingredients': ['eggs', 'spinach', 'cheese', 'olive oil', 'herbs'],
                        'calories': 280, 'protein': 22, 'carbs': 6, 'fat': 18
                    },
                    {
                        'title': "Protein Smoothie Bowl",
                        'ingredients': ['protein powder', 'banana', 'peanut butter', 'almond milk', 'granola'],
                        'calories': 350, 'protein': 28, 'carbs': 32, 'fat': 14
                    },
                    {
                        'title': "Cottage Cheese Pancakes",
                        'ingredients': ['cottage cheese', 'eggs', 'oats', 'banana', 'cinnamon'],
                        'calories': 290, 'protein': 24, 'carbs': 25, 'fat': 10
                    }
                ],
                'low_carb': [
                    {
                        'title': "Avocado Egg Bowl",
                        'ingredients': ['avocado', 'eggs', 'bacon', 'cheese', 'herbs'],
                        'calories': 420, 'protein': 18, 'carbs': 8, 'fat': 36
                    },
                    {
                        'title': "Keto Omelet",
                        'ingredients': ['eggs', 'cheese', 'mushrooms', 'spinach', 'butter'],
                        'calories': 380, 'protein': 20, 'carbs': 6, 'fat': 32
                    },
                    {
                        'title': "Smoked Salmon Plate",
                        'ingredients': ['smoked salmon', 'cream cheese', 'cucumber', 'capers', 'dill'],
                        'calories': 340, 'protein': 22, 'carbs': 5, 'fat': 26
                    }
                ],
                'vegan': [
                    {
                        'title': "Overnight Oats with Berries",
                        'ingredients': ['rolled oats', 'almond milk', 'berries', 'maple syrup', 'chia seeds'],
                        'calories': 290, 'protein': 8, 'carbs': 48, 'fat': 8
                    },
                    {
                        'title': "Tofu Scramble",
                        'ingredients': ['tofu', 'vegetables', 'nutritional yeast', 'turmeric', 'olive oil'],
                        'calories': 220, 'protein': 12, 'carbs': 10, 'fat': 14
                    },
                    {
                        'title': "Acai Smoothie Bowl",
                        'ingredients': ['acai puree', 'banana', 'coconut milk', 'granola', 'coconut flakes'],
                        'calories': 310, 'protein': 6, 'carbs': 52, 'fat': 12
                    }
                ],
                'vegetarian': [
                    {
                        'title': "Veggie Cheese Omelet",
                        'ingredients': ['eggs', 'cheese', 'bell peppers', 'onions', 'herbs'],
                        'calories': 320, 'protein': 18, 'carbs': 8, 'fat': 24
                    },
                    {
                        'title': "Greek Yogurt Parfait",
                        'ingredients': ['greek yogurt', 'granola', 'honey', 'mixed berries', 'nuts'],
                        'calories': 280, 'protein': 15, 'carbs': 35, 'fat': 10
                    }
                ],
                'balanced': [
                    {
                        'title': "Whole Grain Avocado Toast",
                        'ingredients': ['whole grain bread', 'avocado', 'egg', 'tomato', 'herbs'],
                        'calories': 340, 'protein': 14, 'carbs': 32, 'fat': 18
                    },
                    {
                        'title': "Oatmeal with Fruit and Nuts",
                        'ingredients': ['rolled oats', 'milk', 'banana', 'walnuts', 'honey'],
                        'calories': 310, 'protein': 12, 'carbs': 45, 'fat': 12
                    },
                    {
                        'title': "Banana Protein Pancakes",
                        'ingredients': ['banana', 'eggs', 'oats', 'berries', 'maple syrup'],
                        'calories': 290, 'protein': 14, 'carbs': 42, 'fat': 8
                    }
                ]
            },
            'lunch': {
                'high_protein': [
                    {
                        'title': "Grilled Chicken Quinoa Salad",
                        'ingredients': ['chicken breast', 'quinoa', 'mixed greens', 'vegetables', 'olive oil'],
                        'calories': 420, 'protein': 35, 'carbs': 30, 'fat': 16
                    },
                    {
                        'title': "Tuna and White Bean Salad",
                        'ingredients': ['tuna', 'white beans', 'vegetables', 'olive oil', 'lemon'],
                        'calories': 380, 'protein': 32, 'carbs': 28, 'fat': 14
                    },
                    {
                        'title': "Turkey and Hummus Wrap",
                        'ingredients': ['turkey breast', 'hummus', 'whole wheat tortilla', 'vegetables', 'spinach'],
                        'calories': 410, 'protein': 28, 'carbs': 35, 'fat': 16
                    }
                ],
                'low_carb': [
                    {
                        'title': "Caesar Salad with Grilled Chicken",
                        'ingredients': ['chicken breast', 'romaine lettuce', 'parmesan', 'caesar dressing', 'croutons'],
                        'calories': 380, 'protein': 30, 'carbs': 12, 'fat': 24
                    },
                    {
                        'title': "Zucchini Noodles with Shrimp",
                        'ingredients': ['shrimp', 'zucchini noodles', 'pesto', 'cherry tomatoes', 'pine nuts'],
                        'calories': 320, 'protein': 28, 'carbs': 10, 'fat': 20
                    }
                ],
                'vegan': [
                    {
                        'title': "Buddha Bowl with Tahini",
                        'ingredients': ['quinoa', 'chickpeas', 'vegetables', 'tahini dressing', 'hemp seeds'],
                        'calories': 450, 'protein': 16, 'carbs': 55, 'fat': 18
                    },
                    {
                        'title': "Chickpea Curry",
                        'ingredients': ['chickpeas', 'coconut milk', 'vegetables', 'curry spices', 'brown rice'],
                        'calories': 420, 'protein': 14, 'carbs': 58, 'fat': 16
                    }
                ],
                'vegetarian': [
                    {
                        'title': "Caprese Salad with Quinoa",
                        'ingredients': ['quinoa', 'mozzarella', 'tomatoes', 'basil', 'balsamic glaze'],
                        'calories': 380, 'protein': 16, 'carbs': 42, 'fat': 16
                    },
                    {
                        'title': "Vegetable Pasta Salad",
                        'ingredients': ['whole wheat pasta', 'vegetables', 'feta cheese', 'olive oil', 'herbs'],
                        'calories': 420, 'protein': 14, 'carbs': 55, 'fat': 16
                    }
                ],
                'balanced': [
                    {
                        'title': "Mediterranean Chicken Bowl",
                        'ingredients': ['chicken breast', 'brown rice', 'vegetables', 'feta cheese', 'olive oil'],
                        'calories': 480, 'protein': 30, 'carbs': 45, 'fat': 20
                    },
                    {
                        'title': "Salmon with Sweet Potato",
                        'ingredients': ['salmon fillet', 'sweet potato', 'asparagus', 'lemon', 'herbs'],
                        'calories': 460, 'protein': 28, 'carbs': 35, 'fat': 22
                    }
                ]
            },
            'dinner': {
                'high_protein': [
                    {
                        'title': "Baked Salmon with Vegetables",
                        'ingredients': ['salmon fillet', 'broccoli', 'asparagus', 'quinoa', 'lemon'],
                        'calories': 520, 'protein': 40, 'carbs': 30, 'fat': 26
                    },
                    {
                        'title': "Grilled Chicken with Quinoa",
                        'ingredients': ['chicken breast', 'quinoa', 'roasted vegetables', 'herbs', 'olive oil'],
                        'calories': 480, 'protein': 38, 'carbs': 32, 'fat': 20
                    },
                    {
                        'title': "Turkey Meatballs with Zucchini Noodles",
                        'ingredients': ['ground turkey', 'zucchini noodles', 'marinara sauce', 'herbs', 'parmesan'],
                        'calories': 420, 'protein': 35, 'carbs': 18, 'fat': 22
                    }
                ],
                'low_carb': [
                    {
                        'title': "Grilled Fish with Cauliflower Mash",
                        'ingredients': ['white fish', 'cauliflower', 'butter', 'green beans', 'herbs'],
                        'calories': 380, 'protein': 32, 'carbs': 12, 'fat': 24
                    },
                    {
                        'title': "Chicken Thighs with Brussels Sprouts",
                        'ingredients': ['chicken thighs', 'brussels sprouts', 'bacon', 'garlic', 'olive oil'],
                        'calories': 450, 'protein': 28, 'carbs': 10, 'fat': 34
                    }
                ],
                'vegan': [
                    {
                        'title': "Lentil Bolognese with Zucchini Noodles",
                        'ingredients': ['lentils', 'zucchini noodles', 'marinara sauce', 'vegetables', 'nutritional yeast'],
                        'calories': 380, 'protein': 18, 'carbs': 48, 'fat': 12
                    },
                    {
                        'title': "Stuffed Bell Peppers",
                        'ingredients': ['bell peppers', 'quinoa', 'black beans', 'vegetables', 'nutritional yeast'],
                        'calories': 420, 'protein': 16, 'carbs': 65, 'fat': 10
                    }
                ],
                'vegetarian': [
                    {
                        'title': "Eggplant Parmesan",
                        'ingredients': ['eggplant', 'marinara sauce', 'mozzarella', 'parmesan', 'basil'],
                        'calories': 480, 'protein': 18, 'carbs': 35, 'fat': 28
                    },
                    {
                        'title': "Mushroom Risotto",
                        'ingredients': ['arborio rice', 'mushrooms', 'vegetable broth', 'parmesan', 'white wine'],
                        'calories': 520, 'protein': 14, 'carbs': 75, 'fat': 16
                    }
                ],
                'balanced': [
                    {
                        'title': "Grilled Chicken with Sweet Potato",
                        'ingredients': ['chicken breast', 'sweet potato', 'mixed vegetables', 'herbs', 'olive oil'],
                        'calories': 520, 'protein': 32, 'carbs': 45, 'fat': 22
                    },
                    {
                        'title': "Baked Cod with Quinoa",
                        'ingredients': ['cod fillet', 'quinoa', 'steamed broccoli', 'lemon', 'herbs'],
                        'calories': 440, 'protein': 30, 'carbs': 40, 'fat': 16
                    }
                ]
            }
        }

    def _validate_user_profile(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize user profile data"""
        if not isinstance(user_profile, dict):
            raise ValueError("user_profile must be a dictionary")
        
        # Normalize and validate fields
        normalized = {
            'diet_type': user_profile.get('diet_type', user_profile.get('diet', 'balanced')),
            'health_goals': user_profile.get('health_goals', []),
            'allergens': user_profile.get('allergens', [])
        }
        
        # Validate diet type
        valid_diets = ['balanced', 'vegan', 'vegetarian', 'keto', 'paleo', 'mediterranean']
        if normalized['diet_type'].lower() not in valid_diets:
            print(f"Warning: Unknown diet type '{normalized['diet_type']}'. Using 'balanced'.")
            normalized['diet_type'] = 'balanced'
        
        # Ensure lists are actually lists
        if not isinstance(normalized['health_goals'], list):
            normalized['health_goals'] = []
        if not isinstance(normalized['allergens'], list):
            normalized['allergens'] = []
        
        return normalized
    def _make_api_request(self, endpoint: str, params: Dict[str, Any], timeout: int = 10) -> Optional[Dict]:
        """
        Make a rate-limited GET request to Spoonacular with retries.
        Ensures apiKey is included.
        Returns JSON dict on success, None on failure/quota.
        """
        # ensure apiKey present
        if 'apiKey' not in params:
            params['apiKey'] = self.spoonacular_api_key

        # rate limiting
        now = time.time()
        wait = self.min_request_interval - (now - self.last_request_time)
        if wait > 0:
            time.sleep(wait)

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(self.max_retries):
            try:
                self.last_request_time = time.time()
                resp = requests.get(url, params=params, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 402:
                    # Paid quota / plan issue
                    print("Spoonacular API: quota/paid plan issue (402). Falling back.")
                    return None
                if resp.status_code == 429:
                    print(f"Spoonacular rate limited. Retry {attempt+1}/{self.max_retries}")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                # other error codes
                print(f"Spoonacular returned {resp.status_code}: {resp.text}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except requests.Timeout:
                print(f"Timeout on attempt {attempt+1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except requests.RequestException as e:
                print(f"RequestException: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        return None

    # ---------------- Public entry ----------------
    def generate_weekly_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Dict]:
        """Public method to generate a 7-day plan. Tries API, falls back to local DB."""
        # Validate and normalize user profile
        try:
            validated_profile = self._validate_user_profile(user_profile)
        except ValueError as e:
            raise ValueError(f"Invalid user profile: {e}")
        
        # Try API first, then fallback
        try:
            if self.spoonacular_api_key:
                plan = self._generate_api_plan(validated_profile)
                if plan:
                    return plan
            
            # Use fallback if API fails or no key
            return self._generate_fallback_plan(validated_profile)
            
        except Exception as e:
            print(f"Error generating meal plan: {e}")
            return self._generate_fallback_plan(validated_profile)

    # ---------------- Internal API plan generation ----------------
    def _generate_api_plan(self, user_profile: Dict[str, Any]) -> Optional[Dict[str, Dict]]:
        """
        Build a weekly plan calling Spoonacular for each meal. Returns None on failure.
        """
        diet_type = user_profile.get('diet_type', user_profile.get('diet', 'balanced')).lower()
        health_goals = [g.lower().replace(' ', '_') for g in user_profile.get('health_goals', [])]
        allergens = [a.lower() for a in user_profile.get('allergens', [])]

        # Map diet types
        diet_mapping = {
            'vegan': 'vegan',
            'vegetarian': 'vegetarian',
            'keto': 'ketogenic',
            'paleo': 'paleo',
            'balanced': None
        }
        api_diet = diet_mapping.get(diet_type, None)

        used_ids = set()
        weekly_plan: Dict[str, Dict] = {}

        for day_idx in range(7):
            day_name = (datetime.now() + timedelta(days=day_idx)).strftime('%A')
            daily_meals: Dict[str, Any] = {}

            for meal_type in ['breakfast', 'lunch', 'dinner']:
                # Try several attempts to get a unique recipe
                meal_selected = None
                attempts = 0
                while attempts < 6 and meal_selected is None:
                    attempts += 1
                    try:
                        meal = self._get_random_recipe(meal_type, api_diet, health_goals, allergens)
                        if not meal:
                            continue
                        rid = meal.get('recipe_id') or meal.get('id')
                        if rid and rid not in used_ids:
                            used_ids.add(rid)
                            meal_selected = meal
                        elif attempts >= 5:
                            # accept duplicate after several tries
                            meal_selected = meal
                    except Exception as e:
                        print(f"Error getting recipe for {meal_type} (attempt {attempts}): {e}")
                        meal_selected = None
                # If still none, fallback to a local meal
                if not meal_selected:
                    meal_selected = self._get_fallback_meal(meal_type, user_profile)
                daily_meals[meal_type] = meal_selected

            weekly_plan[day_name] = daily_meals

        return weekly_plan

    # ---------------- Bulk plan (optional) ----------------
    def get_bulk_meal_plan(self, user_profile: Dict[str, Any], days: int = 7) -> Dict[str, Dict]:
        """
        Efficient bulk retrieval for each meal type. Will call Spoonacular complexSearch once per meal type.
        """
        try:
            breakfasts = self._get_bulk_recipes('breakfast', user_profile, days)
            lunches = self._get_bulk_recipes('lunch', user_profile, days)
            dinners = self._get_bulk_recipes('dinner', user_profile, days)

            weekly_plan: Dict[str, Dict] = {}
            for day in range(days):
                day_name = (datetime.now() + timedelta(days=day)).strftime('%A')
                weekly_plan[day_name] = {
                    'breakfast': breakfasts[day] if day < len(breakfasts) else self._get_fallback_meal('breakfast', user_profile),
                    'lunch': lunches[day] if day < len(lunches) else self._get_fallback_meal('lunch', user_profile),
                    'dinner': dinners[day] if day < len(dinners) else self._get_fallback_meal('dinner', user_profile),
                }
            return weekly_plan
        except Exception as e:
            print(f"Bulk generation failed: {e}")
            return self.generate_weekly_plan(user_profile)

    # ---------------- Bulk helper ----------------
    def _get_bulk_recipes(self, meal_type: str, user_profile: Dict[str, Any], count: int = 7) -> List[Dict]:
        diet = user_profile.get('diet_type', user_profile.get('diet', 'balanced')).lower()
        health_goals = [g.lower().replace(' ', '_') for g in user_profile.get('health_goals', [])]
        allergens = [a.lower() for a in user_profile.get('allergens', [])]

        diet_map = {
            'vegan': 'vegan',
            'vegetarian': 'vegetarian',
            'keto': 'ketogenic',
            'paleo': 'paleo',
            'balanced': None
        }
        api_diet = diet_map.get(diet, None)

        params = {
            'type': meal_type,
            'number': max(count, 7) * 2,
            'addRecipeInformation': True,
            'fillIngredients': True,
            'sort': 'random'
        }
        if api_diet:
            params['diet'] = api_diet

        # Assemble intolerances
        if allergens:
            intolerance_map = {
                'dairy': 'dairy', 'gluten': 'gluten', 'nuts': 'tree nuts,peanuts',
                'shellfish': 'shellfish', 'eggs': 'egg', 'soy': 'soy', 'fish': 'seafood'
            }
            intolerances = []
            for a in allergens:
                if a in intolerance_map:
                    intolerances.extend(intolerance_map[a].split(','))
            if intolerances:
                params['intolerances'] = ','.join(sorted(set(intolerances)))

        data = self._make_api_request('recipes/complexSearch', params)
        recipes: List[Dict] = []
        if not data or 'results' not in data:
            return recipes

        # Collect up to 'count' detailed recipes
        for item in data.get('results', [])[:count]:
            rid = item.get('id')
            try:
                details = self._get_recipe_details(rid)
                recipe_data = {
                    'title': item.get('title'),
                    'ingredients': self._extract_ingredients(details),
                    'instructions': self._extract_instructions(details),
                    'nutrition': self._extract_nutrition(details),
                    'image': item.get('image', ''),
                    'ready_in_minutes': item.get('readyInMinutes', 30),
                    'servings': item.get('servings', 2),
                    'recipe_id': rid,
                    'source_url': item.get('sourceUrl', '')
                }
                recipes.append(recipe_data)
            except Exception as e:
                print(f"Skipping recipe {rid} due to error: {e}")
                continue
        return recipes

    # ---------------- Fallbacks & helpers ----------------
    def _get_fallback_meal(self, meal_type: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get a detailed fallback meal when API is unavailable"""
        meal_category = self._determine_meal_category(user_profile.get('health_goals', []), user_profile.get('diet_type', user_profile.get('diet', 'balanced')))
        
        # Get available meals for the category
        available_meals = self.fallback_meals.get(meal_type, {}).get(meal_category, [])
        
        # If no meals for specific category, try 'balanced' as fallback
        if not available_meals:
            available_meals = self.fallback_meals.get(meal_type, {}).get('balanced', [])
        
        # If still no meals, create a basic meal
        if not available_meals:
            return self._create_basic_meal(meal_type, meal_category)
        
        # Select a random meal from available options
        selected_meal = random.choice(available_meals)
        
        # If the meal is already a detailed dict, return it with additional processing
        if isinstance(selected_meal, dict):
            # Add cooking instructions based on meal type and ingredients
            instructions = self._generate_detailed_instructions(selected_meal['title'], selected_meal['ingredients'])
            
            return {
                'title': selected_meal['title'],
                'ingredients': selected_meal['ingredients'],
                'instructions': instructions,
                'nutrition': {
                    'calories': {'amount': selected_meal['calories'], 'unit': 'kcal'},
                    'protein': {'amount': selected_meal['protein'], 'unit': 'g'},
                    'carbohydrates': {'amount': selected_meal['carbs'], 'unit': 'g'},
                    'fat': {'amount': selected_meal['fat'], 'unit': 'g'}
                },
                'estimated': True,
                'recipe_id': None,
                'ready_in_minutes': self._estimate_cooking_time(selected_meal['title']),
                'servings': 1,
                'meal_category': meal_category
            }
        
        # If it's a simple string (legacy format), convert it
        return self._convert_legacy_meal(selected_meal, meal_type, meal_category)
    
    def _create_basic_meal(self, meal_type: str, meal_category: str) -> Dict[str, Any]:
        """Create a basic meal when no predefined meals are available"""
        basic_meals = {
            'breakfast': {
                'title': f"Simple {meal_category.replace('_', ' ').title()} Breakfast",
                'ingredients': ['oats', 'milk', 'banana', 'honey'],
                'calories': 300, 'protein': 12, 'carbs': 45, 'fat': 8
            },
            'lunch': {
                'title': f"Simple {meal_category.replace('_', ' ').title()} Lunch",
                'ingredients': ['brown rice', 'vegetables', 'protein source', 'olive oil'],
                'calories': 400, 'protein': 20, 'carbs': 50, 'fat': 12
            },
            'dinner': {
                'title': f"Simple {meal_category.replace('_', ' ').title()} Dinner",
                'ingredients': ['protein source', 'vegetables', 'whole grains', 'herbs'],
                'calories': 450, 'protein': 25, 'carbs': 40, 'fat': 18
            }
        }
        
        basic_meal = basic_meals.get(meal_type, basic_meals['lunch'])
        
        return {
            'title': basic_meal['title'],
            'ingredients': basic_meal['ingredients'],
            'instructions': self._generate_detailed_instructions(basic_meal['title'], basic_meal['ingredients']),
            'nutrition': {
                'calories': {'amount': basic_meal['calories'], 'unit': 'kcal'},
                'protein': {'amount': basic_meal['protein'], 'unit': 'g'},
                'carbohydrates': {'amount': basic_meal['carbs'], 'unit': 'g'},
                'fat': {'amount': basic_meal['fat'], 'unit': 'g'}
            },
            'estimated': True,
            'recipe_id': None,
            'ready_in_minutes': 20,
            'servings': 1
        }
    
    def _convert_legacy_meal(self, meal_title: str, meal_type: str, meal_category: str) -> Dict[str, Any]:
        """Convert legacy string-based meals to detailed format"""
        ingredients = self._generate_ingredients_for_meal(meal_title)
        nutrition = self._estimate_nutrition(meal_title, meal_category)
        
        return {
            'title': meal_title,
            'ingredients': ingredients,
            'instructions': self._generate_detailed_instructions(meal_title, ingredients),
            'nutrition': {
                'calories': {'amount': nutrition.get('calories', 300), 'unit': 'kcal'},
                'protein': {'amount': nutrition.get('protein', 15), 'unit': 'g'},
                'carbohydrates': {'amount': nutrition.get('carbohydrates', 30), 'unit': 'g'},
                'fat': {'amount': nutrition.get('fat', 12), 'unit': 'g'}
            },
            'estimated': True,
            'recipe_id': None,
            'ready_in_minutes': self._estimate_cooking_time(meal_title),
            'servings': 1
        }
    
    def _generate_detailed_instructions(self, meal_title: str, ingredients: List[str]) -> List[str]:
        """Generate detailed cooking instructions based on meal title and ingredients"""
        title_lower = meal_title.lower()
        
        # Breakfast instructions
        if 'smoothie' in title_lower or 'bowl' in title_lower:
            return [
                "1. Add liquid ingredients to blender first",
                "2. Add frozen fruits and other ingredients",
                "3. Blend until smooth and creamy (1-2 minutes)",
                "4. Pour into bowl and add toppings",
                "5. Serve immediately"
            ]
        
        if 'scramble' in title_lower or 'omelet' in title_lower:
            return [
                "1. Heat oil or butter in non-stick pan over medium heat",
                "2. Whisk eggs in a bowl with salt and pepper",
                "3. Pour eggs into pan and let set for 30 seconds",
                "4. Gently scramble or fold for omelet",
                "5. Add vegetables and cheese if using",
                "6. Cook until eggs are set but still creamy",
                "7. Serve immediately while hot"
            ]
        
        if 'oats' in title_lower or 'oatmeal' in title_lower:
            return [
                "1. Combine oats and liquid in a pot",
                "2. Bring to a boil, then reduce heat to low",
                "3. Simmer for 5-10 minutes, stirring occasionally",
                "4. Add sweeteners and spices",
                "5. Top with fruits and nuts",
                "6. Serve warm"
            ]
        
        # Lunch/Dinner instructions
        if 'grilled' in title_lower:
            return [
                "1. Preheat grill to medium-high heat",
                "2. Season protein with salt, pepper, and herbs",
                "3. Oil the grill grates to prevent sticking",
                "4. Grill protein for appropriate time (varies by type)",
                "5. Let rest for 5 minutes before serving",
                "6. Serve with prepared sides"
            ]
        
        if 'salad' in title_lower:
            return [
                "1. Wash and dry all vegetables thoroughly",
                "2. Chop vegetables into bite-sized pieces",
                "3. Prepare protein if using (cook and cool)",
                "4. Combine all ingredients in large bowl",
                "5. Add dressing just before serving",
                "6. Toss gently to coat evenly"
            ]
        
        if 'curry' in title_lower or 'stir-fry' in title_lower:
            return [
                "1. Heat oil in large pan or wok over medium-high heat",
                "2. Add aromatics (onion, garlic, ginger) and cook for 2 minutes",
                "3. Add protein and cook until almost done",
                "4. Add vegetables in order of cooking time needed",
                "5. Add sauce and spices, stir well",
                "6. Simmer until vegetables are tender",
                "7. Serve over rice or grains"
            ]
        
        # Default instructions
        return [
            "1. Gather and prepare all ingredients",
            "2. Follow standard cooking methods for each component",
            "3. Season to taste with salt, pepper, and herbs",
            "4. Cook until all components are properly done",
            "5. Combine and serve immediately while hot"
        ]
    
    def _estimate_cooking_time(self, meal_title: str) -> int:
        """Estimate cooking time based on meal complexity"""
        title_lower = meal_title.lower()
        
        # Quick meals (under 15 minutes)
        if any(word in title_lower for word in ['smoothie', 'salad', 'yogurt', 'toast']):
            return random.randint(5, 12)
        
        # Medium meals (15-30 minutes)
        if any(word in title_lower for word in ['scramble', 'omelet', 'stir-fry', 'pasta']):
            return random.randint(15, 25)
        
        # Longer meals (30-45 minutes)
        if any(word in title_lower for word in ['baked', 'roasted', 'grilled', 'curry']):
            return random.randint(25, 40)
        
        # Very long meals (45+ minutes)
        if any(word in title_lower for word in ['slow', 'braised', 'stew']):
            return random.randint(45, 75)
        
        # Default time for unmatched meals
        return 25
        
    def _generate_fallback_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate comprehensive meal plan using enhanced local database"""
        print("🍽️ Generating meal plan from local database (API unavailable)")
        
        health_goals = user_profile.get('health_goals', [])
        diet_type = user_profile.get('diet_type', 'balanced')
        allergens = user_profile.get('allergens', [])
        
        # Determine primary meal category
        meal_category = self._determine_meal_category(health_goals, diet_type)
        print(f"📋 Selected meal category: {meal_category.replace('_', ' ').title()}")
        
        weekly_plan = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Track used meals to ensure variety
        used_meals = set()
        
        for day in days:
            daily_meals = {}
            
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                # Get fallback meal with variety tracking
                meal = self._get_varied_fallback_meal(meal_type, user_profile, used_meals)
                
                # Filter allergens if specified
                if allergens:
                    meal = self._filter_meal_allergens(meal, allergens)
                
                daily_meals[meal_type] = meal
            
            weekly_plan[day] = daily_meals
        
        # Add plan metadata
        plan_info = {
            'generated_by': 'local_database',
            'diet_category': meal_category,
            'total_meals': len(weekly_plan) * 3,
            'allergen_filtered': bool(allergens),
            'generation_time': datetime.now().isoformat()
        }
        
        weekly_plan['_plan_info'] = plan_info
        print(f"✅ Generated {len(weekly_plan)-1} days with {(len(weekly_plan)-1) * 3} meals")
        
        return weekly_plan
    
    def _get_varied_fallback_meal(self, meal_type: str, user_profile: Dict[str, Any], used_meals: set) -> Dict[str, Any]:
        """Get a fallback meal ensuring variety across the week"""
        meal_category = self._determine_meal_category(user_profile.get('health_goals', []), user_profile.get('diet_type', 'balanced'))
        
        # Get available meals for the category
        available_meals = self.fallback_meals.get(meal_type, {}).get(meal_category, [])
        
        # If no meals for specific category, try 'balanced' as fallback
        if not available_meals:
            available_meals = self.fallback_meals.get(meal_type, {}).get('balanced', [])
        
        # Filter out already used meals
        unused_meals = [meal for meal in available_meals if (isinstance(meal, dict) and meal['title'] not in used_meals) or (isinstance(meal, str) and meal not in used_meals)]
        
        # If we've used all meals, reset the used set for this meal type
        if not unused_meals:
            unused_meals = available_meals
        
        if unused_meals:
            selected_meal = random.choice(unused_meals)
            
            # Track used meal
            if isinstance(selected_meal, dict):
                used_meals.add(selected_meal['title'])
            else:
                used_meals.add(selected_meal)
            
            # Convert to standard format
            if isinstance(selected_meal, dict):
                return self._format_detailed_meal(selected_meal, meal_category)
            else:
                return self._convert_legacy_meal(selected_meal, meal_type, meal_category)
        
        # Fallback to basic meal
        return self._create_basic_meal(meal_type, meal_category)
    
    def _format_detailed_meal(self, meal_data: Dict[str, Any], meal_category: str) -> Dict[str, Any]:
        """Format detailed meal data to standard format"""
        instructions = self._generate_detailed_instructions(meal_data['title'], meal_data['ingredients'])
        
        return {
            'title': meal_data['title'],
            'ingredients': meal_data['ingredients'],
            'instructions': instructions,
            'nutrition': {
                'calories': {'amount': meal_data['calories'], 'unit': 'kcal'},
                'protein': {'amount': meal_data['protein'], 'unit': 'g'},
                'carbohydrates': {'amount': meal_data['carbs'], 'unit': 'g'},
                'fat': {'amount': meal_data['fat'], 'unit': 'g'}
            },
            'estimated': True,
            'recipe_id': None,
            'ready_in_minutes': self._estimate_cooking_time(meal_data['title']),
            'servings': 1,
            'meal_category': meal_category,
            'image': '',
            'source_url': ''
        }
    
    def _filter_meal_allergens(self, meal: Dict[str, Any], allergens: List[str]) -> Dict[str, Any]:
        """Filter or modify meal based on allergens"""
        if not allergens:
            return meal
            
        meal_title = meal.get('title', '').lower()
        ingredients = [ing.lower() for ing in meal.get('ingredients', [])]
        
        allergen_map = {
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'parmesan', 'mozzarella', 'feta'],
            'gluten': ['bread', 'pasta', 'wheat', 'flour', 'breadcrumbs', 'couscous'],
            'nuts': ['nuts', 'almond', 'peanut', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pine nuts'],
            'eggs': ['egg', 'eggs'],
            'soy': ['soy', 'tofu', 'tempeh', 'edamame'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'shellfish']
        }
        
        # Check for allergens
        has_allergens = False
        detected_allergens = []
        for allergen in allergens:
            allergen_key = allergen.lower()
            if allergen_key in allergen_map:
                allergen_keywords = allergen_map[allergen_key]
                for keyword in allergen_keywords:
                    if keyword in meal_title or any(keyword in ing for ing in ingredients):
                        has_allergens = True
                        detected_allergens.append(allergen)
                        break
        
        if has_allergens:
            # Add allergen warning to the meal
            warning = f"⚠️ Contains: {', '.join(detected_allergens)}"
            if 'allergen_warning' not in meal:
                meal['allergen_warning'] = warning
            else:
                meal['allergen_warning'] += f" | {warning}"
            
            # Modify title to indicate allergen presence
            if not meal['title'].startswith("⚠️"):
                meal['title'] = f"⚠️ {meal['title']}"
        
        return meal

    def _get_random_recipe(self, meal_type: str, diet: Optional[str], health_goals: List[str], allergens: List[str]) -> Optional[Dict[str, Any]]:
        params = {
            'type': meal_type,
            'number': 10,
            'addRecipeInformation': True,
            'fillIngredients': True,
            'sort': 'random',
            'maxReadyTime': 60
        }
        if diet:
            params['diet'] = diet

        # Health goal tweaks
        if any('muscle' in g for g in health_goals):
            params['minProtein'] = 15
        if any('weight' in g for g in health_goals):
            # tighten calories for weight loss
            params['maxCalories'] = int(600)

        # intolerances
        if allergens:
            allergen_map = {
                'dairy': 'dairy', 'gluten': 'gluten', 'nuts': 'tree nuts,peanuts',
                'shellfish': 'shellfish', 'eggs': 'egg', 'soy': 'soy', 'fish': 'seafood'
            }
            intolerances = []
            for a in allergens:
                if a in allergen_map:
                    intolerances.extend(allergen_map[a].split(','))
            if intolerances:
                params['intolerances'] = ','.join(sorted(set(intolerances)))

        data = self._make_api_request('recipes/complexSearch', params)
        if not data or 'results' not in data or not data['results']:
            return None

        recipe_choice = random.choice(data['results'])
        recipe_id = recipe_choice.get('id')
        details = self._get_recipe_details(recipe_id)
        if not details:
            return None

        return {
            'title': recipe_choice.get('title'),
            'ingredients': self._extract_ingredients(details),
            'instructions': self._extract_instructions(details),
            'nutrition': self._extract_nutrition(details),
            'image': recipe_choice.get('image', ''),
            'ready_in_minutes': recipe_choice.get('readyInMinutes', 30),
            'servings': recipe_choice.get('servings', 2),
            'source_url': recipe_choice.get('sourceUrl', ''),
            'recipe_id': recipe_id
        }

    def _get_recipe_details(self, recipe_id: int) -> Dict[str, Any]:
        params = {'includeNutrition': True}
        data = self._make_api_request(f'recipes/{recipe_id}/information', params)
        return data or {}

    def _extract_ingredients(self, recipe_details: Dict[str, Any]) -> List[str]:
        ingredients = []
        for ing in recipe_details.get('extendedIngredients', []) or []:
            ingredients.append(ing.get('original', ing.get('name', '')))
        return ingredients

    def _extract_instructions(self, recipe_details: Dict[str, Any]) -> List[str]:
        instructions = []
        for inst in recipe_details.get('analyzedInstructions', []) or []:
            for step in inst.get('steps', []):
                instructions.append(step.get('step', ''))
        return instructions or ["Follow standard cooking instructions"]

    def _extract_nutrition(self, recipe_details: Dict[str, Any]) -> Dict[str, Any]:
        nutrition = {}
        nutr_section = recipe_details.get('nutrition', {}) or {}
        for nutrient in nutr_section.get('nutrients', []) or []:
            name = nutrient.get('name', '').lower()
            if name in ['calories', 'protein', 'carbohydrates', 'fat', 'fiber']:
                nutrition[name] = {'amount': nutrient.get('amount', 0), 'unit': nutrient.get('unit', '')}
        return nutrition

    def _generate_ingredients_for_meal(self, meal_title: str) -> List[str]:
        patterns = {
            'chicken': ['chicken breast', 'olive oil', 'garlic', 'herbs'],
            'salmon': ['salmon fillet', 'lemon', 'herbs', 'olive oil'],
            'quinoa': ['quinoa', 'vegetable broth', 'onion'],
            'yogurt': ['greek yogurt', 'berries', 'honey', 'granola'],
            'oatmeal': ['rolled oats', 'milk', 'banana', 'cinnamon'],
            'salad': ['mixed greens', 'tomatoes', 'cucumber', 'olive oil', 'vinegar']
        }
        meal_lower = meal_title.lower()
        ing = []
        for k, lst in patterns.items():
            if k in meal_lower:
                ing.extend(lst)
        return ing or ['main ingredient', 'seasonings', 'cooking oil']

    def _generate_instructions_for_meal(self, meal_title: str) -> List[str]:
        if 'grilled' in meal_title.lower():
            return [
                "1. Preheat grill to medium-high heat",
                "2. Season ingredients",
                "3. Grill until cooked",
                "4. Rest and serve"
            ]
        if 'salad' in meal_title.lower():
            return [
                "1. Wash and chop veggies",
                "2. Mix with dressing",
                "3. Serve fresh"
            ]
        return [
            "1. Prepare ingredients",
            "2. Cook according to recipe",
            "3. Season and serve"
        ]

    def _estimate_nutrition(self, meal_title: str, category: str) -> Dict[str, int]:
        base = {
            'high_protein': {'calories': 400, 'protein': 35, 'carbohydrates': 20, 'fat': 15},
            'low_carb': {'calories': 350, 'protein': 25, 'carbohydrates': 10, 'fat': 25},
            'vegan': {'calories': 375, 'protein': 15, 'carbohydrates': 45, 'fat': 18},
            'balanced': {'calories': 425, 'protein': 25, 'carbohydrates': 35, 'fat': 20}
        }.get(category, {'calories': 425, 'protein': 25, 'carbohydrates': 35, 'fat': 20})
        # add small variance
        return {k: int(v * random.uniform(0.85, 1.15)) for k, v in base.items()}

    def _determine_meal_category(self, health_goals, diet_type):
        """Determine the appropriate meal category based on diet type and health goals"""
        dt = (diet_type or '').lower().strip()
        
        # Priority 1: Specific diet types
        if dt in ['vegan']:
            return 'vegan'
        elif dt in ['vegetarian']:
            return 'vegetarian'
        elif dt in ['keto', 'ketogenic']:
            return 'low_carb'
        elif dt in ['paleo']:
            return 'high_protein'
        
        # Priority 2: Health goals
        hg = ' '.join(health_goals or []).lower()
        if any(goal in hg for goal in ['muscle', 'gain', 'protein', 'build']):
            return 'high_protein'
        elif any(goal in hg for goal in ['weight', 'loss', 'lose', 'cut', 'lean']):
            return 'low_carb'
        elif 'vegan' in hg:
            return 'vegan'
        elif 'vegetarian' in hg:
            return 'vegetarian'
        
        # Default to balanced
        return 'balanced'

    def _filter_allergens(self, meals: List[str], allergens: List[str]) -> List[str]:
        safe = []
        allergen_keywords = {
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'gluten': ['bread', 'pasta', 'wheat'],
            'nuts': ['nut', 'almond', 'peanut', 'walnut'],
            'eggs': ['egg'],
            'soy': ['soy', 'tofu'],
            'shellfish': ['shrimp', 'crab', 'lobster']
        }
        for meal in meals:
            m = meal.lower()
            ok = True
            for a in (allergens or []):
                ak = a.lower()
                keys = allergen_keywords.get(ak, [])
                if any(k in m for k in keys):
                    ok = False
                    break
            if ok:
                safe.append(meal)
        return safe

    def customize_meal_plan(self, base_plan: Dict[str, Dict], preferences: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Apply simple customizations (swap specific day_meal entries).
        preferences example: {'meal_swaps': {'Monday_lunch': <meal_dict>}}
        """
        customized = {day: {mt: md for mt, md in meals.items()} for day, meals in base_plan.items()}
        swaps = preferences.get('meal_swaps', {})
        for key, new_meal in swaps.items():
            try:
                day, meal_type = key.split('_', 1)
                if day in customized and meal_type in customized[day]:
                    customized[day][meal_type] = new_meal
            except Exception:
                continue
        return customized

# initialize
meal_planner = MealPlanGenerator()
