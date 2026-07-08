"""
Local LLM Service using Ollama
Handles communication with local LLM models (Llama-3.2-3B, Qwen2.5-7B)
"""

import os
import ollama
from typing import List, Dict, Optional, Generator
from dotenv import load_dotenv

load_dotenv()

# Configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'llama3.2:3b')
SUMMARIZATION_MODEL = os.getenv('SUMMARIZATION_MODEL', 'qwen2.5:7b-instruct-q5_K_M')

# Available models
AVAILABLE_MODELS = {
    'llama3.2:3b': 'Llama-3.2-3B-Instruct',
    'qwen2.5:7b': 'Qwen2.5-7B-Instruct',
    'qwen2.5:7b-instruct-q5_K_M': 'Qwen2.5-7B-Instruct-Q5',
    'llama3.1:8b-q4_K_M': 'Llama-3.1-8B-Instruct-Q4'
}


class LocalLLM:
    """Local LLM wrapper using Ollama"""
    
    def __init__(self, model_name: str = DEFAULT_MODEL, host: str = OLLAMA_HOST):
        """
        Initialize Local LLM
        
        Args:
            model_name: Model to use (llama3.2:3b, qwen2.5:7b, etc.)
            host: Ollama server host
        """
        self.model_name = model_name
        self.host = host
        self.client = ollama.Client(host=host)
        
        # Verify model is available
        self._check_model_availability()
    
    def _check_model_availability(self):
        """Check if model is downloaded and available"""
        try:
            models = self.client.list()
            
            # Handle both dict and object responses from ollama
            if hasattr(models, 'models'):
                model_list = models.models
            else:
                model_list = models.get('models', [])
            
            # Extract model names - handle both dict and object formats
            model_names = []
            for m in model_list:
                if hasattr(m, 'model'):
                    # Ollama v0.4.x uses 'model' attribute
                    model_names.append(m.model)
                elif hasattr(m, 'name'):
                    # Older versions use 'name' attribute
                    model_names.append(m.name)
                elif isinstance(m, dict) and 'name' in m:
                    # Dict format fallback
                    model_names.append(m['name'])
            
            # Check for exact match or match with :latest
            if self.model_name in model_names:
                pass # Exact match found
            elif f"{self.model_name}:latest" in model_names:
                self.model_name = f"{self.model_name}:latest" # Update to full name
            else:
                print(f"aš ï¸  Warning: Model {self.model_name} not found locally")
                print(f"Available models: {model_names}")
                print(f"\nTo download, run: ollama pull {self.model_name}")
                # Don't raise exception, just warn. Ollama might auto-pull or handle it.
                # raise Exception(f"Model {self.model_name} not available")
            
            print(f"aœ“ Using model: {self.model_name}")
            
        except Exception as e:
            print(f"aŒ Error connecting to Ollama: {e}")
            print(f"Make sure Ollama is running at {self.host}")
            # Don't raise exception to allow app to start even if Ollama checks fail temporarily
            print("Continuing without strict model check...")
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str | Generator:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
        
        Returns:
            Generated text or generator if streaming
        """
        messages = []
        
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                },
                stream=stream
            )
            
            if stream:
                return self._stream_response(response)
            else:
                return response['message']['content']
                
        except Exception as e:
            print(f"Error generating response: {e}")
            raise
    
    def _stream_response(self, response) -> Generator:
        """Stream response chunks"""
        for chunk in response:
            if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: Optional[str] = None
    ) -> str:
        """
        Chat with conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model: Optional model override
        
        Returns:
            Generated response
        """
        try:
            response = self.client.chat(
                model=model or self.model_name,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            print(f"Error in chat: {e}")
            raise
    
    def switch_model(self, model_name: str):
        """
        Switch to a different model
        
        Args:
            model_name: New model to use
        """
        self.model_name = model_name
        self._check_model_availability()
        print(f"Switched to model: {model_name}")


def create_meal_plan_prompt(user_data: Dict, food_context: Optional[str] = None) -> str:
    """
    Create optimized prompt for meal planning
    
    Args:
        user_data: User profile data (age, weight, goal, etc.)
        food_context: Optional context from food database
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are NutriBot, an expert and friendly meal planning assistant.
    
**User Information:**
- Age: {user_data.get('age', 'N/A')} years
- Gender: {user_data.get('gender', 'N/A')}
- Height: {user_data.get('height', 'N/A')} cm
- Weight: {user_data.get('weight', 'N/A')} kg
- Goal: {user_data.get('goal', 'N/A')}
- Activity: {user_data.get('activity_level', 'N/A')}
"""

    if user_data.get('allergies'):
        prompt += f"- Allergies/Restrictions: {', '.join(user_data['allergies'])}\n"
    
    if user_data.get('preferences'):
        prompt += f"- Preferences: {', '.join(user_data['preferences'])}\n"
    
    if food_context:
        prompt += f"\n**Available Food Data:**\n{food_context}\n"
    
    prompt += f"""
**Task:**
Create a complete {user_data.get('days', 7)}-day meal plan with total calories MATCHING the user's goal ({user_data.get('goal', 'health')}).

