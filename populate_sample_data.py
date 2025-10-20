import sqlite3
import random
from datetime import datetime, timedelta

# Connect to the database
conn = sqlite3.connect('nutrition_app.db')
cursor = conn.cursor()

# User ID to populate data for
user_id = 1

# Date range: October 1 to October 17, 2025
start_date = datetime(2025, 10, 1).date()
end_date = datetime(2025, 10, 17).date()

# Generate data for each day
current_date = start_date
while current_date <= end_date:
    # Generate realistic nutrition data with some variation
    # Base values
    base_calories = random.randint(1800, 2500)
    base_protein = random.randint(80, 150)
    base_carbs = random.randint(150, 300)
    base_fat = random.randint(50, 120)
    base_water = random.randint(1500, 3000)
    base_exercise = random.randint(0, 90)
    
    # Add some daily variation
    variation = random.uniform(0.8, 1.2)
    calories = int(base_calories * variation)
    protein = round(base_protein * variation, 1)
    carbs = round(base_carbs * variation, 1)
    fat = round(base_fat * variation, 1)
    water = int(base_water * variation)
    exercise = int(base_exercise * variation)
    
    # Weekend variation (people tend to eat more and exercise less on weekends)
    if current_date.weekday() >= 5:  # Saturday or Sunday
        calories = int(calories * 1.1)
        exercise = int(exercise * 0.7)
    
    # Random notes
    notes_options = [
        "Good day!",
        "Felt energetic",
        "Had a cheat meal",
        "Workout day",
        "Rest day",
        "Busy day",
        "Stressful day",
        ""
    ]
    notes = random.choice(notes_options)
    
    # Insert or update the daily log
    cursor.execute('''
        INSERT OR REPLACE INTO daily_logs 
        (user_id, log_date, calories_consumed, protein_grams, carbs_grams, 
         fat_grams, water_ml, exercise_minutes, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        current_date,
        calories,
        protein,
        carbs,
        fat,
        water,
        exercise,
        notes
    ))
    
    print(f"Added data for {current_date}: {calories} calories, {water}ml water, {exercise}min exercise")
    
    # Move to next day
    current_date += timedelta(days=1)

# Commit changes and close connection
conn.commit()
conn.close()

print(f"\nSuccessfully populated data from {start_date} to {end_date} for user_id {user_id}")