# Nutrition Assistant Dashboard

A comprehensive nutrition assistant built with Streamlit and advanced NLP capabilities.

## 🌟 Features

### Core Functionality
- **User Authentication**: Secure registration and login system
- **Profile Management**: Comprehensive diet preferences, allergens, activity levels, and health goals
- **Meal Analysis**: AI-powered ingredient analysis and nutritional recommendations
- **Weekly Meal Planner**: Personalized 7-day meal plans
- **Intelligent Chatbot**: Natural language nutrition assistant
- **Nutrition Tracking**: BMI calculation, calorie estimation, and macro tracking
- **Analytics Dashboard**: Visual insights and personalized recommendations

### NLP Technologies Used
- **spaCy**: Named entity recognition and ingredient extraction
- **NLTK & TextBlob**: Text processing and sentiment analysis
- **Sentence Transformers**: Semantic similarity for meal recommendations
- **Scikit-learn**: Classification and clustering for nutrition analysis
- **Transformers (Optional)**: Advanced language understanding

## 🚀 Quick Start

### Option 1: Simplified Version (Recommended for Quick Testing)

```bash
# Clone or download the project
# Navigate to the project directory
cd nlp-project

# Install basic requirements
pip install streamlit pandas plotly

# Run the simplified app
streamlit run app_simple.py
```

### Option 2: Full Version with Advanced NLP

```bash
# Install all dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run the full app
streamlit run app.py
```

### Option 3: Automated Installation

```bash
# Run the installation script
python install_dependencies.py

# Start the application
streamlit run app.py
```

## 📁 Project Structure

```
nlp-project/
├── app.py                    # Main Streamlit application (full version)
├── app_simple.py            # Simplified version without heavy dependencies
├── database.py              # Database management and user authentication
├── nlp_analyzer.py          # Advanced NLP analysis engine
├── meal_planner.py          # Meal planning with API integration
├── chatbot.py               # Intelligent nutrition chatbot
├── requirements.txt         # Python dependencies
├── install_dependencies.py  # Automated setup script
├── start_app.bat           # Windows startup script
├── start_app.sh            # Linux/Mac startup script
├── .env                    # Environment variables
├── .env.example            # Environment template
└── README.md               # This file
```

## 💡 Usage Guide

### 1. Registration and Login
- Create a new account or login with existing credentials
- All data is stored securely in a local SQLite database

### 2. Profile Setup
- Enter basic information (age, gender, height, weight)
- Set activity level and diet preferences
- Specify health goals (weight loss, muscle gain, etc.)
- List any allergies or dietary restrictions

### 3. Meal Analysis
- Describe your meal in natural language
- Get instant nutritional analysis
- Receive personalized recommendations
- View food group breakdown

### 4. Weekly Meal Planning
- Generate personalized 7-day meal plans
- Based on your profile and health goals
- Considers dietary restrictions and preferences
- Download plans as JSON files

### 5. Nutrition Chatbot (Full Version)
- Ask questions in natural language
- Get meal suggestions and recipe analysis
- Receive nutrition advice and tips
- Example queries:
  - "I want a high-protein lunch for muscle gain"
  - "Analyze this recipe: chicken, rice, broccoli"
  - "Suggest vegan meals for the week"

### 6. Analytics and Tracking
- View BMI and calorie recommendations
- Track macronutrient distribution
- Get personalized nutrition tips
- Visual charts and insights

## 🔧 Configuration

### API Keys (Optional)

For enhanced functionality, you can add API keys to the `.env` file:

```env
# Spoonacular API for recipe data
SPOONACULAR_API_KEY=your_key_here

# Nutritionix API for nutrition information
NUTRITIONIX_APP_ID=your_app_id_here
NUTRITIONIX_API_KEY=your_key_here
```

**Get API Keys:**
- [Spoonacular API](https://spoonacular.com/food-api) - Free tier available
- [Nutritionix API](https://www.nutritionix.com/business/api) - Free tier available

### Environment Variables

```env
# Database configuration
DATABASE_URL=sqlite:///nutrition_app.db

# Security
SECRET_KEY=your_secret_key_here
```

## 🤖 NLP Features in Detail

### Ingredient Extraction
- Uses spaCy's named entity recognition
- Custom food vocabulary and patterns
- Handles various input formats and descriptions

### Nutritional Analysis
- Categorizes ingredients into food groups
- Calculates nutrition scores based on balance
- Provides personalized recommendations

### Natural Language Processing
- Intent recognition for user queries
- Entity extraction (meal types, diet preferences, goals)
- Sentiment analysis for user feedback

### Semantic Similarity
- Meal recommendation based on user preferences
- Recipe clustering and categorization
- Ingredient substitution suggestions

## 📊 Data Sources

- **Spoonacular API**: Recipe data and nutrition information
- **Nutritionix API**: Comprehensive food database
- **Custom Knowledge Base**: Nutrition facts and recommendations
- **Local Database**: User profiles and meal logs

## 🛠️ Technical Requirements

### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 1GB free disk space

### Recommended Requirements
- Python 3.9+
- 8GB RAM
- 2GB free disk space
- Internet connection for API features

## 🔒 Security Features

- Secure password hashing (bcrypt or fallback)
- SQLite database with prepared statements
- Session management
- Input validation and sanitization

## 🌐 Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🐛 Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Use `app_simple.py` for basic functionality
   - Install dependencies: `pip install streamlit pandas plotly`

2. **spaCy Model Not Found**
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **API Errors**
   - Check your internet connection
   - Verify API keys in `.env` file
   - App works with fallback data without APIs

4. **Database Issues**
   - Delete `nutrition_app.db` to reset
   - Check file permissions

### Performance Optimization

- Use `app_simple.py` for faster startup
- Add API keys for better meal planning
- Clear browser cache if UI issues occur

## 🔄 Updates and Maintenance

### Regular Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update spaCy model
python -m spacy download en_core_web_sm --upgrade
```

### Database Backup
```bash
# Backup user data
cp nutrition_app.db nutrition_app_backup.db
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section
2. Review the error logs in the terminal
3. Try the simplified version (`app_simple.py`)
4. Check for environment-specific issues

## 🎯 Future Enhancements

- [ ] Mobile app version
- [ ] Integration with fitness trackers
- [ ] Meal photo analysis
- [ ] Social features and meal sharing
- [ ] Advanced ML models for recommendations
- [ ] Multi-language support
- [ ] Offline mode capabilities

---

**Happy Nutrition Tracking! 🥗💪**