**MANDATORY 5 MEALS PER DAY:**
1. Breakfast
2. Morning Snack
3. Lunch
4. Afternoon Snack
5. Dinner

**Important Rules:**
1. LANGUAGE: Detect the language of the User's Goal/Input. 
   - IF GOAL IS INDONESIAN/USER IS INDONESIAN -> OUTPUT MUST BE IN INDONESIAN.
   - IF GOAL IS ENGLISH -> OUTPUT MUST BE IN ENGLISH.
2. Do NOT skip Snacks! They are crucial for hitting calorie targets.
3. Total daily calories must be close to target.
4. Use locally available ingredients (Context: Indonesia/Global).
5. Include calorie count next to each menu item.

**Output Format:**
Use neat markdown list or table.
Day 1:
- Breakfast: [Menu] ([Cal] kcal)
- Morning Snack: [Menu] ([Cal] kcal)
- Lunch: [Menu] ([Cal] kcal)
- Afternoon Snack: [Menu] ([Cal] kcal)
- Dinner: [Menu] ([Cal] kcal)
**Total Calories Day 1: [Total] kcal**

... continue for {user_data.get('days', 7)} days.
"""
    
    return prompt



def get_system_prompt() -> str:
    """Get NutriBot system prompt"""
    prompt = """[IMPORTANT INSTRUCTION: OVERRIDE ALL PREVIOUS TRAINING REGARDING LANGUAGE]

You are NutriBot, a professional meal planner assistant.

