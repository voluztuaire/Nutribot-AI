"""
Model Evaluation Script for NutriBot
=====================================
Evaluates Llama 3.2 3B vs Qwen 2.5 7B on meal planning tasks.

Metrics measured:
- Response Time (seconds)
- Token Count (prompt + completion)
- Characters per second
- Model confidence indicators

Usage:
    python evaluate_models.py
"""

import time
import json
import csv
import os
from datetime import datetime
from ollama import Client

# Configuration
MODELS = [
    "llama3.2:3b",
    "qwen2.5:7b-instruct-q5_K_M"
]

# Test cases - various meal planning prompts
TEST_CASES = [
    # English prompts
    {
        "id": 1,
        "prompt": "Can you suggest 4 healthy meals for my diet?",
        "language": "en",
        "category": "meal_suggestion"
    },
    {
        "id": 2,
        "prompt": "What is a good breakfast for weight loss?",
        "language": "en",
        "category": "meal_suggestion"
    },
    {
        "id": 3,
        "prompt": "Create a 3-day meal plan for muscle gain with high protein",
        "language": "en",
        "category": "meal_plan"
    },
    {
        "id": 4,
        "prompt": "How many calories are in grilled chicken breast?",
        "language": "en",
        "category": "nutrition_info"
    },
    {
        "id": 5,
        "prompt": "Give me a healthy snack recipe with less than 200 calories",
        "language": "en",
        "category": "recipe"
    },
    # Indonesian prompts
    {
        "id": 6,
        "prompt": "Tolong berikan saya 4 menu makanan sehat untuk diet",
        "language": "id",
        "category": "meal_suggestion"
    },
    {
        "id": 7,
        "prompt": "Apa sarapan yang bagus untuk menurunkan berat badan?",
        "language": "id",
        "category": "meal_suggestion"
    },
    {
        "id": 8,
        "prompt": "Buatkan rencana makan 3 hari untuk menambah massa otot",
        "language": "id",
        "category": "meal_plan"
    },
    {
        "id": 9,
        "prompt": "Berapa kalori dalam nasi goreng?",
        "language": "id",
        "category": "nutrition_info"
    },
    {
        "id": 10,
        "prompt": "Berikan resep camilan sehat dengan kurang dari 200 kalori",
        "language": "id",
        "category": "recipe"
    }
]

# System prompt for NutriBot
SYSTEM_PROMPT = """You are NutriBot, a professional meal planner assistant.

CRITICAL LANGUAGE RULE:
- IF USER SPEAKS ENGLISH a†’ YOU MUST REPLY IN ENGLISH.
- IF USER SPEAKS INDONESIAN a†’ YOU MUST REPLY IN INDONESIAN.

You ONLY answer questions about:
- Meal planning & Diet
- Nutrition & Food health
- Healthy recipes
- Fitness (diet context only)

Keep responses concise and helpful."""


def evaluate_single_prompt(client: Client, model: str, prompt: str) -> dict:
    """Evaluate a single prompt on a model and return metrics."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    # Measure response time
    start_time = time.time()
    
    try:
        response = client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.7,
                "num_predict": 512  # Max tokens
            }
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Extract metrics from response
        reply = response.get('message', {}).get('content', '')
        
        # Token counts (if available)
        prompt_tokens = response.get('prompt_eval_count', 0)
        completion_tokens = response.get('eval_count', 0)
        total_tokens = prompt_tokens + completion_tokens
        
        # Calculate characters per second
        chars_per_sec = len(reply) / response_time if response_time > 0 else 0
        
        # Tokens per second
        tokens_per_sec = completion_tokens / response_time if response_time > 0 else 0
        
        return {
            "success": True,
            "response_time": round(response_time, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "response_length": len(reply),
            "chars_per_sec": round(chars_per_sec, 2),
            "tokens_per_sec": round(tokens_per_sec, 2),
            "response_preview": reply[:200] + "..." if len(reply) > 200 else reply,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response_time": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "response_length": 0,
            "chars_per_sec": 0,
            "tokens_per_sec": 0,
            "response_preview": "",
            "error": str(e)
        }


def run_evaluation():
    """Run full evaluation across all models and test cases."""
    
    print("=" * 60)
    print("NutriBot Model Evaluation")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Models: {', '.join(MODELS)}")
    print(f"Test Cases: {len(TEST_CASES)}")
    print("=" * 60)
    
    # Connect to Ollama
    client = Client(host='http://localhost:11434')
    
    # Results storage
    all_results = []
    model_summaries = {}
    
    for model in MODELS:
        print(f"\nðŸ“Š Evaluating: {model}")
        print("-" * 40)
        
        model_results = []
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"  [{i}/{len(TEST_CASES)}] {test_case['prompt'][:40]}...", end="", flush=True)
            
            result = evaluate_single_prompt(client, model, test_case["prompt"])
            
            # Add test case info
            result["model"] = model
            result["test_id"] = test_case["id"]
            result["prompt"] = test_case["prompt"]
            result["language"] = test_case["language"]
            result["category"] = test_case["category"]
            
            model_results.append(result)
            all_results.append(result)
            
            if result["success"]:
                print(f" aœ“ {result['response_time']}s, {result['total_tokens']} tokens")
            else:
                print(f" aœ— Error: {result['error']}")
        
        # Calculate model summary
        successful = [r for r in model_results if r["success"]]
        if successful:
            model_summaries[model] = {
                "total_tests": len(model_results),
                "successful": len(successful),
                "failed": len(model_results) - len(successful),
                "avg_response_time": round(sum(r["response_time"] for r in successful) / len(successful), 3),
                "avg_tokens": round(sum(r["total_tokens"] for r in successful) / len(successful), 1),
                "avg_tokens_per_sec": round(sum(r["tokens_per_sec"] for r in successful) / len(successful), 2),
                "avg_chars_per_sec": round(sum(r["chars_per_sec"] for r in successful) / len(successful), 2),
            }
    
    # Export results to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"evaluation_results_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        if all_results:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
    
    print(f"\nðŸ“ Results saved to: {csv_filename}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    
    for model, summary in model_summaries.items():
        print(f"\nðŸ¤– {model}")
        print(f"   Tests: {summary['successful']}/{summary['total_tests']} passed")
        print(f"   Avg Response Time: {summary['avg_response_time']}s")
        print(f"   Avg Tokens: {summary['avg_tokens']}")
        print(f"   Avg Tokens/sec: {summary['avg_tokens_per_sec']}")
        print(f"   Avg Chars/sec: {summary['avg_chars_per_sec']}")
    
    # Export summary to JSON
    summary_filename = f"evaluation_summary_{timestamp}.json"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "models": MODELS,
            "test_cases_count": len(TEST_CASES),
            "summaries": model_summaries,
            "detailed_results": all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nðŸ“ Summary saved to: {summary_filename}")
    print("\naœ… Evaluation complete!")
    
    return model_summaries, all_results


if __name__ == "__main__":
    run_evaluation()



