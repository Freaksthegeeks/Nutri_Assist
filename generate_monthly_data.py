import sqlite3
import random
from datetime import datetime, timedelta

def generate_monthly_data():
    """Generate one month of sample data with specified distribution"""
    
    # Connect to the database
    conn = sqlite3.connect('nutrition_app.db')
    cursor = conn.cursor()

    # User ID to populate data for
    user_id = 1

    # Date range: September 17 to October 17, 2025
    start_date = datetime(2025, 9, 17).date()
    end_date = datetime(2025, 10, 17).date()

    # Define target values for a typical user profile
    # These represent ideal daily goals
    TARGET_CALORIES = 2200
    TARGET_WATER = 2500  # ml
    TARGET_EXERCISE = 45  # minutes
    TARGET_PROTEIN = 120  # grams
    TARGET_CARBS = 250   # grams
    TARGET_FAT = 80      # grams

    print(f"Generating data from {start_date} to {end_date}")
    print(f"Target values: {TARGET_CALORIES} calories, {TARGET_WATER}ml water, {TARGET_EXERCISE}min exercise")

    # Generate data for each day
    current_date = start_date
    total_days = (end_date - start_date).days + 1
    completed_days = 0
    incomplete_days = 0
    remaining_days = 0

    while current_date <= end_date:
        # Determine if this day should meet goals (80%), be incomplete (15%), or remaining (5%)
        rand = random.random()
        
        if rand < 0.80:  # 80% - Complete goals
            # Generate values that meet or exceed targets
            calories = int(TARGET_CALORIES * random.uniform(0.95, 1.15))  # 95-115% of target
            water = int(TARGET_WATER * random.uniform(0.9, 1.2))          # 90-120% of target
            exercise = int(TARGET_EXERCISE * random.uniform(0.9, 1.3))    # 90-130% of target
            protein = round(TARGET_PROTEIN * random.uniform(0.9, 1.2), 1)
            carbs = round(TARGET_CARBS * random.uniform(0.85, 1.15), 1)
            fat = round(TARGET_FAT * random.uniform(0.8, 1.2), 1)
            completed_days += 1
            status = "Completed"
        elif rand < 0.95:  # 15% - Incomplete goals
            # Generate values that fall short of targets
            calories = int(TARGET_CALORIES * random.uniform(0.6, 0.9))    # 60-90% of target
            water = int(TARGET_WATER * random.uniform(0.5, 0.85))         # 50-85% of target
            exercise = int(TARGET_EXERCISE * random.uniform(0.3, 0.7))    # 30-70% of target
            protein = round(TARGET_PROTEIN * random.uniform(0.6, 0.9), 1)
            carbs = round(TARGET_CARBS * random.uniform(0.5, 0.85), 1)
            fat = round(TARGET_FAT * random.uniform(0.5, 0.8), 1)
            incomplete_days += 1
            status = "Incomplete"
        else:  # 5% - Remaining (very low values)
            # Generate very low values
            calories = int(TARGET_CALORIES * random.uniform(0.2, 0.5))    # 20-50% of target
            water = int(TARGET_WATER * random.uniform(0.2, 0.5))          # 20-50% of target
            exercise = int(TARGET_EXERCISE * random.uniform(0, 0.3))      # 0-30% of target
            protein = round(TARGET_PROTEIN * random.uniform(0.2, 0.5), 1)
            carbs = round(TARGET_CARBS * random.uniform(0.2, 0.5), 1)
            fat = round(TARGET_FAT * random.uniform(0.1, 0.4), 1)
            remaining_days += 1
            status = "Very Low"

        # Weekend variation (people tend to eat more and exercise less on weekends)
        if current_date.weekday() >= 5:  # Saturday or Sunday
            calories = int(calories * random.uniform(1.05, 1.15))
            exercise = int(exercise * random.uniform(0.7, 0.9))
            water = int(water * random.uniform(0.9, 1.05))

        # Random notes based on status
        notes_options = {
            "Completed": [
                "Great day! Met all my goals",
                "Feeling energetic and healthy",
                "Perfect nutrition day",
                "Hit all targets today",
                "Consistent with my plan"
            ],
            "Incomplete": [
                "Could do better tomorrow",
                "Missed some targets today",
                "Had a busy day",
                "Slipped on my goals",
                "Need to get back on track"
            ],
            "Very Low": [
                "Not a good day health-wise",
                "Completely off track",
                "Had to skip everything today",
                "Very busy/unwell day",
                "No time for health today"
            ]
        }
        
        notes = random.choice(notes_options[status])

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

        print(f"Added {status} data for {current_date}: {calories} calories, {water}ml water, {exercise}min exercise")

        # Move to next day
        current_date += timedelta(days=1)

    # Commit changes and close connection
    conn.commit()
    conn.close()

    # Print summary
    print(f"\nSuccessfully populated data from {start_date} to {end_date} for user_id {user_id}")
    print(f"Total days: {total_days}")
    print(f"Completed goal days (80%): {completed_days} ({completed_days/total_days*100:.1f}%)")
    print(f"Incomplete goal days (15%): {incomplete_days} ({incomplete_days/total_days*100:.1f}%)")
    print(f"Remaining days (5%): {remaining_days} ({remaining_days/total_days*100:.1f}%)")
    print("\nData generation complete. You can now view analytics and reports in the app.")

if __name__ == "__main__":
    generate_monthly_data()