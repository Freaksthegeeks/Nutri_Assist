import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sqlite3
import hashlib

# Simplified database manager without external dependencies
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

# Simple meal analyzer without complex NLP
class SimpleMealAnalyzer:
    def __init__(self):
        self.food_groups = {
            'proteins': ['chicken', 'beef', 'fish', 'salmon', 'tuna', 'eggs', 'tofu', 'beans', 'lentils'],
            'carbs': ['rice', 'pasta', 'bread', 'potato', 'oats', 'quinoa'],
            'vegetables': ['broccoli', 'spinach', 'carrot', 'tomato', 'onion', 'pepper'],
            'fruits': ['apple', 'banana', 'orange', 'berry', 'avocado'],
            'dairy': ['milk', 'cheese', 'yogurt'],
            'fats': ['oil', 'nuts', 'seeds', 'avocado']
        }
    
    def extract_ingredients(self, text):
        ingredients = []
        text_lower = text.lower()
        
        for category, items in self.food_groups.items():
            for item in items:
                if item in text_lower:
                    ingredients.append(item)
        
        return list(set(ingredients))
    
    def analyze_meal(self, ingredients, user_profile=None):
        categorized = {category: [] for category in self.food_groups.keys()}
        
        for ingredient in ingredients:
            for category, items in self.food_groups.items():
                if ingredient in items:
                    categorized[category].append(ingredient)
        
        score = 0
        food_groups_present = len([cat for cat, items in categorized.items() if items])
        
        if food_groups_present >= 3:
            score += 30
        if categorized['proteins']:
            score += 25
        if categorized['vegetables']:
            score += 25
        if categorized['fruits']:
            score += 20
        
        recommendations = []
        if not categorized['proteins']:
            recommendations.append("Add a protein source for better nutrition")
        if not categorized['vegetables']:
            recommendations.append("Include vegetables for vitamins and minerals")
        
        return {
            'nutrition_score': min(score, 100),
            'category_analysis': categorized,
            'recommendations': recommendations,
            'ingredients': ingredients
        }

