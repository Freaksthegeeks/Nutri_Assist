import sqlite3
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    print("Warning: bcrypt not available. Using simple hash instead.")
    import hashlib
    BCRYPT_AVAILABLE = False

import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self, db_path="nutrition_app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User profiles table
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
        
        # Meal logs table
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
        
        # Meal plans table
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
        
        # Daily logs table
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
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, log_date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, username, email, password):
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hash password
            if BCRYPT_AVAILABLE:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            else:
                # Fallback to simple hash (not recommended for production)
                password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')
            
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
        """Authenticate user login"""
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
                if BCRYPT_AVAILABLE:
                    if bcrypt.checkpw(password.encode('utf-8'), user[2]):
                        return {"success": True, "user_id": user[0], "username": user[1]}
                else:
                    # Fallback hash check
                    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')
                    if password_hash == user[2]:
                        return {"success": True, "user_id": user[0], "username": user[1]}
                
            return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_user_profile(self, user_id, profile_data):
        """Save or update user profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if profile exists
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
        """Get user profile data"""
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
        """Save meal analysis log"""
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
        """Save generated meal plan"""
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
    
    def get_recent_meal_plans(self, user_id, limit=5):
        """Get recent meal plans for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT plan_data, week_start_date, created_at
                FROM meal_plans WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
            
            plans = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "plan_data": json.loads(plan[0]),
                    "week_start_date": plan[1],
                    "created_at": plan[2]
                }
                for plan in plans
            ]
        except Exception as e:
            print(f"Error getting meal plans: {e}")
            return []
    
    def save_daily_log(self, user_id, log_data):
        """Save or update daily log entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            log_date = log_data.get('date', datetime.now().date())
            
            # First, try to update existing record
            cursor.execute('''
                UPDATE daily_logs SET
                calories_consumed = ?,
                protein_grams = ?,
                carbs_grams = ?,
                fat_grams = ?,
                water_ml = ?,
                exercise_minutes = ?,
                notes = ?
                WHERE user_id = ? AND log_date = ?
            ''', (
                log_data.get('calories', 0),
                log_data.get('protein', 0),
                log_data.get('carbs', 0),
                log_data.get('fat', 0),
                log_data.get('water', 0),
                log_data.get('exercise', 0),
                log_data.get('notes', ''),
                user_id,
                log_date
            ))
            
            # If no rows were updated, insert a new record
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO daily_logs 
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
        """Get daily logs for user"""
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
