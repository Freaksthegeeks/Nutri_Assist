import sqlite3

# Connect to the database
conn = sqlite3.connect('nutrition_app.db')
cursor = conn.cursor()

# Check the number of daily logs for user_id 1
cursor.execute('SELECT COUNT(*) FROM daily_logs WHERE user_id = 1')
count = cursor.fetchone()[0]
print(f'Daily logs count for user_id 1: {count}')

# Show some sample data
cursor.execute('SELECT log_date, calories_consumed, water_ml, exercise_minutes FROM daily_logs WHERE user_id = 1 ORDER BY log_date LIMIT 5')
logs = cursor.fetchall()
print('\nSample data:')
for log in logs:
    print(log)

conn.close()