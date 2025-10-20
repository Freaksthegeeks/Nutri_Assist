import streamlit as st
import pandas as pd
import spacy
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import random
import hashlib

# Import our custom modules with fallback handling
try:
    from database import DatabaseManager
    from nlp_analyzer import nlp_analyzer
    from meal_planner import meal_planner
    from chatbot import nutrition_chatbot
    FULL_FEATURES = True
except ImportError as e:
    print(f"Import error: {e}. Using simplified features.")
    FULL_FEATURES = False
    # We'll define simplified versions below

# Simplified implementations for fallback
if not FULL_FEATURES:
    import sqlite3
    
    class SimpleDatabaseManager:
        def __init__(self, db_path="nutrition_app.db"):
            self.db_path = db_path
            self.init_database()
        
        def init_database(self):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    height REAL,
                    weight REAL,
                    activity_level TEXT,
                    diet_type TEXT,
                    allergens TEXT,
                    health_goals TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meal_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meal_name TEXT NOT NULL,
                    ingredients TEXT NOT NULL,
                    analysis_result TEXT,
                    meal_type TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meal_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_data TEXT NOT NULL,
                    week_start_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    log_date DATE NOT NULL,
                    calories_consumed INTEGER DEFAULT 0,
                    protein_grams REAL DEFAULT 0,
                    carbs_grams REAL DEFAULT 0,
                    fat_grams REAL DEFAULT 0,
                    water_ml INTEGER DEFAULT 0,
                    exercise_minutes INTEGER DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
        
        def register_user(self, username, email, password):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                ''', (username, email, password_hash))
                
                user_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return {"success": True, "user_id": user_id}
            except sqlite3.IntegrityError:
                return {"success": False, "error": "Username or email already exists"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def authenticate_user(self, username, password):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, password_hash FROM users
                    WHERE username = ? OR email = ?
                ''', (username, username))
                
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    if password_hash == user[2]:
                        return {"success": True, "user_id": user[0], "username": user[1]}
                
                return {"success": False, "error": "Invalid credentials"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def save_user_profile(self, user_id, profile_data):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE user_profiles SET
                        age = ?, gender = ?, height = ?, weight = ?,
                        activity_level = ?, diet_type = ?, allergens = ?,
                        health_goals = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (
                        profile_data.get('age'),
                        profile_data.get('gender'),
                        profile_data.get('height'),
                        profile_data.get('weight'),
                        profile_data.get('activity_level'),
                        profile_data.get('diet_type'),
                        json.dumps(profile_data.get('allergens', [])),
                        json.dumps(profile_data.get('health_goals', [])),
                        user_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO user_profiles 
                        (user_id, age, gender, height, weight, activity_level, 
                         diet_type, allergens, health_goals)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        profile_data.get('age'),
                        profile_data.get('gender'),
                        profile_data.get('height'),
                        profile_data.get('weight'),
                        profile_data.get('activity_level'),
                        profile_data.get('diet_type'),
                        json.dumps(profile_data.get('allergens', [])),
                        json.dumps(profile_data.get('health_goals', []))
                    ))
                
                conn.commit()
                conn.close()
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def get_user_profile(self, user_id):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT age, gender, height, weight, activity_level,
                           diet_type, allergens, health_goals
                    FROM user_profiles WHERE user_id = ?
                ''', (user_id,))
                
                profile = cursor.fetchone()
                conn.close()
                
                if profile:
                    return {
                        "age": profile[0],
                        "gender": profile[1],
                        "height": profile[2],
                        "weight": profile[3],
                        "activity_level": profile[4],
                        "diet_type": profile[5],
                        "allergens": json.loads(profile[6]) if profile[6] else [],
                        "health_goals": json.loads(profile[7]) if profile[7] else []
                    }
                return None
            except Exception as e:
                print(f"Error getting profile: {e}")
                return None
        
        def save_meal_log(self, user_id, meal_data):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO meal_logs 
                    (user_id, meal_name, ingredients, analysis_result, meal_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    meal_data.get('meal_name'),
                    json.dumps(meal_data.get('ingredients', [])),
                    json.dumps(meal_data.get('analysis_result', {})),
                    meal_data.get('meal_type')
                ))
                
                conn.commit()
                conn.close()
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def save_meal_plan(self, user_id, plan_data, week_start_date):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO meal_plans (user_id, plan_data, week_start_date)
                    VALUES (?, ?, ?)
                ''', (user_id, json.dumps(plan_data), week_start_date))
                
                conn.commit()
                conn.close()
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def get_meal_stats(self, user_id):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM meal_logs WHERE user_id = ?
                ''', (user_id,))
                meals_count = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM meal_plans WHERE user_id = ?
                ''', (user_id,))
                plans_count = cursor.fetchone()[0]
                
                conn.close()
                return {"meals_analyzed": meals_count, "meal_plans": plans_count}
            except Exception as e:
                return {"meals_analyzed": 0, "meal_plans": 0}
        
        def save_daily_log(self, user_id, log_data):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                log_date = log_data.get('date', datetime.now().date())
                
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_logs 
                    (user_id, log_date, calories_consumed, protein_grams, carbs_grams, 
                     fat_grams, water_ml, exercise_minutes, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    log_date,
                    log_data.get('calories', 0),
                    log_data.get('protein', 0),
                    log_data.get('carbs', 0),
                    log_data.get('fat', 0),
                    log_data.get('water', 0),
                    log_data.get('exercise', 0),
                    log_data.get('notes', '')
                ))
                
                conn.commit()
                conn.close()
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def get_daily_logs(self, user_id, days=7):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT log_date, calories_consumed, protein_grams, carbs_grams,
                           fat_grams, water_ml, exercise_minutes, notes
                    FROM daily_logs 
                    WHERE user_id = ? 
                    ORDER BY log_date DESC 
                    LIMIT ?
                ''', (user_id, days))
                
                logs = cursor.fetchall()
                conn.close()
                
                return [
                    {
                        "date": log[0],
                        "calories": log[1],
                        "protein": log[2],
                        "carbs": log[3],
                        "fat": log[4],
                        "water": log[5],
                        "exercise": log[6],
                        "notes": log[7]
                    }
                    for log in logs
                ]
            except Exception as e:
                print(f"Error getting daily logs: {e}")
                return []
    
    class SimpleNLPAnalyzer:
        def __init__(self):
            self.food_groups = {
                'proteins': ['chicken', 'beef', 'fish', 'salmon', 'tuna', 'eggs', 'tofu', 'beans', 'lentils', 'quinoa', 'turkey', 'pork', 'lamb', 'shrimp', 'crab', 'lobster', 'cottage cheese', 'protein powder', 'tempeh', 'seitan'],
                'carbs': ['rice', 'pasta', 'bread', 'potato', 'oats', 'quinoa', 'barley', 'wheat', 'sweet potato', 'corn', 'buckwheat', 'millet', 'amaranth', 'bulgur', 'couscous', 'noodles'],
                'vegetables': ['broccoli', 'spinach', 'carrot', 'tomato', 'onion', 'pepper', 'cucumber', 'lettuce', 'kale', 'cauliflower', 'cabbage', 'zucchini', 'eggplant', 'asparagus', 'mushroom', 'beetroot', 'celery'],
                'fruits': ['apple', 'banana', 'orange', 'berry', 'grape', 'mango', 'pineapple', 'avocado', 'strawberry', 'blueberry', 'raspberry', 'blackberry', 'peach', 'pear', 'plum', 'kiwi', 'watermelon', 'cantaloupe'],
                'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream', 'ice cream', 'whey', 'kefir', 'mozzarella', 'cheddar', 'parmesan'],
                'fats': ['oil', 'butter', 'nuts', 'seeds', 'avocado', 'olive', 'coconut oil', 'olive oil', 'almond', 'walnut', 'cashew', 'peanut', 'sunflower seeds', 'chia seeds', 'flax seeds']
            }
            
            # Enhanced nutrition database
            self.nutrition_db = {
                'chicken': {'calories_per_100g': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
                'salmon': {'calories_per_100g': 208, 'protein': 25, 'carbs': 0, 'fat': 12, 'fiber': 0},
                'rice': {'calories_per_100g': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
                'broccoli': {'calories_per_100g': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.6},
                'apple': {'calories_per_100g': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2, 'fiber': 2.4},
                'eggs': {'calories_per_100g': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0},
                'avocado': {'calories_per_100g': 160, 'protein': 2, 'carbs': 9, 'fat': 15, 'fiber': 7},
                'quinoa': {'calories_per_100g': 120, 'protein': 4.4, 'carbs': 22, 'fat': 1.9, 'fiber': 2.8},
                'spinach': {'calories_per_100g': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'fiber': 2.2},
                'yogurt': {'calories_per_100g': 59, 'protein': 10, 'carbs': 3.6, 'fat': 0.4, 'fiber': 0}
            }
        
        def extract_ingredients(self, text):
            ingredients = []
            text_lower = text.lower()
            
            for category, items in self.food_groups.items():
                for item in items:
                    if item in text_lower:
                        ingredients.append(item)
            
            return list(set(ingredients))
        
        def analyze_meal_nutrition(self, ingredients, user_profile=None):
            categorized = {category: [] for category in self.food_groups.keys()}
            
            # Categorize ingredients
            for ingredient in ingredients:
                for category, items in self.food_groups.items():
                    if ingredient in items:
                        categorized[category].append(ingredient)
            
            # Calculate detailed nutrition
            total_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0}
            
            for ingredient in ingredients:
                if ingredient in self.nutrition_db:
                    nutrition = self.nutrition_db[ingredient]
                    # Assume 100g serving for estimation
                    total_nutrition['calories'] += nutrition['calories_per_100g']
                    total_nutrition['protein'] += nutrition['protein']
                    total_nutrition['carbs'] += nutrition['carbs']
                    total_nutrition['fat'] += nutrition['fat']
                    total_nutrition['fiber'] += nutrition['fiber']
            
            # Calculate nutrition score
            score = 0
            food_groups_present = len([cat for cat, items in categorized.items() if items])
            
            # Scoring system
            if food_groups_present >= 4:
                score += 40
            elif food_groups_present >= 3:
                score += 30
            elif food_groups_present >= 2:
                score += 20
            
            if categorized['proteins']:
                score += 25
            if categorized['vegetables']:
                score += 25
            if categorized['fruits']:
                score += 20
            
            # Bonus points for variety
            if len(ingredients) >= 5:
                score += 10
            
            # Penalty for processed foods
            processed_foods = ['processed', 'canned', 'frozen', 'packaged']
            for food in ingredients:
                if any(proc in food.lower() for proc in processed_foods):
                    score -= 5
            
            recommendations = []
            allergen_warnings = []
            nutritional_benefits = []
            
            # Enhanced recommendations
            if not categorized['proteins']:
                recommendations.append("Add a protein source (chicken, fish, beans, tofu) for muscle maintenance")
            if not categorized['vegetables']:
                recommendations.append("Include vegetables for essential vitamins, minerals, and fiber")
            if not categorized['fruits']:
                recommendations.append("Consider adding fruits for natural vitamins and antioxidants")
            if food_groups_present < 3:
                recommendations.append("Aim for variety - include foods from multiple food groups")
            
            # Allergen checking
            if user_profile:
                allergens = user_profile.get('allergens', [])
                allergen_keywords = {
                    'Nuts': ['almond', 'walnut', 'cashew', 'peanut', 'nuts'],
                    'Dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
                    'Gluten': ['wheat', 'bread', 'pasta', 'flour'],
                    'Shellfish': ['shrimp', 'crab', 'lobster', 'shellfish'],
                    'Eggs': ['egg', 'eggs'],
                    'Soy': ['soy', 'tofu', 'tempeh'],
                    'Fish': ['fish', 'salmon', 'tuna']
                }
                
                for allergen in allergens:
                    keywords = allergen_keywords.get(allergen, [allergen.lower()])
                    for keyword in keywords:
                        if any(keyword in ing.lower() for ing in ingredients):
                            allergen_warnings.append(f"⚠️ Allergen Alert: Contains {allergen}")
                            break
            
            # Enhanced nutritional benefits
            for ingredient in ingredients:
                if ingredient in ['salmon', 'tuna', 'fish']:
                    nutritional_benefits.append(f"🐟 {ingredient.title()}: Excellent source of omega-3 fatty acids for heart health")
                elif ingredient in ['broccoli', 'spinach', 'kale']:
                    nutritional_benefits.append(f"🥬 {ingredient.title()}: Rich in vitamins K, C, and folate")
                elif ingredient in ['blueberry', 'strawberry', 'berry']:
                    nutritional_benefits.append(f"🫐 {ingredient.title()}: High in antioxidants and vitamin C")
                elif ingredient in ['avocado']:
                    nutritional_benefits.append(f"🥑 {ingredient.title()}: Healthy monounsaturated fats and fiber")
                elif ingredient in ['quinoa']:
                    nutritional_benefits.append(f"🌾 {ingredient.title()}: Complete protein with all essential amino acids")
                elif ingredient in ['nuts', 'almond', 'walnut']:
                    nutritional_benefits.append(f"🌰 {ingredient.title()}: Healthy fats and vitamin E")
            
            return {
                'nutrition_score': min(score, 100),
                'category_analysis': categorized,
                'recommendations': recommendations,
                'allergen_warnings': allergen_warnings,
                'nutritional_benefits': nutritional_benefits,
                'ingredients': ingredients,
                'detailed_nutrition': total_nutrition,
                'food_groups_count': food_groups_present
            }
    
    class SimpleMealPlanner:
        def __init__(self):
            self.meal_database = {
                'breakfast': {
                    'high_protein': [
                        {
                            'title': "Greek Yogurt Power Bowl",
                            'ingredients': ['greek yogurt', 'berries', 'granola', 'honey', 'chia seeds'],
                            'calories': 350, 'protein': 20, 'carbs': 45, 'fat': 12
                        },
                        {
                            'title': "Scrambled Eggs with Spinach",
                            'ingredients': ['eggs', 'spinach', 'cheese', 'olive oil', 'herbs'],
                            'calories': 320, 'protein': 22, 'carbs': 8, 'fat': 24
                        },
                        {
                            'title': "Protein Smoothie Bowl",
                            'ingredients': ['protein powder', 'banana', 'peanut butter', 'almond milk', 'oats'],
                            'calories': 400, 'protein': 30, 'carbs': 35, 'fat': 15
                        },
                        {
                            'title': "Cottage Cheese Pancakes",
                            'ingredients': ['cottage cheese', 'eggs', 'oats', 'berries', 'honey'],
                            'calories': 380, 'protein': 25, 'carbs': 40, 'fat': 12
                        }
                    ],
                    'balanced': [
                        {
                            'title': "Avocado Toast with Egg",
                            'ingredients': ['whole grain bread', 'avocado', 'egg', 'tomato', 'herbs'],
                            'calories': 340, 'protein': 15, 'carbs': 35, 'fat': 18
                        },
                        {
                            'title': "Overnight Oats with Fruit",
                            'ingredients': ['oats', 'milk', 'banana', 'berries', 'nuts'],
                            'calories': 320, 'protein': 12, 'carbs': 45, 'fat': 12
                        },
                        {
                            'title': "Whole Grain Cereal Bowl",
                            'ingredients': ['whole grain cereal', 'milk', 'banana', 'almonds'],
                            'calories': 300, 'protein': 12, 'carbs': 50, 'fat': 8
                        },
                        {
                            'title': "Fruit and Yogurt Parfait",
                            'ingredients': ['yogurt', 'granola', 'mixed berries', 'honey'],
                            'calories': 280, 'protein': 15, 'carbs': 40, 'fat': 8
                        }
                    ],
                    'vegan': [
                        {
                            'title': "Chia Pudding with Fruit",
                            'ingredients': ['chia seeds', 'almond milk', 'maple syrup', 'berries', 'coconut'],
                            'calories': 290, 'protein': 8, 'carbs': 35, 'fat': 15
                        },
                        {
                            'title': "Tofu Scramble with Vegetables",
                            'ingredients': ['tofu', 'spinach', 'mushrooms', 'nutritional yeast', 'turmeric'],
                            'calories': 310, 'protein': 18, 'carbs': 15, 'fat': 20
                        },
                        {
                            'title': "Smoothie Bowl with Plant Protein",
                            'ingredients': ['plant protein powder', 'spinach', 'banana', 'coconut milk', 'seeds'],
                            'calories': 350, 'protein': 20, 'carbs': 30, 'fat': 18
                        },
                        {
                            'title': "Quinoa Breakfast Bowl",
                            'ingredients': ['quinoa', 'almond milk', 'cinnamon', 'apple', 'walnuts'],
                            'calories': 330, 'protein': 12, 'carbs': 45, 'fat': 12
                        }
                    ]
                },
                'lunch': {
                    'high_protein': [
                        {
                            'title': "Grilled Chicken Quinoa Bowl",
                            'ingredients': ['chicken breast', 'quinoa', 'mixed vegetables', 'olive oil', 'herbs'],
                            'calories': 450, 'protein': 35, 'carbs': 40, 'fat': 15
                        },
                        {
                            'title': "Tuna and White Bean Salad",
                            'ingredients': ['tuna', 'white beans', 'mixed greens', 'tomatoes', 'olive oil'],
                            'calories': 420, 'protein': 32, 'carbs': 30, 'fat': 18
                        },
                        {
                            'title': "Lentil Power Soup",
                            'ingredients': ['lentils', 'vegetables', 'vegetable broth', 'spinach', 'herbs'],
                            'calories': 380, 'protein': 22, 'carbs': 45, 'fat': 8
                        },
                        {
                            'title': "Turkey and Hummus Wrap",
                            'ingredients': ['turkey', 'hummus', 'whole wheat tortilla', 'vegetables', 'spinach'],
                            'calories': 410, 'protein': 28, 'carbs': 35, 'fat': 16
                        }
                    ],
                    'balanced': [
                        {
                            'title': "Mediterranean Chicken Bowl",
                            'ingredients': ['chicken', 'brown rice', 'cucumber', 'tomatoes', 'feta', 'olive oil'],
                            'calories': 480, 'protein': 30, 'carbs': 45, 'fat': 20
                        },
                        {
                            'title': "Salmon with Sweet Potato",
                            'ingredients': ['salmon', 'sweet potato', 'asparagus', 'lemon', 'herbs'],
                            'calories': 460, 'protein': 28, 'carbs': 35, 'fat': 22
                        },
                        {
                            'title': "Turkey Vegetable Soup",
                            'ingredients': ['turkey', 'mixed vegetables', 'broth', 'whole grain bread'],
                            'calories': 390, 'protein': 25, 'carbs': 40, 'fat': 12
                        },
                        {
                            'title': "Quinoa Buddha Bowl",
                            'ingredients': ['quinoa', 'roasted vegetables', 'chickpeas', 'tahini', 'greens'],
                            'calories': 440, 'protein': 18, 'carbs': 55, 'fat': 16
                        }
                    ],
                    'vegan': [
                        {
                            'title': "Quinoa Buddha Bowl Supreme",
                            'ingredients': ['quinoa', 'chickpeas', 'roasted vegetables', 'tahini dressing', 'hemp seeds'],
                            'calories': 450, 'protein': 18, 'carbs': 55, 'fat': 18
                        },
                        {
                            'title': "Chickpea and Vegetable Curry",
                            'ingredients': ['chickpeas', 'coconut milk', 'curry spices', 'vegetables', 'brown rice'],
                            'calories': 420, 'protein': 15, 'carbs': 60, 'fat': 15
                        },
                        {
                            'title': "Black Bean Sweet Potato Bowl",
                            'ingredients': ['black beans', 'roasted sweet potato', 'quinoa', 'avocado', 'lime'],
                            'calories': 400, 'protein': 16, 'carbs': 65, 'fat': 12
                        },
                        {
                            'title': "Mediterranean Quinoa Salad",
                            'ingredients': ['quinoa', 'tomatoes', 'cucumber', 'olives', 'lemon dressing'],
                            'calories': 380, 'protein': 12, 'carbs': 50, 'fat': 15
                        }
                    ]
                },
                'dinner': {
                    'high_protein': [
                        {
                            'title': "Baked Salmon with Quinoa",
                            'ingredients': ['salmon fillet', 'quinoa', 'roasted vegetables', 'lemon', 'herbs'],
                            'calories': 520, 'protein': 38, 'carbs': 35, 'fat': 25
                        },
                        {
                            'title': "Grilled Chicken with Sweet Potato",
                            'ingredients': ['chicken breast', 'sweet potato', 'broccoli', 'olive oil'],
                            'calories': 480, 'protein': 40, 'carbs': 30, 'fat': 18
                        },
                        {
                            'title': "Turkey Meatballs with Zucchini Noodles",
                            'ingredients': ['ground turkey', 'zucchini', 'marinara sauce', 'herbs'],
                            'calories': 420, 'protein': 35, 'carbs': 20, 'fat': 22
                        },
                        {
                            'title': "Beef and Vegetable Stir-fry",
                            'ingredients': ['lean beef', 'mixed vegetables', 'brown rice', 'ginger', 'garlic'],
                            'calories': 500, 'protein': 32, 'carbs': 40, 'fat': 20
                        }
                    ],
                    'balanced': [
                        {
                            'title': "Herb-Crusted Chicken with Vegetables",
                            'ingredients': ['chicken', 'roasted vegetables', 'quinoa', 'herbs', 'olive oil'],
                            'calories': 510, 'protein': 35, 'carbs': 40, 'fat': 22
                        },
                        {
                            'title': "Baked Cod with Brown Rice Pilaf",
                            'ingredients': ['cod', 'brown rice', 'vegetables', 'lemon', 'herbs'],
                            'calories': 450, 'protein': 30, 'carbs': 45, 'fat': 12
                        },
                        {
                            'title': "Turkey Chili with Cornbread",
                            'ingredients': ['ground turkey', 'beans', 'tomatoes', 'vegetables', 'cornbread'],
                            'calories': 480, 'protein': 28, 'carbs': 50, 'fat': 18
                        },
                        {
                            'title': "Salmon with Quinoa Pilaf",
                            'ingredients': ['salmon', 'quinoa', 'roasted vegetables', 'lemon dressing'],
                            'calories': 520, 'protein': 32, 'carbs': 40, 'fat': 24
                        }
                    ],
                    'vegan': [
                        {
                            'title': "Lentil Bolognese with Zucchini Noodles",
                            'ingredients': ['red lentils', 'zucchini', 'marinara sauce', 'nutritional yeast', 'herbs'],
                            'calories': 380, 'protein': 18, 'carbs': 45, 'fat': 12
                        },
                        {
                            'title': "Stuffed Bell Peppers with Quinoa",
                            'ingredients': ['bell peppers', 'quinoa', 'black beans', 'vegetables', 'herbs'],
                            'calories': 420, 'protein': 16, 'carbs': 60, 'fat': 12
                        },
                        {
                            'title': "Chickpea Curry with Brown Rice",
                            'ingredients': ['chickpeas', 'coconut milk', 'curry spices', 'brown rice', 'spinach'],
                            'calories': 450, 'protein': 18, 'carbs': 65, 'fat': 15
                        },
                        {
                            'title': "Tofu and Vegetable Stir-fry",
                            'ingredients': ['tofu', 'mixed vegetables', 'brown rice', 'sesame oil', 'ginger'],
                            'calories': 400, 'protein': 20, 'carbs': 45, 'fat': 16
                        }
                    ]
                }
            }
        
        def generate_weekly_plan(self, user_profile):
            health_goals = user_profile.get('health_goals', [])
            diet_type = user_profile.get('diet_type', 'balanced').lower()
            
            # Determine meal category based on goals and diet type
            if 'Muscle Gain' in health_goals:
                meal_category = 'high_protein'
            elif diet_type == 'vegan':
                meal_category = 'vegan'
            else:
                meal_category = 'balanced'
            
            weekly_plan = {}
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days:
                daily_meals = {}
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    meals = self.meal_database[meal_type].get(meal_category, 
                                                            self.meal_database[meal_type]['balanced'])
                    selected_meal = random.choice(meals)
                    
                    # Handle both old string format and new dict format
                    if isinstance(selected_meal, dict):
                        daily_meals[meal_type] = {
                            'title': selected_meal['title'],
                            'ingredients': selected_meal['ingredients'],
                            'instructions': self._generate_instructions(selected_meal['title']),
                            'nutrition': {
                                'calories': selected_meal['calories'],
                                'protein': selected_meal['protein'],
                                'carbohydrates': selected_meal['carbs'],
                                'fat': selected_meal['fat']
                            }
                        }
                    else:
                        # Fallback for old string format
                        daily_meals[meal_type] = {
                            'title': selected_meal,
                            'ingredients': self._generate_ingredients(selected_meal),
                            'instructions': self._generate_instructions(selected_meal),
                            'nutrition': self._estimate_nutrition(meal_category)
                        }
                
                weekly_plan[day] = daily_meals
            
            return weekly_plan
        
        def _generate_ingredients(self, meal_title):
            # Simple ingredient generation based on meal title
            ingredients = []
            meal_lower = meal_title.lower()
            
            if 'chicken' in meal_lower:
                ingredients.extend(['chicken breast', 'olive oil', 'garlic', 'herbs'])
            if 'salmon' in meal_lower:
                ingredients.extend(['salmon fillet', 'lemon', 'herbs', 'olive oil'])
            if 'quinoa' in meal_lower:
                ingredients.extend(['quinoa', 'vegetable broth', 'onion'])
            if 'yogurt' in meal_lower:
                ingredients.extend(['greek yogurt', 'berries', 'honey', 'granola'])
            
            return ingredients if ingredients else ['main ingredient', 'seasonings', 'cooking oil']
        
        def _generate_instructions(self, meal_title):
            # Enhanced instructions based on meal type
            meal_lower = meal_title.lower()
            
            if 'smoothie' in meal_lower:
                return [
                    "1. Add liquid ingredients to blender first",
                    "2. Add frozen fruits and protein powder",
                    "3. Blend until smooth and creamy",
                    "4. Pour into bowl and add toppings"
                ]
            elif 'scramble' in meal_lower or 'eggs' in meal_lower:
                return [
                    "1. Heat oil in non-stick pan over medium heat",
                    "2. Add vegetables and sauté for 2-3 minutes",
                    "3. Add beaten eggs and gently scramble",
                    "4. Season with herbs and serve hot"
                ]
            elif 'salad' in meal_lower or 'bowl' in meal_lower:
                return [
                    "1. Prepare and wash all vegetables",
                    "2. Cook grains/proteins according to package instructions",
                    "3. Arrange ingredients in bowl",
                    "4. Drizzle with dressing and toss gently"
                ]
            elif 'soup' in meal_lower or 'curry' in meal_lower:
                return [
                    "1. Sauté aromatics (onion, garlic, ginger) in oil",
                    "2. Add spices and cook for 30 seconds",
                    "3. Add liquid and main ingredients, bring to boil",
                    "4. Simmer until tender and flavors develop"
                ]
            elif 'grilled' in meal_lower or 'baked' in meal_lower:
                return [
                    "1. Preheat oven/grill to appropriate temperature",
                    "2. Season protein with herbs and spices",
                    "3. Cook until internal temperature is safe",
                    "4. Rest for 5 minutes before serving"
                ]
            else:
                return [
                    "1. Prepare all ingredients and equipment",
                    "2. Follow cooking method appropriate for main ingredient",
                    "3. Season to taste with herbs and spices",
                    "4. Serve immediately while hot"
                ]
        
        def _estimate_nutrition(self, category):
            base_nutrition = {
                'high_protein': {'calories': 400, 'protein': 35, 'carbohydrates': 20, 'fat': 15},
                'balanced': {'calories': 425, 'protein': 25, 'carbohydrates': 35, 'fat': 20},
                'vegan': {'calories': 375, 'protein': 15, 'carbohydrates': 45, 'fat': 18}
            }
            return base_nutrition.get(category, base_nutrition['balanced'])
    
    class SimpleChatbot:
        def __init__(self):
            self.responses = {
                'protein': "Great sources of protein include chicken, fish, eggs, beans, and tofu. Aim for 0.8-1g per kg of body weight daily.",
                'weight loss': "For weight loss, focus on creating a caloric deficit through portion control and regular exercise. Include plenty of vegetables and lean proteins.",
                'muscle gain': "For muscle gain, increase protein intake to 1.6-2.2g per kg body weight, include complex carbs, and ensure adequate calories.",
                'vegan': "Vegan meals can include quinoa bowls, lentil curries, tofu stir-fries, and plant-based protein smoothies.",
                'recipe': "I can help analyze recipes! Please list the main ingredients and I'll provide nutritional insights."
            }
        
        def process_message(self, message, user_profile=None):
            message_lower = message.lower()
            
            for keyword, response in self.responses.items():
                if keyword in message_lower:
                    return response
            
            return "I'm here to help with nutrition questions! Ask me about protein, weight loss, muscle gain, vegan meals, or recipe analysis."
    
    # Use simplified versions if full features not available
    DatabaseManager = SimpleDatabaseManager
    nlp_analyzer = SimpleNLPAnalyzer()
    meal_planner = SimpleMealPlanner()
    nutrition_chatbot = SimpleChatbot()
st.set_page_config(
    page_title="Nutrition Assistant",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'daily_calories' not in st.session_state:
    st.session_state.daily_calories = 0
if 'daily_water' not in st.session_state:
    st.session_state.daily_water = 0
if 'daily_exercise' not in st.session_state:
    st.session_state.daily_exercise = 0
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

def main():
    """Main application function"""
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2E8B57;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .chat-message {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f1f8e9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication
    if st.session_state.user_id is None:
        show_auth_page()
    else:
        show_dashboard()

def show_auth_page():
    """Show authentication page"""
    st.markdown('<h1 class="main-header">🥗 Nutrition Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #666;">Your AI-Powered Nutrition Companion</h3>', 
                unsafe_allow_html=True)
    
    # Create tabs for login and register
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()
    
    # App features preview
    st.markdown("---")
    st.markdown("### 🌟 Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI Meal Analysis</h4>
            <p>Get instant nutritional analysis of your meals using advanced NLP</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📅 Smart Meal Planning</h4>
            <p>Generate personalized 7-day meal plans based on your goals</p>
        </div>
        """, unsafe_allow_html=True)
    
    

def show_login_form():
    """Show login form"""
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                result = db.authenticate_user(username, password)
                if result['success']:
                    st.session_state.user_id = result['user_id']
                    st.session_state.username = result['username']
                    
                    # Load user profile
                    profile = db.get_user_profile(result['user_id'])
                    st.session_state.user_profile = profile
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result['error'])
            else:
                st.error("Please fill in all fields")

def show_register_form():
    """Show registration form"""
    st.subheader("Create New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if username and email and password and confirm_password:
                if password == confirm_password:
                    result = db.register_user(username, email, password)
                    if result['success']:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error(result['error'])
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill in all fields")

def show_dashboard():
    """Show main dashboard"""
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}! 👋")
        
        menu_options = [
            "🏠 Dashboard",
            "👤 Profile Setup",
            "🍽️ Meal Analysis",
            "📅 Meal Planning",
            "📊 Analytics",
            "📱 Daily Tracker",
            "📈 Progress Reports",
            "🎯 Goal Setting",
            "⚙️ Settings"
        ]
        
        selected_option = st.selectbox("Navigation", menu_options)
        
        st.markdown("---")
        if st.button("Logout"):
            # Clear session state
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    # Main content based on selection
    if selected_option == "🏠 Dashboard":
        show_home_dashboard()
    elif selected_option == "👤 Profile Setup":
        show_profile_setup()
    elif selected_option == "🍽️ Meal Analysis":
        show_meal_analysis()
    elif selected_option == "📅 Meal Planning":
        show_meal_planning()
    elif selected_option == "📊 Analytics":
        show_analytics()
    elif selected_option == "📱 Daily Tracker":
        show_daily_tracker()
    elif selected_option == "📈 Progress Reports":
        show_progress_reports()
    elif selected_option == "🎯 Goal Setting":
        show_goal_setting()
    elif selected_option == "⚙️ Settings":
        show_settings()

def show_home_dashboard():
    """Show home dashboard"""
    st.markdown('<h1 class="main-header">🏠 Nutrition Dashboard</h1>', unsafe_allow_html=True)
    
    # Get user stats
    if st.session_state.user_id:
        try:
            stats = db.get_meal_stats(st.session_state.user_id)
        except:
            stats = {"meals_analyzed": 0, "meal_plans": 0}
    else:
        stats = {"meals_analyzed": 0, "meal_plans": 0}
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        profile_status = "Complete" if st.session_state.user_profile else "Incomplete"
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯</h3>
            <h4>Profile Status</h4>
            <p>{profile_status}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🍽️</h3>
            <h4>Meals Analyzed</h4>
            <p>{stats['meals_analyzed']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📅</h3>
            <h4>Meal Plans</h4>
            <p>{stats['meal_plans']}</p>
        </div>
        """, unsafe_allow_html=True)
    
   
    
    st.markdown("---")
    
    # Load today's data from database if not already in session state
    if 'daily_calories' not in st.session_state:
        st.session_state.daily_calories = 0
    if 'daily_water' not in st.session_state:
        st.session_state.daily_water = 0
    if 'daily_exercise' not in st.session_state:
        st.session_state.daily_exercise = 0
    
    # Load today's data from database
    today = datetime.now().date()
    today_logs = db.get_daily_logs(st.session_state.user_id, 1)  # Get today's log
    
    if today_logs and len(today_logs) > 0 and today_logs[0]['date'] == str(today):
        # Update session state with today's data from database
        st.session_state.daily_calories = today_logs[0].get('calories', 0)
        st.session_state.daily_water = today_logs[0].get('water', 0)
        st.session_state.daily_exercise = today_logs[0].get('exercise', 0)
    
    # Enhanced Today's Summary with Progress Tracking
    if st.session_state.user_profile:
        st.subheader("📅 Today's Progress Dashboard")
        
        # Calculate daily targets based on profile
        profile = st.session_state.user_profile
        height_m = profile.get('height', 170) / 100
        weight = profile.get('weight', 70)
        age = profile.get('age', 25)
        gender = profile.get('gender', 'Male')
        
        # Calculate BMR and daily calorie target
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
        
        activity_multipliers = {
            'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
            'Very Active': 1.725, 'Extremely Active': 1.9
        }
        
        daily_calorie_target = int(bmr * activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55))
        daily_water_target = int(weight * 35)  # 35ml per kg
        daily_exercise_target = 30  # 30 minutes
        
        # Progress metrics with targets and progress bars
        col1, col2, col3 = st.columns(3)
        
        with col1:
            calorie_progress = min(st.session_state.daily_calories / daily_calorie_target * 100, 100) if daily_calorie_target > 0 else 0
            st.metric(
                "Calories Today", 
                f"{st.session_state.daily_calories}/{daily_calorie_target} kcal",
                f"{calorie_progress:.1f}% of target"
            )
            # Enhanced progress bar
            progress_color = "green" if calorie_progress >= 80 else "orange" if calorie_progress >= 60 else "red"
            
        with col2:
            water_progress = min(st.session_state.daily_water / daily_water_target * 100, 100) if daily_water_target > 0 else 0
            st.metric(
                "Water Intake", 
                f"{st.session_state.daily_water}/{daily_water_target} ml",
                f"{water_progress:.1f}% of target"
            )
            # Water progress bar
            water_color = "blue" if water_progress >= 80 else "lightblue" if water_progress >= 60 else "gray"
           
        with col3:
            exercise_progress = min(st.session_state.daily_exercise / daily_exercise_target * 100, 100) if daily_exercise_target > 0 else 0
            st.metric(
                "Exercise Today", 
                f"{st.session_state.daily_exercise}/{daily_exercise_target} min",
                f"{exercise_progress:.1f}% of target"
            )
            # Exercise progress bar
            exercise_color = "green" if exercise_progress >= 100 else "orange" if exercise_progress >= 50 else "red"
        
        # Daily achievement status
        achievements = []
        if calorie_progress >= 80 and calorie_progress <= 120:
            achievements.append("🎯 Calorie goal achieved!")
        if water_progress >= 80:
            achievements.append("💧 Hydration goal achieved!")
        if exercise_progress >= 100:
            achievements.append("🏃 Exercise goal achieved!")
        
        if achievements:
            st.success(" | ".join(achievements))
        elif calorie_progress < 50 and water_progress < 50 and exercise_progress < 50:
            st.info("💪 Let's start tracking your daily progress!")
        else:
            st.info("📈 Keep going! You're making progress towards your daily goals.")
        
        # Enhanced Quick Log with Smart Suggestions
        st.subheader("⚡ Smart Quick Log")
        
        # Show personalized quick log options based on current progress and time
        current_hour = datetime.now().hour
        suggestions = []
        
        # Time-based suggestions
        if 6 <= current_hour <= 10:  # Morning
            suggestions.extend([
                ("☕ Coffee (5 cal)", 5, 0, 0),
                ("🥛 Banana (105 cal)", 105, 0, 0),
                ("🍳 Breakfast logged", 300, 0, 0)
            ])
        elif 11 <= current_hour <= 14:  # Lunch time
            suggestions.extend([
                ("🥗 Mixed salad (150 cal)", 150, 0, 0),
                ("🍽️ Lunch logged", 450, 0, 0),
                ("💧 Post-meal water", 0, 300, 0)
            ])
        elif 18 <= current_hour <= 21:  # Dinner time
            suggestions.extend([
                ("🍽️ Dinner logged", 500, 0, 0),
                ("🥦 Vegetables (50 cal)", 50, 0, 0)
            ])
        
        # Always available options
        suggestions.extend([
            ("💧 +250ml Water", 0, 250, 0),
            ("🍎 Apple (80 cal)", 80, 0, 0),
            ("🏊 15min Exercise", 0, 0, 15),
            ("🚪 30min Workout", 0, 0, 30)
        ])
        
        # Display quick log buttons in a responsive grid
        num_cols = 4
        cols = st.columns(num_cols)
        
        for i, (label, calories, water, exercise) in enumerate(suggestions[:8]):  # Show max 8 options
            with cols[i % num_cols]:
                if st.button(label, use_container_width=True, key=f"quick_log_{i}"):
                    if calories > 0:
                        st.session_state.daily_calories += calories
                        st.success(f"✅ Added {calories} calories!")
                    if water > 0:
                        st.session_state.daily_water += water
                        st.success(f"✅ Added {water}ml water!")
                    if exercise > 0:
                        st.session_state.daily_exercise += exercise
                        st.success(f"✅ Added {exercise} minutes exercise!")
                    
                    # Save to database immediately
                    log_data = {
                        'date': today,
                        'calories': st.session_state.daily_calories,
                        'water': st.session_state.daily_water,
                        'exercise': st.session_state.daily_exercise,
                        'notes': f"Quick log update at {datetime.now().strftime('%H:%M')}"
                    }
                    try:
                        result = db.save_daily_log(st.session_state.user_id, log_data)
                        if not result.get('success', True):
                            st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error saving log: {str(e)}")
                        
                    st.rerun()
        
        # Custom entry section
        st.markdown("**Custom Entry:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            custom_calories = st.number_input("Calories", min_value=0, max_value=1000, value=0, key="custom_cal")
            if st.button("➕ Add Calories", use_container_width=True) and custom_calories > 0:
                st.session_state.daily_calories += custom_calories
                st.success(f"✅ Added {custom_calories} calories!")
                
                # Save to database immediately
                log_data = {
                    'date': today,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Custom calories added at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if not result.get('success', True):
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
                st.rerun()
        
        with col2:
            custom_water = st.number_input("Water (ml)", min_value=0, max_value=2000, value=0, key="custom_water")
            if st.button("➕ Add Water", use_container_width=True) and custom_water > 0:
                st.session_state.daily_water += custom_water
                st.success(f"✅ Added {custom_water}ml water!")
                
                # Save to database immediately
                log_data = {
                    'date': today,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Custom water added at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if not result.get('success', True):
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
                st.rerun()
        
        with col3:
            custom_exercise = st.number_input("Exercise (min)", min_value=0, max_value=180, value=0, key="custom_ex")
            if st.button("➕ Add Exercise", use_container_width=True) and custom_exercise > 0:
                st.session_state.daily_exercise += custom_exercise
                st.success(f"✅ Added {custom_exercise} minutes!")
                
                # Save to database immediately
                log_data = {
                    'date': today,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Custom exercise added at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if not result.get('success', True):
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
                st.rerun()
        
        with col4:
            st.markdown("**Daily Log:**")
            if st.button("💾 Save Complete Log", use_container_width=True):
                log_data = {
                    'date': today,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Manual save at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if result.get('success', True):
                        st.success("✅ Today's complete log saved!")
                        # Show summary
                        st.info(f"📈 Summary: {log_data['calories']} cal | {log_data['water']} ml | {log_data['exercise']} min")
                    else:
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
            # Reset button
            if st.button("🔄 Reset Today", use_container_width=True):
                st.session_state.daily_calories = 0
                st.session_state.daily_water = 0
                st.session_state.daily_exercise = 0
                
                # Save reset state to database
                log_data = {
                    'date': today,
                    'calories': 0,
                    'water': 0,
                    'exercise': 0,
                    'notes': f"Reset at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if result.get('success', True):
                        st.success("✅ Today's tracking reset!")
                    else:
                        st.error(f"❌ Error resetting: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error resetting log: {str(e)}")
                    
                st.rerun()
    
    st.markdown("---")
    
    # Additional quick tools
    st.markdown("**Additional Tools:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🧾 BMI Calculator", use_container_width=True):
            if st.session_state.user_profile:
                profile = st.session_state.user_profile
                height_m = profile.get('height', 170) / 100
                weight = profile.get('weight', 70)
                bmi = weight / (height_m ** 2)
                
                if bmi < 18.5:
                    category = "Underweight"
                    color = "blue"
                elif bmi < 25:
                    category = "Normal"
                    color = "green"
                elif bmi < 30:
                    category = "Overweight"
                    color = "orange"
                else:
                    category = "Obese"
                    color = "red"
                
                st.info(f"📊 Your BMI: {bmi:.1f} ({category})")
            else:
                st.warning("Complete profile to calculate BMI")
    
    with col2:
        if st.button("💧 Hydration Check", use_container_width=True):
            if st.session_state.user_profile:
                weight = st.session_state.user_profile.get('weight', 70)
                target_water = weight * 35
                current_water = st.session_state.daily_water
                remaining = max(0, target_water - current_water)
                
                if remaining == 0:
                    st.success(f"🎆 Hydration goal achieved! ({current_water}ml)")
                else:
                    st.info(f"💧 Drink {remaining}ml more water today!")
            else:
                st.warning("Set your weight in profile for hydration tracking")
    
    with col3:
        if st.button("🔥 Calorie Tracker", use_container_width=True):
            if st.session_state.user_profile:
                # Calculate calorie target
                profile = st.session_state.user_profile
                height_m = profile.get('height', 170) / 100
                weight = profile.get('weight', 70)
                age = profile.get('age', 25)
                gender = profile.get('gender', 'Male')
                
                if gender == 'Male':
                    bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
                else:
                    bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
                
                activity_multipliers = {
                    'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
                    'Very Active': 1.725, 'Extremely Active': 1.9
                }
                
                target_calories = int(bmr * activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55))
                current_calories = st.session_state.daily_calories
                remaining = max(0, target_calories - current_calories)
                
                if remaining <= 100:
                    st.success(f"🎯 Calorie goal nearly reached! ({current_calories}/{target_calories})")
                else:
                    st.info(f"🔥 {remaining} calories remaining for today")
            else:
                st.warning("Complete profile for calorie tracking")
    
    with col4:
        if st.button("🏃 Exercise Goal", use_container_width=True):
            target_exercise = 30  # minutes
            current_exercise = st.session_state.daily_exercise
            remaining = max(0, target_exercise - current_exercise)
            
            if remaining == 0:
                st.success(f" YYS Exercise goal achieved! ({current_exercise} min)")
            else:
                st.info(f"🏃 {remaining} minutes of exercise remaining today")
    
    # Personalized recommendations
    if st.session_state.user_profile:
        st.markdown("---")
        st.subheader("💡 Personalized Recommendations")
        
        profile = st.session_state.user_profile
        goals = profile.get('health_goals', [])
        
        recommendations = []
        
        if 'Weight Loss' in goals:
            recommendations.append("🎯 Focus on portion control and increase vegetable intake")
        if 'Muscle Gain' in goals:
            recommendations.append("💪 Ensure adequate protein intake (1.6-2.2g per kg body weight)")
        if 'Balanced Diet' in goals:
            recommendations.append("⚖️ Follow the plate method: 1/2 vegetables, 1/4 protein, 1/4 grains")
        
        # Calculate BMI and add recommendation
        height_m = profile.get('height', 170) / 100
        weight = profile.get('weight', 70)
        bmi = weight / (height_m ** 2)
        
        if bmi < 18.5:
            recommendations.append("🐈 Consider increasing caloric intake with healthy foods")
        elif bmi > 25:
            recommendations.append("🏃 Consider regular exercise and caloric moderation")
        
        for rec in recommendations:
            st.info(rec)
    
    # Profile completion reminder
    if not st.session_state.user_profile:
        st.warning("⚠️ Complete your profile to get personalized recommendations!")
        if st.button("Complete Profile Now"):
            st.session_state.selected_option = "👤 Profile Setup"
            st.rerun()

def show_profile_setup():
    """Show profile setup page"""
    st.markdown('<h1 class="main-header">👤 Profile Setup</h1>', unsafe_allow_html=True)
    
    st.info("💡 Complete your profile to get personalized nutrition recommendations!")
    
    # Get existing profile data
    existing_profile = st.session_state.user_profile or {}
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Information")
            age = st.number_input(
                "Age", 
                min_value=10, max_value=120, 
                value=int(existing_profile.get('age', 25))
            )
            gender = st.selectbox(
                "Gender", 
                ["Male", "Female", "Other"], 
                index=["Male", "Female", "Other"].index(existing_profile.get('gender', 'Male'))
            )
            height = st.number_input(
                "Height (cm)", 
                min_value=100, max_value=250, 
                value=int(existing_profile.get('height', 170))
            )
            weight = st.number_input(
                "Weight (kg)", 
                min_value=30, max_value=300, 
                value=int(existing_profile.get('weight', 70))
            )
        
        with col2:
            st.subheader("Lifestyle & Goals")
            activity_level = st.selectbox(
                "Activity Level",
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                index=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"].index(
                    existing_profile.get('activity_level', 'Moderately Active'))
            )
            
            diet_type = st.selectbox(
                "Diet Type",
                ["Balanced", "Vegetarian", "Vegan", "Keto", "Paleo", "Mediterranean"],
                index=["Balanced", "Vegetarian", "Vegan", "Keto", "Paleo", "Mediterranean"].index(
                    existing_profile.get('diet_type', 'Balanced'))
            )
        
        st.subheader("Health Goals")
        health_goals = st.multiselect(
            "Select your health goals:",
            ["Weight Loss", "Muscle Gain", "Balanced Diet", "Energy Boost", "Better Digestion", "Heart Health"],
            default=existing_profile.get('health_goals', [])
        )
        
        st.subheader("Allergies & Restrictions")
        allergens = st.multiselect(
            "Select any allergens or dietary restrictions:",
            ["Nuts", "Dairy", "Gluten", "Shellfish", "Eggs", "Soy", "Fish"],
            default=existing_profile.get('allergens', [])
        )
        
        # ✅ Submit button is required in forms
        submit_button = st.form_submit_button("Save Profile", use_container_width=True)
        
        if submit_button:
            profile_data = {
                'age': age,
                'gender': gender,
                'height': height,
                'weight': weight,
                'activity_level': activity_level,
                'diet_type': diet_type,
                'health_goals': health_goals,
                'allergens': allergens
            }
            
            result = db.save_user_profile(st.session_state.user_id, profile_data)
            if result['success']:
                st.session_state.user_profile = profile_data
                st.success("✅ Profile saved successfully!")
                
                # Calculate BMI
                bmi = weight / ((height/100) ** 2)
                st.info(f"Your BMI: {bmi:.1f}")
                
            else:
                st.error(f"Error saving profile: {result['error']}")

def show_meal_analysis():
    """Show meal analysis page"""
    st.markdown('<h1 class="main-header">🍽️ Meal Analysis</h1>', unsafe_allow_html=True)
    
    st.info("🤖 Enter your meal details and get instant nutritional analysis powered by advanced NLP!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🍽️ Analyze Your Meal")
        
        with st.form("meal_analysis_form"):
            meal_description = st.text_area(
                "Describe your meal:",
                placeholder="e.g., Grilled chicken with quinoa and steamed broccoli",
                height=100
            )
            
            meal_type = st.selectbox(
                "Meal Type:",
                ["Breakfast", "Lunch", "Dinner", "Snack"]
            )
            
            if st.form_submit_button("Analyze Meal"):
                if meal_description:
                    with st.spinner("Analyzing your meal..."):
                        # Extract ingredients using NLP
                        ingredients = nlp_analyzer.extract_ingredients(meal_description)
                        
                        if ingredients:
                            # Analyze nutrition
                            analysis = nlp_analyzer.analyze_meal_nutrition(
                                ingredients, 
                                st.session_state.user_profile
                            )
                            
                            # Save to database
                            meal_data = {
                                'meal_name': meal_description[:50] + "..." if len(meal_description) > 50 else meal_description,
                                'ingredients': ingredients,
                                'analysis_result': analysis,
                                'meal_type': meal_type
                            }
                            db.save_meal_log(st.session_state.user_id, meal_data)
                            
                            # Display results
                            show_meal_analysis_results(analysis, ingredients)
                        else:
                            st.error("Please describe your meal or list ingredients")
                else:
                    st.error("Please describe your meal or list ingredients")

    with col2:
        st.subheader("💡 Tips")
        st.markdown("""
        **For better analysis:**
        - List specific ingredients
        - Include cooking methods
        - Mention quantities if known
        - Be as descriptive as possible
        
        **Example inputs:**
        - "Salmon with quinoa and steamed broccoli"
        - "Greek yogurt with berries and honey"
        - "Chicken stir-fry with vegetables and brown rice"
        """)

def show_meal_analysis_results(analysis, ingredients):
    """Display meal analysis results"""
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    # Nutrition score and summary
    score = analysis['nutrition_score']
    score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"
    
    # Display meal summary with detailed nutrition if available
    if 'meal_summary' in analysis:
        st.subheader("🍽️ Meal Summary")
        summary = analysis['meal_summary']
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Calories", f"{summary['total_calories']:.0f}")
        with col2:
            st.metric("Protein", f"{summary['total_protein_g']:.1f}g")
        with col3:
            st.metric("Carbs", f"{summary['total_carbs_g']:.1f}g")
        with col4:
            st.metric("Fat", f"{summary['total_fat_g']:.1f}g")
        with col5:
            st.metric("Fiber", f"{summary['total_fiber_g']:.1f}g")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Nutrition Score", f"{score}/100")
        st.markdown(f'<div style="width: {score}%; height: 10px; background-color: {score_color}; border-radius: 5px;"></div>', 
                   unsafe_allow_html=True)
    
    with col2:
        st.metric("Ingredients Found", len(ingredients))
    
    with col3:
        food_groups = len([cat for cat, items in analysis['category_analysis'].items() if items])
        st.metric("Food Groups", food_groups)
    
    # Macronutrient distribution
    if 'meal_summary' in analysis:
        summary = analysis['meal_summary']
        fig = go.Figure(data=[go.Pie(
            labels=['Protein', 'Carbohydrates', 'Fat'],
            values=[summary['protein_percentage'], summary['carb_percentage'], summary['fat_percentage']],
            marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1'],
            textinfo='label+percent'
        )])
        fig.update_layout(title="Macronutrient Distribution", height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col1:
        st.subheader("🥗 Food Group Analysis")
        categories = analysis['category_analysis']
        for category, items in categories.items():
            if items:
                st.write(f"**{category.title()}:** {', '.join(items)}")
    
    with col2:
        st.subheader("💡 Recommendations")
        if analysis['recommendations']:
            for rec in analysis['recommendations']:
                st.write(f"• {rec}")
        else:
            st.write("Great job! Your meal looks well-balanced.")
    
    # Benefits and warnings
    if analysis['nutritional_benefits']:
        st.subheader("✨ Nutritional Benefits")
        for benefit in analysis['nutritional_benefits']:
            st.success(benefit)
    
    if analysis['allergen_warnings']:
        st.subheader("⚠️ Allergen Warnings")
        for warning in analysis['allergen_warnings']:
            st.warning(warning)

def show_meal_planning():
    """Show meal planning page"""
    st.markdown('<h1 class="main-header">📅 Weekly Meal Planning</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Please complete your profile first to get personalized meal plans!")
        if st.button("Go to Profile Setup"):
            st.session_state.selected_option = "👤 Profile Setup"
            st.rerun()
        return
    
    st.info("🤖 Generate a personalized 7-day meal plan based on your profile and goals!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Plan Preferences")
        
        week_start = st.date_input("Week Starting", value=datetime.now().date())
        
        special_requests = st.text_area(
            "Special Requests or Preferences:",
            placeholder="e.g., More vegetarian options, quick meals, specific cuisines",
            height=100
        )
        
        if st.button("🎯 Generate Meal Plan", use_container_width=True):
            with st.spinner("Creating your personalized meal plan..."):
                try:
                    # Generate meal plan
                    weekly_plan = meal_planner.generate_weekly_plan(st.session_state.user_profile)
                    
                    # Save to database
                    db.save_meal_plan(st.session_state.user_id, weekly_plan, week_start)
                    
                    # Display the plan
                    show_weekly_meal_plan(weekly_plan)
                    
                except Exception as e:
                    st.error(f"Error generating meal plan: {str(e)}")
                    # Show a fallback plan even if there's an error
                    st.info("Showing sample meal plan:")
                    sample_plan = meal_planner._generate_fallback_plan(st.session_state.user_profile)
                    show_weekly_meal_plan(sample_plan)
    
    with col2:
        st.subheader("Your Profile Summary")
        profile = st.session_state.user_profile
        
        st.write(f"**Diet Type:** {profile.get('diet_type', 'Not set')}")
        st.write(f"**Goals:** {', '.join(profile.get('health_goals', []))}")
        st.write(f"**Activity Level:** {profile.get('activity_level', 'Not set')}")
        
        if profile.get('allergens'):
            st.write(f"**Allergens:** {', '.join(profile['allergens'])}")
        
        # Add nutrition summary
        st.subheader("Nutrition Summary")
        # Calculate BMR and daily calories
        height_m = profile.get('height', 170) / 100
        weight = profile.get('weight', 70)
        age = profile.get('age', 25)
        gender = profile.get('gender', 'Male')
        
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
        
        activity_multipliers = {
            'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
            'Very Active': 1.725, 'Extremely Active': 1.9
        }
        
        daily_calories = int(bmr * activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55))
        st.write(f"**Daily Calories:** {daily_calories} kcal")
        
        # Protein recommendation based on goals
        health_goals = profile.get('health_goals', [])
        if 'Muscle Gain' in health_goals:
            protein_target = weight * 2.2  # 2.2g per kg for muscle gain
            st.write(f"**Protein Target:** {protein_target:.0f}g")
        else:
            protein_target = weight * 1.2  # 1.2g per kg for maintenance
            st.write(f"**Protein Target:** {protein_target:.0f}g")

def show_weekly_meal_plan(weekly_plan):
    """Display the generated weekly meal plan"""
    st.markdown("---")
    st.subheader("🗓️ Your Weekly Meal Plan")
    
    # Remove plan info if it exists (internal data)
    display_plan = {k: v for k, v in weekly_plan.items() if k != '_plan_info'}
    
    # Create tabs for each day
    days = list(display_plan.keys())
    if not days:
        st.warning("No meal plan data available.")
        return
        
    tabs = st.tabs(days)
    
    for i, day in enumerate(days):
        with tabs[i]:
            meals = display_plan[day]
            
            # Skip if this is metadata
            if day == '_plan_info':
                continue
                
            for meal_type, meal_data in meals.items():
                # Skip if meal_data is not a dict (could be metadata)
                if not isinstance(meal_data, dict):
                    continue
                    
                title = meal_data.get('title', 'Unknown Meal')
                with st.expander(f"{meal_type.title()}: {title}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Ingredients:**")
                        ingredients = meal_data.get('ingredients', [])
                        if ingredients:
                            for ingredient in ingredients[:10]:  # Show first 10
                                st.write(f"• {ingredient}")
                        else:
                            st.write("Ingredient list not available")
                        
                        # Show allergen warnings if any
                        if meal_data.get('allergen_warning'):
                            st.warning(meal_data['allergen_warning'])
                    
                    with col2:
                        st.write("**Nutrition (estimated):**")
                        nutrition = meal_data.get('nutrition', {})
                        if nutrition:
                            for nutrient, data in nutrition.items():
                                if isinstance(data, dict):
                                    amount = data.get('amount', 0)
                                    unit = data.get('unit', '')
                                    st.write(f"• {nutrient.title()}: {amount} {unit}")
                                else:
                                    st.write(f"• {nutrient.title()}: {data}")
                        else:
                            st.write("Nutrition information not available")
                    
                    instructions = meal_data.get('instructions', [])
                    if instructions:
                        st.write("**Instructions:**")
                        for i, instruction in enumerate(instructions[:10], 1):  # Show first 10 steps
                            st.write(f"{i}. {instruction}")
                    elif meal_data.get('estimated'):
                        st.info("📋 Estimated recipe - customize to your preferences!")
    
    # Download option
    if st.button("📄 Download Meal Plan as JSON"):
        plan_json = json.dumps(weekly_plan, indent=2)
        st.download_button(
            label="Download",
            data=plan_json,
            file_name=f"meal_plan_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

def show_chatbot():
    """Show nutrition chatbot interface"""
    st.markdown('<h1 class="main-header">💬 Nutrition Chatbot</h1>', unsafe_allow_html=True)
    
    st.info("🤖 Ask me anything about nutrition! I can help with meal suggestions, recipe analysis, and dietary advice.")
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("💭 Conversation History")
        
        for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
            if 'user' in message:
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["user"]}</div>', 
                          unsafe_allow_html=True)
            elif 'assistant' in message:
                st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["assistant"]}</div>', 
                          unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    
    # Example queries
    st.subheader("💡 Try these example queries:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🥗 I want a high-protein lunch for muscle gain"):
            process_chat_message("I want a high-protein lunch for muscle gain")
        
        if st.button("🍗 Analyze this recipe: chicken, rice, broccoli"):
            process_chat_message("Analyze this recipe: chicken, rice, broccoli")
    
    with col2:
        if st.button("🌱 Suggest vegan meals for the week"):
            process_chat_message("Suggest vegan meals for the week")
        
        if st.button("💪 What foods help with muscle recovery?"):
            process_chat_message("What foods help with muscle recovery?")
    
    # Text input for custom messages
    user_input = st.text_input("Ask me anything about nutrition:", key="chat_input")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("Send Message", use_container_width=True) and user_input:
            process_chat_message(user_input)
    
    with col2:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

def process_chat_message(message):
    """Process a chat message and get response"""
    with st.spinner("Thinking..."):
        # Get response from chatbot
        response = nutrition_chatbot.process_message(message, st.session_state.user_profile)
        
        # Add to session history
        st.session_state.chat_history.append({'user': message})
        st.session_state.chat_history.append({'assistant': response})
        
        st.rerun()

def show_analytics():
    """Show enhanced analytics and insights"""
    st.markdown('<h1 class="main-header">📊 Nutrition Analytics</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Complete your profile to see personalized analytics!")
        return
    
    # BMI Calculation and comprehensive health metrics
    profile = st.session_state.user_profile
    height_m = profile.get('height', 170) / 100
    weight = profile.get('weight', 70)
    age = profile.get('age', 25)
    gender = profile.get('gender', 'Male')
    bmi = weight / (height_m ** 2)
    
    # Health metrics dashboard
    st.subheader("📊 Health Metrics Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current BMI", f"{bmi:.1f}")
        
        # BMI category with color coding
        if bmi < 18.5:
            category = "Underweight"
            color = "blue"
            advice = "Consider healthy weight gain"
        elif bmi < 25:
            category = "Normal"
            color = "green"
            advice = "Maintain current weight"
        elif bmi < 30:
            category = "Overweight"
            color = "orange"
            advice = "Consider healthy weight loss"
        else:
            category = "Obese"
            color = "red"
            advice = "Consult healthcare provider"
        
        st.markdown(f'<p style="color: {color}; font-weight: bold;">{category}</p>', unsafe_allow_html=True)
        st.caption(advice)
    
    with col2:
        # Calculate BMR and daily calories
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
        
        activity_multipliers = {
            'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
            'Very Active': 1.725, 'Extremely Active': 1.9
        }
        
        activity_level = profile.get('activity_level', 'Moderately Active')
        calories = bmr * activity_multipliers.get(activity_level, 1.55)
        
        st.metric("Daily Calories", f"{calories:.0f}")
        st.metric("BMR", f"{bmr:.0f}")
        st.caption(f"Based on {activity_level}")
    
    with col3:
        # Water intake recommendation
        water_intake = weight * 35  # 35ml per kg body weight
        st.metric("Water Target (ml)", f"{water_intake:.0f}")
        
        # Ideal weight range
        ideal_weight_min = 18.5 * (height_m ** 2)
        ideal_weight_max = 24.9 * (height_m ** 2)
        st.metric("Ideal Weight Range", f"{ideal_weight_min:.0f}-{ideal_weight_max:.0f} kg")
    
    with col4:
        # Body fat estimation (rough)
        if gender == 'Male':
            body_fat = (1.20 * bmi) + (0.23 * age) - 16.2
        else:
            body_fat = (1.20 * bmi) + (0.23 * age) - 5.4
        
        body_fat = max(0, body_fat)  # Ensure non-negative
        st.metric("Est. Body Fat %", f"{body_fat:.1f}%")
        
        # Health risk assessment
        if bmi < 18.5 or bmi > 30:
            risk = "High"
            risk_color = "red"
        elif bmi > 25:
            risk = "Moderate"
            risk_color = "orange"
        else:
            risk = "Low"
            risk_color = "green"
        
        st.markdown(f'<p style="color: {risk_color};">Health Risk: {risk}</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Macronutrient recommendations with interactive visualization
    st.subheader("🥗 Personalized Macronutrient Distribution")
    
    health_goals = profile.get('health_goals', [])
    
    # Determine macronutrient ratios based on goals
    if 'Muscle Gain' in health_goals:
        protein_pct = 30
        carb_pct = 40
        fat_pct = 30
        goal_type = "Muscle Gain"
    elif 'Weight Loss' in health_goals:
        protein_pct = 35
        carb_pct = 30
        fat_pct = 35
        goal_type = "Weight Loss"
    elif profile.get('diet_type') == 'Keto':
        protein_pct = 25
        carb_pct = 5
        fat_pct = 70
        goal_type = "Ketogenic Diet"
    else:
        protein_pct = 25
        carb_pct = 45
        fat_pct = 30
        goal_type = "Balanced Diet"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Enhanced pie chart
        fig = px.pie(
            values=[protein_pct, carb_pct, fat_pct],
            names=['Protein', 'Carbohydrates', 'Fats'],
            title=f"Recommended Distribution for {goal_type}",
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1'],
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{percent}<br>%{value}% of calories<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Daily Macronutrient Targets:**")
        
        daily_calories = int(calories)
        protein_cals = (protein_pct / 100) * daily_calories
        carb_cals = (carb_pct / 100) * daily_calories
        fat_cals = (fat_pct / 100) * daily_calories
        
        # Convert to grams (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
        protein_g = protein_cals / 4
        carb_g = carb_cals / 4
        fat_g = fat_cals / 9
        
        st.metric("Protein", f"{protein_g:.0f}g", f"{protein_pct}% of calories")
        st.metric("Carbohydrates", f"{carb_g:.0f}g", f"{carb_pct}% of calories")
        st.metric("Fats", f"{fat_g:.0f}g", f"{fat_pct}% of calories")
        
        st.caption(f"Based on {daily_calories} calories/day")
    
    st.markdown("---")
    
    # Weekly nutrition goal tracking
    st.subheader("📈 Weekly Nutrition Goal Tracking")
    
    # Simulated weekly data (in a real app, this would come from daily logs)
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Generate sample data for demonstration
    import random
    random.seed(42)  # For consistent demo data
    
    weekly_data = {
        'Day': days_of_week,
        'Calories': [random.randint(int(calories*0.8), int(calories*1.2)) for _ in range(7)],
        'Protein (g)': [random.randint(int(protein_g*0.7), int(protein_g*1.3)) for _ in range(7)],
        'Water (ml)': [random.randint(int(water_intake*0.6), int(water_intake*1.4)) for _ in range(7)],
        'Exercise (min)': [random.randint(0, 60) for _ in range(7)]
    }
    
    df_weekly = pd.DataFrame(weekly_data)
    
    # Create subplots for different metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Calorie tracking
        fig_cal = px.bar(
            df_weekly, x='Day', y='Calories',
            title='Weekly Calorie Intake',
            color='Calories',
            color_continuous_scale='RdYlGn'
        )
        fig_cal.add_hline(y=calories, line_dash="dash", line_color="red", annotation_text="Target")
        st.plotly_chart(fig_cal, use_container_width=True)
    
    with col2:
        # Water intake tracking
        fig_water = px.line(
            df_weekly, x='Day', y='Water (ml)',
            title='Weekly Water Intake',
            markers=True
        )
        fig_water.add_hline(y=water_intake, line_dash="dash", line_color="blue", annotation_text="Target")
        st.plotly_chart(fig_water, use_container_width=True)
    
    st.markdown("---")
    
    # Personalized nutrition tips based on comprehensive profile analysis
    st.subheader("💡 Personalized Nutrition Insights")
    
    insights = []
    
    # BMI-based insights
    if bmi < 18.5:
        insights.append("🔼 **Weight Gain Focus**: Include calorie-dense healthy foods like nuts, avocados, and whole grains")
    elif bmi > 25:
        insights.append("🔽 **Weight Management**: Focus on portion control and increase vegetable intake")
    
    # Goal-based insights
    if 'Weight Loss' in health_goals:
        insights.extend([
            "🎯 **Caloric Deficit**: Aim for 300-500 calories below maintenance for sustainable weight loss",
            "🥗 **Protein Priority**: Higher protein intake helps preserve muscle mass during weight loss",
            "🥦 **Fiber Focus**: Include plenty of fiber-rich vegetables for satiety"
        ])
    
    if 'Muscle Gain' in health_goals:
        insights.extend([
            "💪 **Protein Timing**: Distribute protein intake throughout the day, especially post-workout",
            "🍞 **Carb Strategy**: Include carbohydrates around workouts for energy and recovery",
            "🍁 **Healthy Fats**: Don't neglect fats - they're crucial for hormone production"
        ])
    
    # Diet-specific insights
    if profile.get('diet_type') == 'Vegan':
        insights.extend([
            "🌱 **Protein Combining**: Combine different plant proteins for complete amino acid profiles",
            "🔴 **B12 Alert**: Consider B12 supplementation for optimal health",
            "⚡ **Iron + Vitamin C**: Pair iron-rich foods with vitamin C for better absorption"
        ])
    elif profile.get('diet_type') == 'Keto':
        insights.extend([
            "🥑 **Electrolyte Balance**: Monitor sodium, potassium, and magnesium intake",
            "🥒 **Quality Fats**: Focus on healthy fats like olive oil, avocados, and nuts",
            "🥬 **Carb Timing**: Time any carbs around workouts for best results"
        ])
    
    # Age and gender-specific insights
    if age > 50:
        insights.append("🦺 **Bone Health**: Ensure adequate calcium and vitamin D intake")
    
    if gender == 'Female':
        insights.append("🩸 **Iron Awareness**: Monitor iron intake, especially if experiencing heavy menstrual cycles")
    
    # Activity-based insights
    if profile.get('activity_level') in ['Very Active', 'Extremely Active']:
        insights.append("🏃 **Recovery Nutrition**: Focus on post-workout nutrition for optimal recovery")
    
    # Display insights
    for insight in insights:
        st.markdown(insight)
    
    if not insights:
        st.info("💡 Complete more of your profile details to get personalized insights!")
    
    st.markdown("---")
    
    # Meal timing recommendations
    st.subheader("⏰ Optimal Meal Timing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recommended Meal Schedule:**")
        
        if 'Muscle Gain' in health_goals:
            schedule = {
                "7:00 AM": "Breakfast (25% of daily calories)",
                "10:00 AM": "Morning snack (10%)",
                "1:00 PM": "Lunch (30%)",
                "4:00 PM": "Pre-workout snack (10%)",
                "7:00 PM": "Dinner (25%)"
            }
        elif 'Weight Loss' in health_goals:
            schedule = {
                "7:00 AM": "Breakfast (30% of daily calories)",
                "12:00 PM": "Lunch (35%)",
                "3:00 PM": "Healthy snack (15%)",
                "6:30 PM": "Light dinner (20%)"
            }
        else:
            schedule = {
                "7:30 AM": "Breakfast (25% of daily calories)",
                "12:30 PM": "Lunch (35%)",
                "3:30 PM": "Afternoon snack (15%)",
                "7:00 PM": "Dinner (25%)"
            }
        
        for time, meal in schedule.items():
            st.write(f"**{time}**: {meal}")
    
    with col2:
        st.write("**Hydration Schedule:**")
        
        hydration_schedule = {
            "Upon waking": "1-2 glasses (start hydrated)",
            "Before meals": "1 glass (30 min before)",
            "During exercise": "Small sips every 15-20 min",
            "Before bed": "1 glass (1 hour before sleep)"
        }
        
        for time, amount in hydration_schedule.items():
            st.write(f"**{time}**: {amount}")
    
    st.markdown("---")
    
    # Progress prediction
    st.subheader("🔮 Progress Prediction")
    
    if 'Weight Loss' in health_goals:
        # Safe weight loss calculation
        weekly_loss = 0.5  # kg per week (safe rate)
        weeks_to_goal = 8  # example timeline
        predicted_weight = weight - (weekly_loss * weeks_to_goal)
        
        st.success(f"🎯 At a safe rate of {weekly_loss}kg/week, you could reach {predicted_weight:.1f}kg in {weeks_to_goal} weeks")
        
    elif 'Muscle Gain' in health_goals:
        # Muscle gain calculation
        monthly_gain = 0.5  # kg per month (realistic for muscle)
        months_to_goal = 6  # example timeline
        predicted_muscle = monthly_gain * months_to_goal
        
        st.success(f"💪 With consistent training and nutrition, you could gain approximately {predicted_muscle:.1f}kg of muscle in {months_to_goal} months")
    
    st.caption("⚠️ Predictions are estimates based on general guidelines. Individual results may vary.")

def show_settings():
    """Show settings page"""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    # Account settings
    st.subheader("👤 Account Settings")
    
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**User ID:** {st.session_state.user_id}")
    
    # Profile management
    st.subheader("📝 Profile Management")
    
    if st.button("Edit Profile"):
        # This would redirect to profile setup
        st.info("Redirecting to profile setup...")
    
    if st.button("Export Profile Data"):
        if st.session_state.user_profile:
            profile_json = json.dumps(st.session_state.user_profile, indent=2)
            st.download_button(
                label="Download Profile Data",
                data=profile_json,
                file_name=f"profile_{st.session_state.username}.json",
                mime="application/json"
            )
        else:
            st.warning("No profile data to export")
    
    # Data management
    st.subheader("📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear Chat History", type="secondary"):
            st.session_state.chat_history = []
            st.success("Chat history cleared")
    
    with col2:
        if st.button("Reset All Data", type="secondary"):
            # This would require confirmation
            st.warning("This action cannot be undone!")
    
    # App information
    st.subheader("ℹ️ About")
    
    st.markdown("""
    **Nutrition Assistant v1.0**
    
    This application uses advanced NLP techniques to provide personalized nutrition guidance:
    - **spaCy** for ingredient extraction and entity recognition
    - **NLTK & TextBlob** for text processing and sentiment analysis
    - **Sentence Transformers** for semantic similarity
    - **Scikit-learn** for classification and clustering
    - **Transformers** for advanced language understanding
    
    **Features:**
    - Real-time meal analysis
    - Personalized meal planning
    - Intelligent nutrition chatbot
    - Comprehensive analytics
    
    **Data Sources:**
    - Spoonacular API for recipes
    - Nutritionix API for nutrition data
    - Custom nutrition knowledge base
    """)
    
    # API status
    st.subheader("🔌 API Status")
    
    api_status = {
        "Spoonacular API": "✅ Connected" if meal_planner.spoonacular_api_key else "❌ Not configured",
        "Nutritionix API": "✅ Connected" if nlp_analyzer.nutritionix_headers.get('x-app-id') else "❌ Not configured",
        "Local NLP Models": "✅ Loaded"
    }
    
    for api, status in api_status.items():
        st.write(f"**{api}:** {status}")

def show_daily_tracker():
    """Show daily nutrition and activity tracker"""
    st.markdown('<h1 class="main-header">📱 Daily Tracker</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Please complete your profile first!")
        return
    
    # Date selection
    selected_date = st.date_input("Select Date", value=st.session_state.selected_date)
    st.session_state.selected_date = selected_date
    
    # Get today's date for comparison
    today = datetime.now().date()  # Define today for scope access
    
    # Calculate daily targets
    profile = st.session_state.user_profile
    height_m = profile.get('height', 170) / 100
    weight = profile.get('weight', 70)
    age = profile.get('age', 25)
    gender = profile.get('gender', 'Male')
    
    # Calculate BMR and daily calories
    if gender == 'Male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
    
    activity_multipliers = {
        'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
        'Very Active': 1.725, 'Extremely Active': 1.9
    }
    
    daily_calories_target = int(bmr * activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55))
    daily_water_target = int(weight * 35)  # 35ml per kg
    daily_exercise_target = 30  # 30 minutes
    
    # Food logging
    st.subheader("🍽️ Food Log")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Quick Add:**")
        
        common_foods = {
            "Apple 🍎": 95,
            "Banana 🍌": 105,
            "Orange 🍊": 62,
            "Boiled Egg 🥚": 70,
            "Bread Slice 🍞": 80,
            "Rice Bowl 🍚": 200,
            "Chicken Breast 🍗": 165,
            "Salad 🥗": 50
        }
        
        selected_food = st.selectbox("Select food:", list(common_foods.keys()))
        
        if st.button("Add Food", use_container_width=True):
            calories_to_add = common_foods[selected_food]
            if selected_date == today:
                st.session_state.daily_calories += calories_to_add
                
                # Save to database immediately
                log_data = {
                    'date': selected_date,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Added {selected_food} at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if not result.get('success', True):
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
            st.success(f"Added {selected_food} ({calories_to_add} cal)")
    
    with col2:
        st.write("**Custom Entry:**")
        
        with st.form("custom_food_form"):
            food_name = st.text_input("Food name")
            food_calories = st.number_input("Calories", min_value=0, max_value=2000, value=100)
            
            if st.form_submit_button("Add Custom Food"):
                if food_name:
                    if selected_date == today:
                        st.session_state.daily_calories += food_calories
                        
                        # Save to database immediately
                        log_data = {
                            'date': selected_date,
                            'calories': st.session_state.daily_calories,
                            'water': st.session_state.daily_water,
                            'exercise': st.session_state.daily_exercise,
                            'notes': f"Added custom food {food_name} at {datetime.now().strftime('%H:%M')}"
                        }
                        try:
                            result = db.save_daily_log(st.session_state.user_id, log_data)
                            if not result.get('success', True):
                                st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"❌ Error saving log: {str(e)}")
                            
                    st.success(f"Added {food_name} ({food_calories} cal)")
    
    st.markdown("---")
    
    # Activity logging
    st.subheader("🏃 Activity Log")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Quick Activities:**")
        
        activities = {
            "Walking (15 min)": 15,
            "Running (20 min)": 20,
            "Cycling (30 min)": 30,
            "Swimming (25 min)": 25,
            "Yoga (45 min)": 45,
            "Weight training (30 min)": 30
        }
        
        selected_activity = st.selectbox("Select activity:", list(activities.keys()))
        
        if st.button("Log Activity", use_container_width=True):
            minutes_to_add = activities[selected_activity]
            if selected_date == today:
                st.session_state.daily_exercise += minutes_to_add
                
                # Save to database immediately
                log_data = {
                    'date': selected_date,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Logged activity {selected_activity} at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if not result.get('success', True):
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
            st.success(f"Logged {selected_activity}")
    
    with col2:
        st.write("**Water Intake:**")
        
        water_amounts = ["250ml (1 glass)", "500ml (bottle)", "750ml (large bottle)", "1000ml (1 liter)"]
        selected_water = st.selectbox("Add water:", water_amounts)
        
        if st.button("Add Water", use_container_width=True):
            water_ml = int(selected_water.split('ml')[0].replace('(', '').strip())
            if selected_date == today:
                st.session_state.daily_water += water_ml
                
                # Save to database immediately
                log_data = {
                    'date': selected_date,
                    'calories': st.session_state.daily_calories,
                    'water': st.session_state.daily_water,
                    'exercise': st.session_state.daily_exercise,
                    'notes': f"Added water {selected_water} at {datetime.now().strftime('%H:%M')}"
                }
                try:
                    result = db.save_daily_log(st.session_state.user_id, log_data)
                    if not result.get('success', True):
                        st.error(f"❌ Error saving: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error saving log: {str(e)}")
                    
            st.success(f"Added {selected_water}")
    
    st.markdown("---")
    
    # Current day summary
    if selected_date == today:
        st.subheader("📈 Today's Progress")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            calories_progress = min(st.session_state.daily_calories / daily_calories_target * 100, 100)
            st.metric(
                "Calories", 
                f"{st.session_state.daily_calories}/{daily_calories_target}",
                f"{calories_progress:.1f}% of target"
            )
            st.progress(calories_progress / 100)
        
        with col2:
            water_progress = min(st.session_state.daily_water / daily_water_target * 100, 100)
            st.metric(
                "Water (ml)", 
                f"{st.session_state.daily_water}/{daily_water_target}",
                f"{water_progress:.1f}% of target"
            )
            st.progress(water_progress / 100)
        
        with col3:
            exercise_progress = min(st.session_state.daily_exercise / daily_exercise_target * 100, 100)
            st.metric(
                "Exercise (min)", 
                f"{st.session_state.daily_exercise}/{daily_exercise_target}",
                f"{exercise_progress:.1f}% of target"
            )
            st.progress(exercise_progress / 100)
        
        # Save button
        if st.button("💾 Save Today's Complete Log", use_container_width=True):
            log_data = {
                'date': selected_date,
                'calories': st.session_state.daily_calories,
                'water': st.session_state.daily_water,
                'exercise': st.session_state.daily_exercise,
                'notes': f"Manual save on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
            try:
                result = db.save_daily_log(st.session_state.user_id, log_data)
                if result.get('success', True):
                    st.success("✅ Daily log saved successfully!")
                else:
                    st.error(f"❌ Error saving log: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Error saving log: {str(e)}")
            st.info("📅 No data available for the selected period. Start logging your daily activities!")
            return
    
    # Get daily logs for the selected period (last 7 days)
    try:
        daily_logs = db.get_daily_logs(st.session_state.user_id, 7)
        
        if not daily_logs:
            st.info("📅 No data available for the selected period. Start logging your daily activities!")
            return
    except Exception as e:
        st.error(f"❌ Error fetching daily logs: {str(e)}")
        return
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(daily_logs)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Summary statistics
    st.subheader("📆 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_calories = df['calories'].mean()
        st.metric("Avg Daily Calories", f"{avg_calories:.0f} kcal")
    
    with col2:
        avg_water = df['water'].mean()
        st.metric("Avg Daily Water", f"{avg_water:.0f} ml")
    
    with col3:
        avg_exercise = df['exercise'].mean()
        st.metric("Avg Daily Exercise", f"{avg_exercise:.0f} min")
    
    with col4:
        total_days = len(df)
        st.metric("Days Logged", f"{total_days}")
    
    st.markdown("---")
    
    st.subheader("📈 Calorie Trend")
    
    profile = st.session_state.user_profile
    height_m = profile.get('height', 170) / 100
    weight = profile.get('weight', 70)
    age = profile.get('age', 25)
    gender = profile.get('gender', 'Male')
    
    # Calculate daily calorie target
    if gender == 'Male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
    
    activity_multipliers = {
        'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
        'Very Active': 1.725, 'Extremely Active': 1.9
    }
    
    daily_target = bmr * activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55)
    
    fig_calories = px.line(
        df, x='date', y='calories',
        title='Daily Calorie Intake',
        labels={'calories': 'Calories (kcal)', 'date': 'Date'}
    )
    
    # Add target line
    fig_calories.add_hline(
        y=daily_target, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Target: {daily_target:.0f} kcal"
    )
    
    st.plotly_chart(fig_calories, use_container_width=True)
        
    # Water and exercise charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💧 Water Intake Trend")
        
        water_target = weight * 35
        
        fig_water = px.bar(
            df, x='date', y='water',
            title='Daily Water Intake',
            labels={'water': 'Water (ml)', 'date': 'Date'}
        )
        
        fig_water.add_hline(
            y=water_target, 
            line_dash="dash", 
            line_color="blue",
            annotation_text=f"Target: {water_target:.0f} ml"
        )
        
        st.plotly_chart(fig_water, use_container_width=True)
    
    with col2:
        st.subheader("🏃 Exercise Trend")
        
        fig_exercise = px.bar(
            df, x='date', y='exercise',
            title='Daily Exercise Minutes',
            labels={'exercise': 'Exercise (min)', 'date': 'Date'},
            color='exercise',
            color_continuous_scale='Viridis'
        )
        
        fig_exercise.add_hline(
            y=30, 
            line_dash="dash", 
            line_color="green",
            annotation_text="Target: 30 min"
        )
        
        st.plotly_chart(fig_exercise, use_container_width=True)
        
        # Weekly comparison
        st.subheader("📅 Weekly Comparison")
        
        if len(df) >= 14:  # At least 2 weeks of data
            df['week'] = df['date'].dt.isocalendar().week
            weekly_stats = df.groupby('week').agg({
                'calories': 'mean',
                'water': 'mean',
                'exercise': 'mean'
            }).round(0)
            
            st.dataframe(weekly_stats)
        else:
            st.info("Need at least 2 weeks of data for weekly comparison")

def show_progress_reports():
    """Show progress reports and analytics"""
    st.markdown('<h1 class="main-header">📈 Progress Reports</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Please complete your profile first!")
        return
    
    # Time period selection
    period = st.selectbox("Select time period:", ["Last 7 days", "Last 30 days", "Last 90 days"])
    days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}[period]
    
    try:
        # Get daily logs
        daily_logs = db.get_daily_logs(st.session_state.user_id, days)
        
        if not daily_logs:
            st.info("📅 No data available for the selected period. Start logging your daily activities!")
            return
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(daily_logs)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Summary statistics
        st.subheader("📆 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_calories = df['calories'].mean()
            st.metric("Avg Daily Calories", f"{avg_calories:.0f} kcal")
        
        with col2:
            avg_water = df['water'].mean()
            st.metric("Avg Daily Water", f"{avg_water:.0f} ml")
        
        with col3:
            avg_exercise = df['exercise'].mean()
            st.metric("Avg Daily Exercise", f"{avg_exercise:.0f} min")
        
        with col4:
            total_days = len(df)
            st.metric("Days Logged", f"{total_days}")
        
        st.markdown("---")
    
        st.subheader("📈 Calorie Trend")
        
        profile = st.session_state.user_profile
        height_m = profile.get('height', 170) / 100
        weight = profile.get('weight', 70)
        age = profile.get('age', 25)
        gender = profile.get('gender', 'Male')
        
        # Calculate daily calorie target
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
        
        activity_multipliers = {
            'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
            'Very Active': 1.725, 'Extremely Active': 1.9
        }
        
        daily_target = bmr * activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55)
        
        fig_calories = px.line(
            df, x='date', y='calories',
            title='Daily Calorie Intake',
            labels={'calories': 'Calories (kcal)', 'date': 'Date'}
        )
        
        # Add target line
        fig_calories.add_hline(
            y=daily_target, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Target: {daily_target:.0f} kcal"
        )
        
        st.plotly_chart(fig_calories, use_container_width=True)
        
        # Water and exercise charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💧 Water Intake Trend")
            
            water_target = weight * 35
            
            fig_water = px.bar(
                df, x='date', y='water',
                title='Daily Water Intake',
                labels={'water': 'Water (ml)', 'date': 'Date'}
            )
            
            fig_water.add_hline(
                y=water_target, 
                line_dash="dash", 
                line_color="blue",
                annotation_text=f"Target: {water_target:.0f} ml"
            )
            
            st.plotly_chart(fig_water, use_container_width=True)
        
        with col2:
            st.subheader("🏃 Exercise Trend")
            
            fig_exercise = px.bar(
                df, x='date', y='exercise',
                title='Daily Exercise Minutes',
                labels={'exercise': 'Exercise (min)', 'date': 'Date'},
                color='exercise',
                color_continuous_scale='Viridis'
            )
            
            fig_exercise.add_hline(
                y=30, 
                line_dash="dash", 
                line_color="green",
                annotation_text="Target: 30 min"
            )
            
            st.plotly_chart(fig_exercise, use_container_width=True)
        
        # Weekly comparison
        st.subheader("📅 Weekly Comparison")
        
        if len(df) >= 14:  # At least 2 weeks of data
            df['week'] = df['date'].dt.isocalendar().week
            weekly_stats = df.groupby('week').agg({
                'calories': 'mean',
                'water': 'mean',
                'exercise': 'mean'
            }).round(0)
            
            st.dataframe(weekly_stats)
        else:
            st.info("Need at least 2 weeks of data for weekly comparison")
            
        # Goal achievement rate
        st.subheader("🎯 Goal Achievement Rate")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            calorie_achievement = (df['calories'] >= daily_target * 0.8).sum() / len(df) * 100
            st.metric("Calorie Goal Achievement", f"{calorie_achievement:.1f}%")
        
        with col2:
            water_achievement = (df['water'] >= water_target * 0.8).sum() / len(df) * 100
            st.metric("Water Goal Achievement", f"{water_achievement:.1f}%")
        
        with col3:
            exercise_achievement = (df['exercise'] >= 30).sum() / len(df) * 100
            st.metric("Exercise Goal Achievement", f"{exercise_achievement:.1f}%")
    
    except Exception as e:
        st.error(f"Error loading progress data: {str(e)}")
        st.info("Start using the Daily Tracker to see your progress reports!")

def show_goal_setting():
    """Show goal setting and management"""
    st.markdown('<h1 class="main-header">🎯 Goal Setting</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Please complete your profile first!")
        return
    
    st.info("💡 Set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound) for better results!")
    
    # Current profile goals
    profile = st.session_state.user_profile
    current_goals = profile.get('health_goals', [])
    
    st.subheader("🏆 Current Health Goals")
    
    if current_goals:
        for goal in current_goals:
            st.success(f"✅ {goal}")
    else:
        st.info("No health goals set yet. Let's add some!")
    
    st.markdown("---")
    
    # Goal recommendations based on BMI
    height_m = profile.get('height', 170) / 100
    weight = profile.get('weight', 70)
    bmi = weight / (height_m ** 2)
    
    st.subheader("💡 Recommended Goals Based on Your Profile")
    
    recommended_goals = []
    
    if bmi < 18.5:
        recommended_goals.extend([
            "Healthy Weight Gain",
            "Increase Muscle Mass",
            "Improve Appetite"
        ])
    elif bmi > 25:
        recommended_goals.extend([
            "Healthy Weight Loss",
            "Increase Physical Activity",
            "Improve Cardiovascular Health"
        ])
    else:
        recommended_goals.extend([
            "Maintain Current Weight",
            "Build Lean Muscle",
            "Improve Overall Fitness"
        ])
    
    # Always recommend these
    recommended_goals.extend([
        "Drink More Water",
        "Eat More Vegetables",
        "Regular Exercise Routine",
        "Better Sleep Habits"
    ])
    
    for goal in recommended_goals:
        if goal not in current_goals:
            st.info(f"💡 Consider: {goal}")
    
    st.markdown("---")
    
    # SMART Goal Creator
    st.subheader("🎯 Create New SMART Goals")
    
    with st.form("goal_form"):
        goal_category = st.selectbox(
            "Goal Category:",
            ["Weight Management", "Exercise & Fitness", "Nutrition & Diet", "Wellness & Lifestyle"]
        )
        
        goal_description = st.text_area(
            "Describe your goal (be specific):",
            placeholder="e.g., Lose 5kg in 3 months through balanced diet and exercise"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_value = st.number_input("Target Value (if applicable):", min_value=0.0, value=0.0)
            target_unit = st.selectbox("Unit:", ["kg", "minutes/day", "glasses/day", "times/week", "other"])
        
        with col2:
            target_date = st.date_input("Target Date:", value=datetime.now().date() + timedelta(days=30))
            priority = st.selectbox("Priority:", ["High", "Medium", "Low"])
        
        if st.form_submit_button("Add Goal", use_container_width=True):
            if goal_description:
                # Here you would save the goal to database
                st.success(f"✅ Goal added: {goal_description}")
                st.balloons()
            else:
                st.error("Please describe your goal")
    
    st.markdown("---")
    
    # Goal tracking tips
    st.subheader("📈 Goal Achievement Tips")
    
    tips = [
        "📅 **Track Daily**: Use the Daily Tracker to monitor progress",
        "🎯 **Start Small**: Begin with achievable mini-goals",
        "📈 **Monitor Progress**: Review your Progress Reports weekly",
        "🎆 **Celebrate Wins**: Acknowledge every achievement, no matter how small",
        "🔄 **Adjust as Needed**: Modify goals based on your progress and circumstances",
        "👥 **Get Support**: Share your goals with friends and family",
        "📝 **Write It Down**: Document your why and motivation",
        "⏰ **Be Patient**: Sustainable changes take time"
    ]
    
    for tip in tips:
        st.markdown(tip)
    
    # Goal examples
    st.markdown("---")
    st.subheader("📝 Example SMART Goals")
    
    examples = {
        "Weight Loss": "Lose 2kg in 8 weeks by eating 1800 calories per day and exercising 4 times per week",
        "Fitness": "Exercise for 30 minutes, 5 days per week for the next 2 months",
        "Nutrition": "Eat 5 servings of fruits and vegetables daily for the next month",
        "Hydration": "Drink 8 glasses of water every day for the next 30 days",
        "Sleep": "Get 7-8 hours of sleep every night for the next 6 weeks"
    }
    
    for category, example in examples.items():
        with st.expander(f"{category} Goal Example"):
            st.write(example)

if __name__ == "__main__":
    main()