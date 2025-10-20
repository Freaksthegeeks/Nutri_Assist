import re
import json
import random
from datetime import datetime
from nlp_analyzer import nlp_analyzer
from meal_planner import meal_planner

class NutritionChatbot:
    def __init__(self):
        self.conversation_history = []
        self.context = {}
        
        # Intent patterns
        self.intent_patterns = {
            'meal_suggestion': [
                r'suggest.*meal', r'recommend.*food', r'what.*eat',
                r'meal.*idea', r'food.*recommendation'
            ],
            'recipe_analysis': [
                r'analyze.*recipe', r'check.*recipe', r'review.*meal',
                r'is.*healthy', r'nutrition.*analysis'
            ],
            'meal_planning': [
                r'meal.*plan', r'weekly.*plan', r'plan.*week',
                r'schedule.*meal', r'diet.*plan'
            ],
            'nutrition_info': [
                r'nutrition.*facts', r'calories.*in', r'protein.*content',
                r'vitamin.*in', r'mineral.*content'
            ],
            'diet_advice': [
                r'diet.*advice', r'lose.*weight', r'gain.*muscle',
                r'healthy.*eating', r'nutrition.*tips'
            ],
            'ingredient_substitute': [
                r'substitute.*for', r'replace.*with', r'alternative.*to',
                r'instead.*of', r'swap.*out'
            ]
        }
        
        # Response templates
        self.response_templates = {
            'greeting': [
                "Hello! I'm your nutrition assistant. How can I help you with your dietary needs today?",
                "Hi there! Ready to explore some healthy meal options?",
                "Welcome! I'm here to help with all your nutrition questions."
            ],
            'meal_suggestion': [
                "Based on your preferences, here are some great meal options:",
                "I'd recommend these meals for you:",
                "Here are some nutritious meal ideas:"
            ],
            'recipe_analysis': [
                "Let me analyze that recipe for you:",
                "Here's my nutritional assessment:",
                "I've reviewed your recipe - here's what I found:"
            ],
            'clarification': [
                "Could you provide more details about what you're looking for?",
                "I'd like to help you better. Can you tell me more about your dietary goals?",
                "To give you the best recommendations, could you share more information?"
            ]
        }
    
    def process_message(self, message, user_profile=None):
        """Process user message and generate response"""
        # Store message in conversation history
        self.conversation_history.append({
            'user': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze the message using NLP
        analyzed_query = nlp_analyzer.process_natural_language_query(message)
        
        # Determine intent
        intent = self._determine_intent(message)
        
        # Extract key information
        extracted_info = self._extract_information(message, analyzed_query)
        
        # Generate response based on intent
        response = self._generate_response(intent, extracted_info, analyzed_query, user_profile)
        
        # Store response in conversation history
        self.conversation_history.append({
            'assistant': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def _determine_intent(self, message):
        """Determine user intent from message"""
        message_lower = message.lower()
        
        # Check for greeting
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        if any(word in message_lower for word in greeting_words):
            return 'greeting'
        
        # Check intent patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        # Default to general inquiry
        return 'general_inquiry'
    
    def _extract_information(self, message, analyzed_query):
        """Extract key information from the message"""
        info = {
            'meal_type': analyzed_query['entities'].get('meal_type'),
            'diet_type': analyzed_query['entities'].get('diet_type'),
            'goal': analyzed_query['entities'].get('goal'),
            'ingredients': analyzed_query['entities'].get('ingredients', []),
            'time_frame': self._extract_time_frame(message),
            'dietary_restrictions': self._extract_dietary_restrictions(message),
            'cooking_method': self._extract_cooking_method(message),
            'cuisine_type': self._extract_cuisine_type(message)
        }
        
        return info
    
    def _extract_time_frame(self, message):
        """Extract time frame from message"""
        time_patterns = {
            'today': r'today|tonight|this evening',
            'tomorrow': r'tomorrow',
            'week': r'week|weekly|7 days',
            'month': r'month|monthly',
            'quick': r'quick|fast|30 minutes|20 minutes'
        }
        
        message_lower = message.lower()
        for time_frame, pattern in time_patterns.items():
            if re.search(pattern, message_lower):
                return time_frame
        
        return None
    
    def _extract_dietary_restrictions(self, message):
        """Extract dietary restrictions from message"""
        restrictions = []
        restriction_keywords = {
            'vegetarian': ['vegetarian', 'veggie'],
            'vegan': ['vegan'],
            'gluten_free': ['gluten free', 'gluten-free', 'no gluten'],
            'dairy_free': ['dairy free', 'dairy-free', 'no dairy', 'lactose free'],
            'low_carb': ['low carb', 'low-carb', 'keto', 'ketogenic'],
            'low_fat': ['low fat', 'low-fat'],
            'high_protein': ['high protein', 'high-protein', 'protein rich']
        }
        
        message_lower = message.lower()
        for restriction, keywords in restriction_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                restrictions.append(restriction)
        
        return restrictions
    
    def _extract_cooking_method(self, message):
        """Extract preferred cooking method"""
        cooking_methods = ['grilled', 'baked', 'steamed', 'fried', 'roasted', 'sautéed', 'raw']
        message_lower = message.lower()
        
        for method in cooking_methods:
            if method in message_lower:
                return method
        
        return None
    
    def _extract_cuisine_type(self, message):
        """Extract cuisine type preference"""
        cuisines = ['italian', 'mexican', 'asian', 'indian', 'mediterranean', 'american', 'chinese', 'thai']
        message_lower = message.lower()
        
        for cuisine in cuisines:
            if cuisine in message_lower:
                return cuisine
        
        return None
    
    def _generate_response(self, intent, extracted_info, analyzed_query, user_profile):
        """Generate appropriate response based on intent"""
        
        if intent == 'greeting':
            return random.choice(self.response_templates['greeting'])
        
        elif intent == 'meal_suggestion':
            return self._generate_meal_suggestions(extracted_info, user_profile)
        
        elif intent == 'recipe_analysis':
            return self._analyze_recipe(extracted_info, user_profile)
        
        elif intent == 'meal_planning':
            return self._generate_meal_plan_response(extracted_info, user_profile)
        
        elif intent == 'nutrition_info':
            return self._provide_nutrition_info(extracted_info)
        
        elif intent == 'diet_advice':
            return self._provide_diet_advice(extracted_info, user_profile)
        
        elif intent == 'ingredient_substitute':
            return self._suggest_substitutes(extracted_info)
        
        else:
            return self._handle_general_inquiry(analyzed_query, user_profile)
    
    def _generate_meal_suggestions(self, extracted_info, user_profile):
        """Generate meal suggestions based on extracted information"""
        # Create a query for the NLP analyzer
        query_parts = []
        
        if extracted_info['meal_type']:
            query_parts.append(extracted_info['meal_type'])
        
        if extracted_info['goal']:
            query_parts.append(extracted_info['goal'])
        
        if extracted_info['diet_type']:
            query_parts.append(extracted_info['diet_type'])
        
        query = ' '.join(query_parts) if query_parts else "healthy meal"
        
        # Parse the query
        parsed_query = nlp_analyzer.process_natural_language_query(query)
        
        # Generate suggestions
        suggestions = nlp_analyzer.generate_meal_suggestions(parsed_query, user_profile)
        
        response = random.choice(self.response_templates['meal_suggestion'])
        response += "\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            response += f"{i}. {suggestion}\n"
        
        # Add personalized notes
        if user_profile:
            health_goals = user_profile.get('health_goals', [])
            if health_goals:
                response += f"\n💡 These suggestions align with your goals: {', '.join(health_goals)}"
        
        return response
    
    def _analyze_recipe(self, extracted_info, user_profile):
        """Analyze a recipe or meal"""
        ingredients = extracted_info['ingredients']
        
        if not ingredients:
            return "Please provide the ingredients or recipe you'd like me to analyze."
        
        # Analyze the meal
        analysis = nlp_analyzer.analyze_meal_nutrition(ingredients, user_profile)
        
        response = random.choice(self.response_templates['recipe_analysis'])
        response += "\n\n"
        
        # Nutrition score
        score = analysis['nutrition_score']
        response += f"🏆 **Nutrition Score:** {score}/100\n\n"
        
        # Category analysis
        categories = analysis['category_analysis']
        response += "📊 **Food Groups Present:**\n"
        for category, items in categories.items():
            if items:
                response += f"• {category.title()}: {', '.join(items)}\n"
        
        # Nutritional benefits
        if analysis['nutritional_benefits']:
            response += "\n✨ **Nutritional Benefits:**\n"
            for benefit in analysis['nutritional_benefits'][:3]:
                response += f"• {benefit}\n"
        
        # Recommendations
        if analysis['recommendations']:
            response += "\n💡 **Recommendations:**\n"
            for rec in analysis['recommendations']:
                response += f"• {rec}\n"
        
        # Allergen warnings
        if analysis['allergen_warnings']:
            response += "\n⚠️ **Allergen Warnings:**\n"
            for warning in analysis['allergen_warnings']:
                response += f"• {warning}\n"
        
        return response
    
    def _generate_meal_plan_response(self, extracted_info, user_profile):
        """Generate meal plan response"""
        if not user_profile:
            return "I'd love to create a meal plan for you! Please set up your profile first so I can personalize it to your dietary needs and goals."
        
        time_frame = extracted_info.get('time_frame', 'week')
        
        if time_frame == 'week' or 'week' in str(extracted_info):
            try:
                # Generate weekly meal plan
                weekly_plan = meal_planner.generate_weekly_plan(user_profile)
                
                response = "🗓️ **Your Personalized Weekly Meal Plan:**\n\n"
                
                # Show first 2 days as preview
                day_count = 0
                for day, meals in weekly_plan.items():
                    if day_count >= 2:
                        break
                    
                    response += f"**{day}:**\n"
                    for meal_type, meal in meals.items():
                        response += f"• {meal_type.title()}: {meal['title']}\n"
                    response += "\n"
                    day_count += 1
                
                response += "📝 This is a preview. The complete plan includes all 7 days with detailed recipes and nutrition information!"
                
                return response
            except Exception as e:
                return "I'm having trouble generating your meal plan right now. Please try again in a moment."
        
        return "I can help you create meal plans! What time frame are you looking for? (daily, weekly, etc.)"
    
    def _provide_nutrition_info(self, extracted_info):
        """Provide general nutrition information"""
        nutrition_facts = {
            'protein': {
                'description': 'Essential for muscle building and repair',
                'sources': ['chicken', 'fish', 'beans', 'tofu', 'eggs'],
                'daily_need': '0.8g per kg of body weight'
            },
            'carbohydrates': {
                'description': 'Primary energy source for the body',
                'sources': ['rice', 'pasta', 'fruits', 'vegetables'],
                'daily_need': '45-65% of total calories'
            },
            'fats': {
                'description': 'Important for hormone production and nutrient absorption',
                'sources': ['nuts', 'avocado', 'olive oil', 'fish'],
                'daily_need': '20-35% of total calories'
            },
            'fiber': {
                'description': 'Aids digestion and helps maintain healthy gut',
                'sources': ['beans', 'oats', 'vegetables', 'fruits'],
                'daily_need': '25g for women, 38g for men'
            }
        }
        
        # Look for specific nutrients mentioned
        ingredients = extracted_info.get('ingredients', [])
        query_text = ' '.join(ingredients).lower()
        
        response = "📚 **Nutrition Information:**\n\n"
        
        for nutrient, info in nutrition_facts.items():
            if nutrient in query_text or any(source in query_text for source in info['sources']):
                response += f"**{nutrient.title()}:**\n"
                response += f"• {info['description']}\n"
                response += f"• Good sources: {', '.join(info['sources'])}\n"
                response += f"• Daily need: {info['daily_need']}\n\n"
        
        if response == "📚 **Nutrition Information:**\n\n":
            response += "I can provide information about proteins, carbohydrates, fats, vitamins, and minerals. What specific nutrient would you like to know about?"
        
        return response
    
    def _provide_diet_advice(self, extracted_info, user_profile):
        """Provide personalized diet advice"""
        advice = {
            'weight_loss': [
                "Focus on creating a caloric deficit through portion control",
                "Include plenty of vegetables and lean proteins",
                "Stay hydrated and limit processed foods",
                "Aim for 150 minutes of moderate exercise per week"
            ],
            'muscle_gain': [
                "Consume adequate protein (1.6-2.2g per kg body weight)",
                "Include complex carbohydrates for energy",
                "Don't forget healthy fats for hormone production",
                "Time protein intake around workouts"
            ],
            'balanced_diet': [
                "Follow the plate method: 1/2 vegetables, 1/4 protein, 1/4 whole grains",
                "Include a variety of colorful foods",
                "Stay hydrated with 8-10 glasses of water daily",
                "Practice mindful eating and portion control"
            ]
        }
        
        goal = extracted_info.get('goal')
        if user_profile:
            health_goals = user_profile.get('health_goals', [])
            if health_goals:
                goal = health_goals[0]  # Use primary goal
        
        response = "🎯 **Personalized Diet Advice:**\n\n"
        
        if goal and goal.replace(' ', '_') in advice:
            goal_advice = advice[goal.replace(' ', '_')]
            for tip in goal_advice:
                response += f"• {tip}\n"
        else:
            # General advice
            response += "• Eat a variety of whole foods\n"
            response += "• Stay hydrated throughout the day\n"
            response += "• Practice portion control\n"
            response += "• Include regular physical activity\n"
        
        response += "\n💡 Remember: Consistency is key to achieving your health goals!"
        
        return response
    
    def _suggest_substitutes(self, extracted_info):
        """Suggest ingredient substitutes"""
        substitutes = {
            'butter': ['olive oil', 'coconut oil', 'applesauce', 'mashed banana'],
            'sugar': ['honey', 'maple syrup', 'stevia', 'dates'],
            'flour': ['almond flour', 'coconut flour', 'oat flour'],
            'milk': ['almond milk', 'oat milk', 'coconut milk', 'soy milk'],
            'eggs': ['flax eggs', 'chia eggs', 'applesauce', 'banana'],
            'cheese': ['nutritional yeast', 'cashew cheese', 'tofu'],
            'meat': ['tofu', 'tempeh', 'mushrooms', 'lentils', 'beans']
        }
        
        ingredients = extracted_info.get('ingredients', [])
        
        response = "🔄 **Ingredient Substitutes:**\n\n"
        
        found_substitutes = False
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            for original, subs in substitutes.items():
                if original in ingredient_lower:
                    response += f"**Instead of {original}:**\n"
                    for sub in subs:
                        response += f"• {sub}\n"
                    response += "\n"
                    found_substitutes = True
        
        if not found_substitutes:
            response += "What ingredient would you like to substitute? I can suggest alternatives for common ingredients like butter, sugar, flour, dairy, and more!"
        
        return response
    
    def _handle_general_inquiry(self, analyzed_query, user_profile):
        """Handle general nutrition inquiries"""
        responses = [
            "I'm here to help with your nutrition questions! You can ask me about:",
            "• Meal suggestions and recipes",
            "• Nutritional analysis of foods",
            "• Weekly meal planning",
            "• Diet advice and tips",
            "• Ingredient substitutions",
            "• Nutrition facts and information",
            "",
            "What would you like to know about?"
        ]
        
        return "\n".join(responses)
    
    def get_conversation_summary(self):
        """Get a summary of the conversation"""
        if not self.conversation_history:
            return "No conversation history yet."
        
        user_messages = [msg for msg in self.conversation_history if 'user' in msg]
        assistant_messages = [msg for msg in self.conversation_history if 'assistant' in msg]
        
        summary = f"Conversation Summary:\n"
        summary += f"• Total messages: {len(self.conversation_history)}\n"
        summary += f"• User messages: {len(user_messages)}\n"
        summary += f"• Assistant responses: {len(assistant_messages)}\n"
        
        return summary

# Initialize the chatbot
nutrition_chatbot = NutritionChatbot()