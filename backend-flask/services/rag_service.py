"""
RAG Service - Retrieval-Augmented Generation
Connects food database with LLM for context-aware meal planning
"""

import os
from typing import List, Dict, Optional
from services.food_database import (
    search_foods, 
    search_by_nutrients,
    get_food_details,
    get_food_categories,
    get_random_foods
)
from services.local_llm import (
    LocalLLM, 
    create_meal_plan_prompt, 
    get_system_prompt,
    summarize_meal_plan,
    summarize_nutrition_info,
    SUMMARIZATION_MODEL
)


class RAGService:
    """RAG service for intelligent meal planning"""
    
    def __init__(self, model_name: str = 'llama3.2:3b'):
        """
        Initialize RAG service
        
        Args:
            model_name: LLM model to use
        """
        self.llm = LocalLLM(model_name=model_name)
        self.context_cache = {}
    
    def get_relevant_foods(self, user_data: Dict) -> List[Dict]:
        """
        Retrieve relevant foods based on user profile and goals
        
        Args:
            user_data: User profile (goal, preferences, allergies, etc.)
        
        Returns:
            List of relevant food items
        """
        goal = user_data.get('goal', '').lower()
        preferences = user_data.get('preferences', [])
        allergies = user_data.get('allergies', [])
        
        relevant_foods = []
        
        # Goal-based food retrieval
        if 'weight loss' in goal or 'turun berat' in goal or 'diet' in goal:
            # High protein, low calorie foods
            foods = search_by_nutrients(
                min_protein=15,
                max_calories=200,
                limit=30
            )
            relevant_foods.extend(foods)
        
        elif 'muscle' in goal or 'otot' in goal or 'naik berat' in goal:
            # High protein foods
            foods = search_by_nutrients(
                min_protein=20,
                limit=30
            )
            relevant_foods.extend(foods)
        
        elif 'maintain' in goal or 'jaga' in goal:
            # Balanced foods
            foods = search_by_nutrients(
                min_protein=10,
                max_calories=300,
                limit=30
            )
            relevant_foods.extend(foods)
        
        # Add variety with random foods from different categories
        categories = ['Vegetables', 'Fruits', 'Proteins', 'Grains']
        for category in categories:
            try:
                random_foods = get_random_foods(category=category, limit=5)
                relevant_foods.extend(random_foods)
            except:
                pass
        
        # Filter out allergens
        if allergies:
            relevant_foods = self._filter_allergens(relevant_foods, allergies)
        
        # Remove duplicates
        seen = set()
        unique_foods = []
        for food in relevant_foods:
            if food['fdc_id'] not in seen:
                seen.add(food['fdc_id'])
                unique_foods.append(food)
        
        return unique_foods[:50]  # Limit to top 50
    
    def _filter_allergens(self, foods: List[Dict], allergies: List[str]) -> List[Dict]:
        """Filter out foods containing allergens"""
        filtered = []
        
        for food in foods:
            description = food.get('description', '').lower()
            ingredients = food.get('ingredients', '').lower() if food.get('ingredients') else ''
            
            # Check if any allergen is in description or ingredients
            has_allergen = False
            for allergen in allergies:
                allergen_lower = allergen.lower()
                if allergen_lower in description or allergen_lower in ingredients:
                    has_allergen = True
                    break
            
            if not has_allergen:
                filtered.append(food)
        
        return filtered
    
    def build_food_context(self, foods: List[Dict], max_items: int = 30) -> str:
        """
        Build context string from food data for LLM
        
        Args:
            foods: List of food items
            max_items: Maximum items to include in context
        
        Returns:
            Formatted context string
        """
        if not foods:
            return "Tidak ada data makanan spesifik tersedia. Gunakan pengetahuan umum."
        
        context = "Here are available foods with nutrition data:\n\n"
        
        for i, food in enumerate(foods[:max_items]):
            nutrients = food.get('nutrients', {})
            
            context += f"{i+1}. **{food.get('description', 'Unknown')}**\n"
            
            if food.get('brand_name'):
                context += f"   Brand: {food['brand_name']}\n"
            
            if nutrients:
                context += "   Nutrition (per 100g): "
                nutrient_parts = []
                
                if nutrients.get('calories'):
                    nutrient_parts.append(f"{nutrients['calories']:.0f} kcal")
                if nutrients.get('protein'):
                    nutrient_parts.append(f"Protein {nutrients['protein']:.1f}g")
                if nutrients.get('carbs'):
                    nutrient_parts.append(f"Carbs {nutrients['carbs']:.1f}g")
                if nutrients.get('fat'):
                    nutrient_parts.append(f"Fat {nutrients['fat']:.1f}g")
                
                context += ", ".join(nutrient_parts) + "\n"
            
            context += "\n"
        
        context += "\nUse the foods above as a reference for the meal plan. "
        context += "You may include other common foods if necessary.\n"
        
        return context
    
    def generate_meal_plan(self, user_data: Dict, use_rag: bool = True) -> str:
        """
        Generate meal plan using RAG
        
        Args:
            user_data: User profile and requirements
            use_rag: Whether to use RAG (retrieve food context)
        
        Returns:
            Generated meal plan as markdown string
        """
        food_context = None
        
        if use_rag:
            # Retrieve relevant foods
            print("Retrieving relevant foods from database...")
            relevant_foods = self.get_relevant_foods(user_data)
            print(f"Found {len(relevant_foods)} relevant foods")
            
            # Build context
            food_context = self.build_food_context(relevant_foods)
        
        # Create prompt
        prompt = create_meal_plan_prompt(user_data, food_context)
        
        # Generate response
        print(f"Generating meal plan with {self.llm.model_name}...")
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=get_system_prompt(),
            temperature=0.7,
            max_tokens=4096
        )
        
        # Generate summary using Qwen2.5 for better quality
        print(f"Generating summary with {SUMMARIZATION_MODEL}...")
        try:
            summary = summarize_meal_plan(response, user_data)
            # Append summary to response
            response += f"\n\n---\n\n## ðŸ“‹ Ringkasan Meal Plan\n\n{summary}"
        except Exception as e:
            print(f"Warning: Could not generate summary: {e}")
        
        return response
    
    def chat_with_context(
        self, 
        message: str, 
        user_data: Optional[Dict] = None,
        history: Optional[List[Dict]] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Chat with context from food database
        
        Args:
            message: User message
            user_data: Optional user profile
            history: Optional conversation history
            model: Optional model override
        
        Returns:
            AI response
        """
        # Detect user language FIRST
        detected_lang = self._detect_language(message)
        
        # Build messages
        messages = [{'role': 'system', 'content': get_system_prompt()}]
        
        # Add history
        if history:
            messages.extend(history)
        
        # Check if user is asking about specific foods
        if self._is_food_query(message):
            # Search for relevant foods
            search_terms = self._extract_food_terms(message)
            relevant_foods = []
            
            for term in search_terms:
                foods = search_foods(term, limit=5)
                relevant_foods.extend(foods)
            
            if relevant_foods:
                # Add food context to message
                food_context = self.build_food_context(relevant_foods, max_items=10)
                message = f"{message}\n\n{food_context}"
        
        # INJECT LANGUAGE DIRECTIVE (CRITICAL FOR FORCING LANGUAGE)
        if detected_lang == 'id':
            lang_directive = "[PENTING: JAWAB DALAM BAHASA INDONESIA]\n\n"
        else:
            lang_directive = "[IMPORTANT: YOU MUST REPLY IN ENGLISH]\n\n"
        
        # INJECT FORMAT DIRECTIVE (CRITICAL FOR NUMBERED LIST)
        format_directive = ""
        if self._is_list_request(message):
            if detected_lang == 'id':
                format_directive = "[FORMAT: Gunakan nomor 1. 2. 3. 4. untuk setiap item. Contoh:\n1. **Nasi Goreng** - Deskripsi singkat (350 kkal, 15g protein)\n2. **Ayam Bakar** - Deskripsi singkat (400 kkal, 35g protein)]\n\n"
            else:
                format_directive = "[FORMAT: Use numbered list 1. 2. 3. 4. for each item. Example:\n1. **Grilled Chicken** - Brief description (350 kcal, 35g protein)\n2. **Salmon Bowl** - Brief description (400 kcal, 40g protein)]\n\n"
        
        message_with_directive = lang_directive + format_directive + message
        
        # Add user message with directive
        messages.append({'role': 'user', 'content': message_with_directive})
        
        # Generate response
        response = self.llm.chat(messages, temperature=0.7, max_tokens=2048, model=model)
        
        # POST-PROCESS: Auto-number response if list was requested but LLM didn't number
        if self._is_list_request(message):
            response = self._auto_number_response(response)
        
        return response
    
    def _auto_number_response(self, response: str) -> str:
        """
        Post-process response to add numbers if they're missing.
        Detects bold items (e.g., **Meal Name**) and numbers them.
        """
        import re
        
        # Check if response already has numbered format (1. 2. 3.)
        if re.search(r'^\s*\d+\.', response, re.MULTILINE):
            print("DEBUG: Response already has numbers, skipping post-process")
            return response
        
        # Find all bold items that look like meal names
        # Pattern: **Something** - description OR **Something**: description
        lines = response.split('\n')
        new_lines = []
        item_number = 1
        
        for line in lines:
            # Check if line starts with bold item (no number)
            if re.match(r'^\s*\*\*[^*]+\*\*\s*[-:]', line):
                # Add number prefix
                stripped = line.lstrip()
                indent = line[:len(line) - len(stripped)]
                new_line = f"{indent}{item_number}. {stripped}"
                new_lines.append(new_line)
                item_number += 1
            else:
                new_lines.append(line)
        
        result = '\n'.join(new_lines)
        if item_number > 1:
            print(f"DEBUG: Post-processed response, added {item_number - 1} numbers")
        return result
    
    def _is_list_request(self, message: str) -> bool:
        """Check if user is asking for a numbered list of items"""
        import re
        message_lower = message.lower()
        
        # Simple keyword check first
        has_number = bool(re.search(r'\d+', message_lower))
        has_meal_word = any(word in message_lower for word in ['meal', 'menu', 'food', 'makanan', 'suggest', 'give', 'berikan', 'buatkan'])
        
        print(f"DEBUG _is_list_request: has_number={has_number}, has_meal_word={has_meal_word}, message='{message_lower[:50]}'")
        
        if has_number and has_meal_word:
            print("DEBUG: List request DETECTED!")
            return True
        
        return False
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words.
        Returns 'id' for Indonesian, 'en' for English.
        """
        text_lower = text.lower()
        
        # Indonesian indicators (common words/phrases)
        indonesian_keywords = [
            'saya', 'aku', 'tolong', 'buatkan', 'berikan', 'kasih', 
            'makan', 'makanan', 'bisa', 'bagaimana', 'apa', 'apakah',
            'mohon', 'untuk', 'adalah', 'yang', 'dengan', 'ini', 'itu',
            'sudah', 'belum', 'ingin', 'mau', 'harus', 'boleh', 'tidak',
            'sehat', 'diet', 'resep', 'masakan', 'menu', 'sarapan',
            'minum', 'kalori', 'protein', 'lemak', 'karbohidrat'
        ]
        
        # English indicators
        english_keywords = [
            'i ', "i'm", 'please', 'can you', 'could you', 'would you',
            'give me', 'suggest', 'provide', 'help', 'what', 'how',
            'the', 'is', 'are', 'my', 'me', 'for', 'with', 'this',
            'that', 'want', 'need', 'should', 'meal', 'food', 'diet',
            'healthy', 'recipe', 'breakfast', 'lunch', 'dinner', 'snack',
            'calories', 'protein', 'carbs', 'fat'
        ]
        
        indo_score = sum(1 for kw in indonesian_keywords if kw in text_lower)
        eng_score = sum(1 for kw in english_keywords if kw in text_lower)
        
        print(f"DEBUG Lang Detection: Indo={indo_score}, Eng={eng_score}")
        
        if indo_score > eng_score:
            return 'id'
        else:
            return 'en'  # Default to English
    
    def _is_food_query(self, message: str) -> bool:
        """Check if message is asking about specific foods"""
        food_keywords = [
            'makanan', 'food', 'nutrisi', 'kalori', 'protein',
            'resep', 'recipe', 'bahan', 'ingredient'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in food_keywords)
    
    def _extract_food_terms(self, message: str) -> List[str]:
        """Extract potential food search terms from message"""
        # Simple extraction - can be improved with NLP
        common_foods = [
            'ayam', 'chicken', 'daging', 'beef', 'ikan', 'fish',
            'telur', 'egg', 'nasi', 'rice', 'roti', 'bread',
            'sayur', 'vegetable', 'buah', 'fruit', 'susu', 'milk'
        ]
        
        message_lower = message.lower()
        found_terms = []
        
        for food in common_foods:
            if food in message_lower:
                found_terms.append(food)
        
        return found_terms if found_terms else ['protein']  # Default fallback
    
    def switch_model(self, model_name: str):
        """Switch to different LLM model"""
        self.llm.switch_model(model_name)


# Test function
if __name__ == '__main__':
    print("Testing RAG Service...")
    
    try:
        # Initialize RAG service
        rag = RAGService(model_name='llama3.2:3b')
        
        # Test meal plan generation
        print("\n1. Testing meal plan generation with RAG:")
        user_data = {
            'age': 25,
            'gender': 'male',
            'height': 170,
            'weight': 70,
            'goal': 'turun berat badan',
            'activity_level': 'moderately active',
            'days': 3,
            'preferences': ['halal'],
            'allergies': []
        }
        
        meal_plan = rag.generate_meal_plan(user_data, use_rag=True)
        print(meal_plan)
        
        print("\naœ“ RAG service working!")
        
    except Exception as e:
        print(f"\naŒ Error: {e}")
        import traceback
        traceback.print_exc()



