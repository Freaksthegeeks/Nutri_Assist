import sqlite3
from datetime import datetime

def check_unique_dates():
    """Check unique dates in the database for user 1"""
    
    # Connect to the database
    conn = sqlite3.connect('nutrition_app.db')
    cursor = conn.cursor()

    # User ID to check
    user_id = 1

    # Query to get all unique dates for the user
    cursor.execute('''
        SELECT DISTINCT log_date, COUNT(*) as count
        FROM daily_logs 
        WHERE user_id = ?
        GROUP BY log_date
        ORDER BY log_date
    ''', (user_id,))

    dates = cursor.fetchall()
    
    print(f"Total unique dates for user_id {user_id}: {len(dates)}")
    
    if len(dates) > 0:
        print("\nDate range:")
        print(f"  First date: {dates[0][0]}")
        print(f"  Last date: {dates[-1][0]}")
        
        # Check for duplicates
        duplicates = [date for date in dates if date[1] > 1]
        if duplicates:
            print(f"\nFound {len(duplicates)} dates with duplicate entries:")
            for date, count in duplicates[:5]:  # Show first 5 duplicates
                print(f"  {date}: {count} entries")
        else:
            print("\nNo duplicate dates found.")
        
        # Show date distribution
        print(f"\nAll dates (showing first 10 and last 10):")
        if len(dates) <= 20:
            for date, count in dates:
                print(f"  {date}: {count} entry")
        else:
            print("First 10 dates:")
            for date, count in dates[:10]:
                print(f"  {date}: {count} entry")
            print("...")    
            print("Last 10 dates:")
            for date, count in dates[-10:]:
                print(f"  {date}: {count} entry")
    else:
        print("No records found.")
    
    conn.close()

if __name__ == "__main__":
    check_unique_dates()