# Page configuration
st.set_page_config(
    page_title="Nutrition Assistant",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    db = SimpleDatabaseManager()
    analyzer = SimpleMealAnalyzer()
    return db, analyzer

db, analyzer = init_components()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None

def main():
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
    </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_id is None:
        show_auth_page()
    else:
        show_dashboard()

def show_auth_page():
    st.markdown('<h1 class="main-header">🥗 Nutrition Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #666;">Your AI-Powered Nutrition Companion</h3>', 
                unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()
    
    # App features preview
    st.markdown("---")
    st.markdown("### 🌟 Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 Meal Analysis</h4>
            <p>Get instant nutritional analysis of your meals</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Nutrition Tracking</h4>
            <p>Track your daily nutrition and health goals</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>💡 Smart Recommendations</h4>
            <p>Get personalized nutrition advice</p>
        </div>
        """, unsafe_allow_html=True)

def show_login_form():
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
                    
                    profile = db.get_user_profile(result['user_id'])
                    st.session_state.user_profile = profile
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result['error'])
            else:
                st.error("Please fill in all fields")

def show_register_form():
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
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}! 👋")
        
        menu_options = [
            "🏠 Dashboard",
            "👤 Profile Setup",
            "🍽️ Meal Analysis",
            "📊 Nutrition Tracker",
            "⚙️ Settings"
        ]
        
        selected_option = st.selectbox("Navigation", menu_options)
        
        st.markdown("---")
        if st.button("Logout"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    # Main content
    if selected_option == "🏠 Dashboard":
        show_home_dashboard()
    elif selected_option == "👤 Profile Setup":
        show_profile_setup()
    elif selected_option == "🍽️ Meal Analysis":
        show_meal_analysis()
    elif selected_option == "📊 Nutrition Tracker":
        show_nutrition_tracker()
    elif selected_option == "⚙️ Settings":
        show_settings()

def show_home_dashboard():
    st.markdown('<h1 class="main-header">🏠 Nutrition Dashboard</h1>', unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯</h3>
            <h4>Profile Status</h4>
            <p>{}</p>
        </div>
        """.format("Complete" if st.session_state.user_profile else "Incomplete"), 
        unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🍽️</h3>
            <h4>Meals Analyzed</h4>
            <p>Ready to Start</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊</h3>
            <h4>Health Score</h4>
            <p>-</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯</h3>
            <h4>Goals</h4>
            <p>Set Goals</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🍽️ Analyze a Meal", use_container_width=True):
            st.info("Click 'Meal Analysis' in the sidebar!")
    
    with col2:
        if st.button("👤 Complete Profile", use_container_width=True):
            st.info("Click 'Profile Setup' in the sidebar!")
    
    with col3:
        if st.button("📊 View Nutrition", use_container_width=True):
            st.info("Click 'Nutrition Tracker' in the sidebar!")

def show_profile_setup():
    st.markdown('<h1 class="main-header">👤 Profile Setup</h1>', unsafe_allow_html=True)
    
    existing_profile = st.session_state.user_profile or {}
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Information")
            age = st.number_input("Age", min_value=10, max_value=120, 
                                value=existing_profile.get('age', 25))
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                index=["Male", "Female", "Other"].index(existing_profile.get('gender', 'Male')))
            height = st.number_input("Height (cm)", min_value=100, max_value=250, 
                                   value=existing_profile.get('height', 170))
            weight = st.number_input("Weight (kg)", min_value=30, max_value=300, 
                                   value=existing_profile.get('weight', 70))
        
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
            ["Weight Loss", "Muscle Gain", "Balanced Diet", "Energy Boost", "Better Digestion"],
            default=existing_profile.get('health_goals', [])
        )
        
        st.subheader("Allergies & Restrictions")
        allergens = st.multiselect(
            "Select any allergens or dietary restrictions:",
            ["Nuts", "Dairy", "Gluten", "Shellfish", "Eggs", "Soy"],
            default=existing_profile.get('allergens', [])
        )
        
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
    st.markdown('<h1 class="main-header">🍽️ Meal Analysis</h1>', unsafe_allow_html=True)
    
    st.info("📝 Enter your meal details to get instant nutritional analysis!")
    
    meal_name = st.text_input("Meal Name", placeholder="e.g., Grilled Chicken Salad")
    
    meal_description = st.text_area(
        "Describe your meal or list ingredients:",
        placeholder="e.g., Grilled chicken breast, mixed greens, cherry tomatoes, cucumber, olive oil",
        height=100
    )
    
    if st.button("🔍 Analyze Meal", use_container_width=True):
        if meal_description:
            with st.spinner("Analyzing your meal..."):
                ingredients = analyzer.extract_ingredients(meal_description)
                analysis = analyzer.analyze_meal(ingredients, st.session_state.user_profile)
                
                st.markdown("---")
                st.subheader("📊 Analysis Results")
                
                # Nutrition score
                score = analysis['nutrition_score']
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Nutrition Score", f"{score}/100")
                with col2:
                    st.metric("Ingredients Found", len(ingredients))
                with col3:
                    food_groups = len([cat for cat, items in analysis['category_analysis'].items() if items])
                    st.metric("Food Groups", food_groups)
                
                # Detailed analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🥗 Food Groups")
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
        else:
            st.error("Please describe your meal")

def show_nutrition_tracker():
    st.markdown('<h1 class="main-header">📊 Nutrition Tracker</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Please complete your profile first to see personalized nutrition tracking!")
        return
    
    profile = st.session_state.user_profile
    height_m = profile.get('height', 170) / 100
    weight = profile.get('weight', 70)
    bmi = weight / (height_m ** 2)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current BMI", f"{bmi:.1f}")
    with col2:
        age = profile.get('age', 25)
        gender = profile.get('gender', 'Male')
        
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * profile.get('height', 170)) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * profile.get('height', 170)) - (4.330 * age)
        
        st.metric("Daily Calories", f"{bmr:.0f}")
    with col3:
        water_intake = weight * 35
        st.metric("Water Intake (ml)", f"{water_intake:.0f}")
    
    # Nutrition goals visualization
    st.subheader("🎯 Nutrition Goals")
    
    health_goals = profile.get('health_goals', [])
    
    if 'Muscle Gain' in health_goals:
        protein_pct, carb_pct, fat_pct = 30, 40, 30
    elif 'Weight Loss' in health_goals:
        protein_pct, carb_pct, fat_pct = 35, 30, 35
    else:
        protein_pct, carb_pct, fat_pct = 25, 45, 30
    
    fig = px.pie(
        values=[protein_pct, carb_pct, fat_pct],
        names=['Protein', 'Carbohydrates', 'Fats'],
        title="Recommended Macronutrient Distribution"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_settings():
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    st.subheader("👤 Account Information")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**User ID:** {st.session_state.user_id}")
    
    if st.session_state.user_profile:
        st.subheader("📊 Profile Data")
        profile_json = json.dumps(st.session_state.user_profile, indent=2)
        st.download_button(
            label="📄 Download Profile Data",
            data=profile_json,
            file_name=f"profile_{st.session_state.username}.json",
            mime="application/json"
        )
    
    st.subheader("ℹ️ About")
    st.markdown("""
    **Nutrition Assistant v1.0 (Simplified)**
    
    This is a streamlined version of the nutrition assistant that works without complex dependencies.
    
    **Features:**
    - User authentication and profiles
    - Basic meal analysis
    - Nutrition tracking
    - Health goal setting
    
    **Note:** This version uses simplified algorithms. For advanced NLP features, 
    install the full requirements.txt dependencies.
    """)

if __name__ == "__main__":
    main()