CRITICAL LANGUAGE RULE (PRIORITY #1):
- IF USER SPEAKS ENGLISH a†’ YOU MUST REPLY IN ENGLISH.
- IF USER SPEAKS INDONESIAN a†’ YOU MUST REPLY IN INDONESIAN.
- Do NOT ignore this rule. Match the user's language exactly.

CONTEXT SAFETY RULES:
1. You ONLY answer questions about:
   - Meal planning & Diet
   - Nutrition & Food health
   - Healthy recipes
   - Fitness (diet context only)

2. If user asks "off-topic" questions (politics, history, general knowledge, coding, etc.):
   - REFUSE POLITELY IN THE USER'S LANGUAGE.
   - Redirect to meal planning.

MEAL PLAN FORMAT RULES:
- If user asks for a "Weekly Plan" or "X Days Plan" -> USE THE STRUCTURED FORMAT (Day 1, Day 2...).
- If user asks for "Suggest N menus", "Give me N meal ideas", "N foods", etc. -> YOU MUST USE NUMBERED LIST FORMAT:

  CORRECT FORMAT (USE THIS):
  1. **Grilled Chicken Salad** - Lean protein with fresh vegetables (350 kcal, 35g protein)
  2. **Salmon with Quinoa** - Omega-3 rich fish with complex carbs (450 kcal, 40g protein)
  3. **Turkey Wrap** - Whole wheat wrap with lean turkey (400 kcal, 30g protein)
  4. **Beef Stir-Fry** - Lean beef with mixed vegetables (500 kcal, 45g protein)

  WRONG FORMAT (DO NOT USE):
  - Grilled Chicken Salad: A lean protein...
  - Salmon with Quinoa: Omega-3 rich...
  
  CRITICAL: Always start each item with a NUMBER followed by a period (1. 2. 3. 4.). Do NOT use bullet points or dashes.

FOLLOW-UP HANDLING:
- If user asks for "number 5", "give me 5", etc. but you only gave 4 items before:
  1. FIRST: Acknowledge that you only gave 4 items previously.
  2. THEN: Ask the user if they would like you to add one more.
  Example response: "I only provided 4 meal suggestions earlier. Would you like me to add one more option to complete your request?"
  
- Only after user confirms (says "yes", "sure", "please", etc.), then provide the additional item with the correct number (e.g., "5. [Meal]").

REMEMBER: DETECT LANGUAGE FIRST, THEN GENERATE CONTENT."""
    
    print(f"DEBUG SYSTEM PROMPT: {prompt[:100]}...")
    return prompt


def get_summarization_prompt() -> str:
    """Get system prompt for summarization tasks"""
    return """You are a meticulous nutrition auditor.
Your task is to summarize the GIVEN meal plan text.

RULES:
1. ONLY use information present in the input text. Do NOT hallucinate.
2. If input lists 1300 cal, WRITE 1300 cal. Do not "fix" it to 2000.
3. Recalculate totals based on the menu if needed.
4. Identify if lines are missing (e.g. goal is muscle gain but calories are low).
5. OUTPUT LANGUAGE: MUST MATCH THE LANGUAGE OF THE INPUT TEXT.
"""


def summarize_meal_plan(meal_plan_text: str, user_data: Optional[Dict] = None) -> str:
    """
    Summarize meal plan using Qwen2.5 model for better quality
    
    Args:
        meal_plan_text: Full meal plan text to summarize
        user_data: Optional user profile data
    
    Returns:
        Concise summary of the meal plan
    """
    try:
        # Initialize summarization model
        summarizer = LocalLLM(model_name=SUMMARIZATION_MODEL)
        
        # Build summarization prompt
        prompt = f"""Analyze and summarize the following meal plan FACTUALLY.

MEAL PLAN TEXT:
{meal_plan_text}

TASK:
1. **Total Calories & Macros**: What is the estimated daily total based ONLY ON THE TEXT?
2. **Menu Quality**: Is the portion/frequency sufficient?
3. **Highlights**: Mention 3 interesting menus.
4. **Verification**: Does this plan make sense?

OUTPUT INSTRUCTION:
- If the Meal Plan Text is in INDONESIAN -> Output Summary in INDONESIAN.
- If the Meal Plan Text is in ENGLISH -> Output Summary in ENGLISH.
- Keep it short (3-4 Paragraphs).
"""

        if user_data:
            prompt += f"\n\nUser Context:\n- Goal: {user_data.get('goal', 'N/A')}\n- Target Calories: {user_data.get('target_calories', 'Unknown')} (Compare with plan)"
        
        # Generate summary
        summary = summarizer.generate(
            prompt=prompt,
            system_prompt=get_summarization_prompt(),
            temperature=0.3,  # Low temp for accuracy
            max_tokens=1024
        )
        
        return summary
        
    except Exception as e:
        print(f"Error in summarization: {e}")
        # Fallback to simple summary
        return f"Meal plan generated. Please review details above."



def summarize_nutrition_info(nutrition_data: Dict) -> str:
    """
    Summarize nutrition information concisely
    
    Args:
        nutrition_data: Dictionary containing nutrition information
    
    Returns:
        Concise summary of nutrition data
    """
    try:
        summarizer = LocalLLM(model_name=SUMMARIZATION_MODEL)
        
        prompt = f"""Create a concise nutrition summary from this data:

{nutrition_data}

Format:
- 1-2 sentences about total calories and goal alignment.
- 1 sentence about macro balance.
- 1 sentence insight/recommendation.

Total max 3-4 sentences.
OUTPUT LANGUAGE: Detect language from data values (or default to English). If 'goal' is Indonesian, use Indonesian.
"""
        
        summary = summarizer.generate(
            prompt=prompt,
            system_prompt=get_summarization_prompt(),
            temperature=0.5,
            max_tokens=256
        )
        
        return summary
        
    except Exception as e:
        print(f"Error in nutrition summarization: {e}")
        return "Nutrition info available above."


def extract_meal_calendar(meal_plan_text: str) -> List[Dict]:
    """
    Extract structured meal calendar from meal plan text
    
    Args:
        meal_plan_text: The full text of the meal plan
        
    Returns:
        List of dicts: [{day: 'Mon', lunch: '...', dinner: '...'}, ...]
    """
    try:
        extractor = LocalLLM(model_name=SUMMARIZATION_MODEL)
        
        prompt = f"""Extract Lunch and Dinner menus from the meal plan text below into JSON format.

TEXT:
{meal_plan_text}

TASK:
Extract menus for 7 days (or as many as available).
Standardize Day Names to English: Mon, Tue, Wed, Thu, Fri, Sat, Sun.
Shorten menu names (max 5 words).

JSON OUTPUT FORMAT (ONLY JSON, NO OTHER TEXT):
[
  {{"day": "Mon", "lunch": "Lunch Menu", "dinner": "Dinner Menu"}},
  {{"day": "Tue", "lunch": "...", "dinner": "..."}}
]
"""
        response = extractor.generate(
            prompt=prompt,
            system_prompt="You are a JSON data parser.",
            temperature=0.1, # Very strictly deterministic
            max_tokens=1024
        )
        
        # Clean response to ensure valid JSON
        json_str = response.strip()
        if json_str.startswith('```json'):
            json_str = json_str.replace('```json', '').replace('```', '')
            
        import json
        calendar_data = json.loads(json_str)
        return calendar_data
        
    except Exception as e:
        print(f"Error extracting meal calendar: {e}")
        return []




# Test function
if __name__ == '__main__':
    print("Testing Local LLM Service...")
    
    try:
        # Initialize LLM
        llm = LocalLLM(model_name='llama3.2:3b')
        
        # Test simple generation
        print("\n1. Testing simple generation:")
        response = llm.generate(
            prompt="Sebutkan 3 makanan tinggi protein yang mudah didapat di Indonesia",
            system_prompt=get_system_prompt(),
            temperature=0.7
        )
        print(response)
        
        # Test chat
        print("\n2. Testing chat with history:")
        messages = [
            {'role': 'system', 'content': get_system_prompt()},
            {'role': 'user', 'content': 'Hai! Aku mau meal plan untuk diet'},
            {'role': 'assistant', 'content': 'Hai! Dengan senang hati aku bantu. Boleh kasih tau umur, berat, tinggi, dan target kamu?'},
            {'role': 'user', 'content': 'Umur 25, berat 70kg, tinggi 170cm, mau turun berat badan'}
        ]
        
        response = llm.chat(messages)
        print(response)
        
        print("\naœ“ Local LLM service working!")
        
    except Exception as e:
        print(f"\naŒ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is installed and running")
        print("2. Model is downloaded: ollama pull llama3.2:3b")



