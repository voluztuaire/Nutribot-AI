"""
Chat Routes
API endpoints untuk chat dengan NutriBot dan food database queries
"""

from flask import Blueprint, request, jsonify
from services.llm import chat_with_history, send_message, summarize_meal_plan, extract_meal_calendar
from services.nutrition import get_nutrition_summary

# Try to import food database service
try:
    from services.food_database import search_foods, get_food_details, search_by_nutrients
    FOOD_DB_AVAILABLE = True
except ImportError:
    FOOD_DB_AVAILABLE = False
    print("aš ï¸  Food database service not available")

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        message = data['message']
        context = data.get('context')
        history = data.get('history', [])
        model = data.get('model')  # Get model from request
        
        # Get AI response
        if history:
            # Chat with history
            response = chat_with_history(message, history, context, model=model)
        else:
            # New chat session
            response = send_message(message, context, model=model)
        
        # Generate Meal Plan Summary and Calendar if response is long (heuristically a meal plan)
        meal_plan_summary = None
        meal_calendar = None
        
        if len(response) > 500:  
            try:
                # Use Qwen2.5 to summarize and extract calendar
                from services.llm import summarize_meal_plan, extract_meal_calendar
                
                meal_plan_summary = summarize_meal_plan(response, context)
                meal_calendar = extract_meal_calendar(response)
                
            except Exception as e:
                print(f"Error generating meal plan extras: {e}")

        # Calculate nutrition summary if user context is complete
        nutrition_summary = None
        if context and all(k in context for k in ['age', 'gender', 'height', 'weight', 'activity_level', 'goal']):
            try:
                nutrition_summary = get_nutrition_summary(
                    weight=float(context['weight']),
                    height=float(context['height']),
                    age=int(context['age']),
                    gender=context['gender'],
                    activity_level=context['activity_level'],
                    goal=context['goal']
                )
            except Exception as e:
                print(f"Error calculating nutrition summary: {e}")
        
        return jsonify({
            'reply': response,
            'nutrition_summary': nutrition_summary,
            'meal_plan_summary': meal_plan_summary,
            'meal_calendar': meal_calendar,
            'error': None
        }), 200
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': str(e),
            'reply': 'Maaf, terjadi kesalahan. Coba lagi ya! ðŸ™'
        }), 500


@chat_bp.route('/nutrition', methods=['POST'])
def calculate_nutrition():
    """
    Calculate nutrition summary
    
    Request JSON:
    {
        "age": 25,
        "gender": "male",
        "height": 170,
        "weight": 70,
        "activity_level": "moderately active",
        "goal": "turun berat badan"
    }
    
    Response JSON:
    {
        "bmr": 1700,
        "tdee": 2635,
        "target_calories": 2135,
        "adjustment": -500,
        "goal_type": "defisit",
        "macros": {
            "protein": 160,
            "carbs": 213,
            "fat": 71,
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['age', 'gender', 'height', 'weight', 'activity_level', 'goal']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': f'Missing required fields: {required_fields}'
            }), 400
        
        result = get_nutrition_summary(
            weight=float(data['weight']),
            height=float(data['height']),
            age=int(data['age']),
            gender=data['gender'],
            activity_level=data['activity_level'],
            goal=data['goal'],
            macro_split=data.get('macro_split', 'balanced')
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in nutrition endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@chat_bp.route('/search-foods', methods=['POST'])
def search_foods_endpoint():
    """
    Search foods from FoodData Central database
    
    Request JSON:
    {
        "query": "chicken breast",
        "filters": {
            "max_calories": 200,
            "category": "Poultry"
        },
        "limit": 20
    }
    
    Response JSON:
    {
        "foods": [
            {
                "fdc_id": 123,
                "description": "Chicken breast, raw",
                "nutrients": {...}
            }
        ],
        "count": 10
    }
    """
    if not FOOD_DB_AVAILABLE:
        return jsonify({
            'error': 'Food database not available. Please run data ingestion first.'
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        filters = data.get('filters', {})
        limit = data.get('limit', 20)
        
        # Search foods
        foods = search_foods(query, filters=filters, limit=limit)
        
        return jsonify({
            'foods': foods,
            'count': len(foods)
        }), 200
        
    except Exception as e:
        print(f"Error in search-foods endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@chat_bp.route('/food-details/<int:fdc_id>', methods=['GET'])
def get_food_details_endpoint(fdc_id):
    """
    Get detailed information for a specific food
    
    Response JSON:
    {
        "fdc_id": 123,
        "description": "Chicken breast, raw",
        "category": "Poultry",
        "nutrients": {...},
        "portions": [...]
    }
    """
    if not FOOD_DB_AVAILABLE:
        return jsonify({
            'error': 'Food database not available'
        }), 503
    
    try:
        food = get_food_details(fdc_id)
        
        if not food:
            return jsonify({
                'error': 'Food not found'
            }), 404
        
        return jsonify(food), 200
        
    except Exception as e:
        print(f"Error in food-details endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@chat_bp.route('/suggest-alternatives', methods=['POST'])
def suggest_alternatives():
    """
    Suggest alternative foods based on nutritional criteria
    
    Request JSON:
    {
        "min_protein": 20,
        "max_calories": 200,
        "max_fat": 10,
        "category": "Poultry",
        "limit": 10
    }
    
    Response JSON:
    {
        "alternatives": [...],
        "count": 10
    }
    """
    if not FOOD_DB_AVAILABLE:
        return jsonify({
            'error': 'Food database not available'
        }), 503
    
    try:
        data = request.get_json()
        
        alternatives = search_by_nutrients(
            min_protein=data.get('min_protein'),
            max_calories=data.get('max_calories'),
            max_fat=data.get('max_fat'),
            max_carbs=data.get('max_carbs'),
            category=data.get('category'),
            limit=data.get('limit', 10)
        )
        
        return jsonify({
            'alternatives': alternatives,
            'count': len(alternatives)
        }), 200
        
    except Exception as e:
        print(f"Error in suggest-alternatives endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500



