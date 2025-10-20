import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def test_data_access():
    """Test that the app can access the generated data"""
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Test user ID
    user_id = 1
    
    # Get recent daily logs
    try:
        logs = db.get_daily_logs(user_id, 30)  # Get last 30 days
        print(f"Successfully retrieved {len(logs)} daily logs")
        
        if logs:
            print("\nMost recent logs:")
            for i, log in enumerate(logs[:5]):  # Show first 5
                print(f"  {log['date']}: {log['calories']} calories, {log['water']}ml water, {log['exercise']}min exercise")
            
            print("\nDate range:")
            if len(logs) > 0:
                dates = [log['date'] for log in logs]
                print(f"  First: {min(dates)}")
                print(f"  Last: {max(dates)}")
                
            # Calculate averages
            avg_calories = sum(log['calories'] for log in logs) / len(logs)
            avg_water = sum(log['water'] for log in logs) / len(logs)
            avg_exercise = sum(log['exercise'] for log in logs) / len(logs)
            
            print(f"\nAverages:")
            print(f"  Calories: {avg_calories:.1f}")
            print(f"  Water: {avg_water:.1f}ml")
            print(f"  Exercise: {avg_exercise:.1f}min")
            
        else:
            print("No logs retrieved")
            
    except Exception as e:
        print(f"Error retrieving logs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_access()