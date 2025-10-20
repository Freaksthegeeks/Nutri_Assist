#!/usr/bin/env python3
"""
Installation script for Nutrition Assistant
This script installs all required dependencies and sets up the environment
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n📦 {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        return False
    return True

def main():
    """Main installation function"""
    print("🚀 Installing Nutrition Assistant Dependencies...")
    print("=" * 50)
    
    # Install pip packages
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("⚠️ Some packages might have failed to install. Continuing...")
    
    # Download spaCy model
    if not run_command("python -m spacy download en_core_web_sm", "Downloading spaCy English model"):
        print("⚠️ spaCy model download failed. You may need to install it manually.")
    
    # Download NLTK data
    print("\n📚 Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        print("✅ NLTK data downloaded successfully!")
    except Exception as e:
        print(f"⚠️ NLTK data download issue: {e}")
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✅ Directories created!")
    
    # Check environment file
    if not os.path.exists(".env"):
        print("\n⚠️ .env file not found. Creating from template...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env file created from template")
        else:
            print("❌ .env.example not found. Please create .env manually.")
    
    print("\n" + "=" * 50)
    print("🎉 Installation completed!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your API keys (optional)")
    print("2. Run: streamlit run app.py")
    print("3. Open your browser to the provided URL")
    print("\n📖 API Keys (optional but recommended):")
    print("   • Spoonacular: https://spoonacular.com/food-api")
    print("   • Nutritionix: https://www.nutritionix.com/business/api")
    print("\n💡 The app will work with fallback data even without API keys!")

if __name__ == "__main__":
    main()