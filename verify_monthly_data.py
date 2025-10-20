import sqlite3
from datetime import datetime

def verify_monthly_data():
    """Verify the monthly data was properly inserted"""
    
    # Connect to the database
    conn = sqlite3.connect('nutrition_app.db')
    cursor = conn.cursor()

    # User ID to check
    user_id = 1

    # Date range: September 17 to October 17, 2025
    start_date = datetime(2025, 9, 17).date()
    end_date = datetime(2025, 10, 17).date()

    # Query to get all daily logs for the user in the date range
    cursor.execute('''
        SELECT log_date, calories_consumed, water_ml, exercise_minutes
        FROM daily_logs 
        WHERE user_id = ? AND log_date BETWEEN ? AND ?
        ORDER BY log_date
    ''', (user_id, start_date, end_date))

    logs = cursor.fetchall()
    
    print(f"Verifying data from {start_date} to {end_date} for user_id {user_id}")
    print(f"Total records found: {len(logs)}")
    
    if len(logs) > 0:
        print("\nFirst 5 records:")
        for i, log in enumerate(logs[:5]):
            print(f"  {log[0]}: {log[1]} calories, {log[2]}ml water, {log[3]}min exercise")
        
        print("\nLast 5 records:")
        for i, log in enumerate(logs[-5:]):
            print(f"  {log[0]}: {log[1]} calories, {log[2]}ml water, {log[3]}min exercise")
        
        # Calculate averages
        total_calories = sum(log[1] for log in logs)
        total_water = sum(log[2] for log in logs)
        total_exercise = sum(log[3] for log in logs)
        
        avg_calories = total_calories / len(logs)
        avg_water = total_water / len(logs)
        avg_exercise = total_exercise / len(logs)
        
        print(f"\nAverages:")
        print(f"  Calories: {avg_calories:.1f}")
        print(f"  Water: {avg_water:.1f}ml")
        print(f"  Exercise: {avg_exercise:.1f}min")
        
        # Check for dynamic differences by looking at variance
        calorie_variance = sum((log[1] - avg_calories) ** 2 for log in logs) / len(logs)
        water_variance = sum((log[2] - avg_water) ** 2 for log in logs) / len(logs)
        exercise_variance = sum((log[3] - avg_exercise) ** 2 for log in logs) / len(logs)
        
        print(f"\nVariance (indicates dynamic differences):")
        print(f"  Calories: {calorie_variance:.1f}")
        print(f"  Water: {water_variance:.1f}")
        print(f"  Exercise: {exercise_variance:.1f}")
    else:
        print("No records found in the specified date range.")
    
    conn.close()

if __name__ == "__main__":
    verify_monthly_data()