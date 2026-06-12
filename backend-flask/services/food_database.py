"""
Food Database Service
Handles queries to FoodData Central SQLite database for meal planning
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'nutribot_foods.db')


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


def search_foods(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict]:
    """
    Search foods by name/description with optional filters
    
    Args:
        query: Search term for food name/description
        filters: Optional filters (max_calories, min_protein, category, etc.)
        limit: Maximum number of results
    
    Returns:
        List of food items with basic nutritional info
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Base query
        sql = """
            SELECT DISTINCT
                f.fdc_id,
                f.description,
                f.data_type,
                fc.description as category,
                f.brand_owner,
                f.brand_name
            FROM foods f
            LEFT JOIN food_categories fc ON f.food_category_id = fc.id
            WHERE (f.description LIKE ? OR f.brand_name LIKE ?)
        """
        params = [f'%{query}%', f'%{query}%']
        
        # Apply filters
        if filters:
            if filters.get('category'):
                sql += " AND fc.description = ?"
                params.append(filters['category'])
            
            if filters.get('data_type'):
                sql += " AND f.data_type = ?"
                params.append(filters['data_type'])
        
        sql += f" LIMIT {limit}"
        
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Enrich with nutritional data
        for food in results:
            food['nutrients'] = get_food_nutrients(food['fdc_id'])
        
        return results


def get_food_nutrients(fdc_id: int) -> Dict[str, float]:
    """
    Get complete nutritional information for a food item
    
    Args:
        fdc_id: FoodData Central ID
    
    Returns:
        Dictionary of nutrient_name: amount
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                n.name as nutrient_name,
                n.unit_name,
                fn.amount
            FROM food_nutrients fn
            JOIN nutrients n ON fn.nutrient_id = n.id
            WHERE fn.fdc_id = ?
            AND n.name IN (
                'Energy', 'Protein', 'Total lipid (fat)', 
                'Carbohydrate, by difference', 'Fiber, total dietary',
                'Sugars, total including NLEA', 'Sodium, Na',
                'Cholesterol', 'Fatty acids, total saturated'
            )
        """, (fdc_id,))
        
        nutrients = {}
        for row in cursor.fetchall():
            nutrient_name = row['nutrient_name']
            amount = row['amount']
            unit = row['unit_name']
            
            # Normalize nutrient names
            if 'Energy' in nutrient_name:
                nutrients['calories'] = amount
            elif 'Protein' in nutrient_name:
                nutrients['protein'] = amount
            elif 'lipid' in nutrient_name or 'fat' in nutrient_name.lower():
                nutrients['fat'] = amount
            elif 'Carbohydrate' in nutrient_name:
                nutrients['carbs'] = amount
            elif 'Fiber' in nutrient_name:
                nutrients['fiber'] = amount
            elif 'Sugar' in nutrient_name:
                nutrients['sugar'] = amount
            elif 'Sodium' in nutrient_name:
                nutrients['sodium'] = amount
            elif 'Cholesterol' in nutrient_name:
                nutrients['cholesterol'] = amount
            elif 'saturated' in nutrient_name.lower():
                nutrients['saturated_fat'] = amount
        
        return nutrients


def get_food_details(fdc_id: int) -> Optional[Dict]:
    """
    Get complete details for a specific food item
    
    Args:
        fdc_id: FoodData Central ID
    
    Returns:
        Complete food information including all nutrients
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                f.fdc_id,
                f.description,
                f.data_type,
                fc.description as category,
                f.brand_owner,
                f.brand_name,
                f.ingredients,
                f.serving_size,
                f.serving_size_unit
            FROM foods f
            LEFT JOIN food_categories fc ON f.food_category_id = fc.id
            WHERE f.fdc_id = ?
        """, (fdc_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        food = dict(row)
        food['nutrients'] = get_food_nutrients(fdc_id)
        food['portions'] = get_food_portions(fdc_id)
        
        return food


def get_food_portions(fdc_id: int) -> List[Dict]:
    """
    Get portion/serving size information
    
    Args:
        fdc_id: FoodData Central ID
    
    Returns:
        List of portion descriptions with gram weights
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                portion_description,
                gram_weight,
                modifier
            FROM food_portions
            WHERE fdc_id = ?
            ORDER BY seq_num
        """, (fdc_id,))
        
        return [dict(row) for row in cursor.fetchall()]


def search_by_nutrients(
    min_protein: Optional[float] = None,
    max_calories: Optional[float] = None,
    max_fat: Optional[float] = None,
    max_carbs: Optional[float] = None,
    category: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Search foods by nutritional criteria
    
    Args:
        min_protein: Minimum protein in grams
        max_calories: Maximum calories
        max_fat: Maximum fat in grams
        max_carbs: Maximum carbs in grams
        category: Food category filter
        limit: Maximum results
    
    Returns:
        List of matching foods
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build dynamic query
        sql = """
            SELECT DISTINCT f.fdc_id, f.description, f.data_type
            FROM foods f
            LEFT JOIN food_categories fc ON f.food_category_id = fc.id
        """
        
        where_clauses = []
        params = []
        
        if min_protein is not None:
            sql += """
                JOIN food_nutrients fn_protein ON f.fdc_id = fn_protein.fdc_id
                JOIN nutrients n_protein ON fn_protein.nutrient_id = n_protein.id
            """
            where_clauses.append("n_protein.name LIKE '%Protein%' AND fn_protein.amount >= ?")
            params.append(min_protein)
        
        if max_calories is not None:
            sql += """
                JOIN food_nutrients fn_cal ON f.fdc_id = fn_cal.fdc_id
                JOIN nutrients n_cal ON fn_cal.nutrient_id = n_cal.id
            """
            where_clauses.append("n_cal.name LIKE '%Energy%' AND fn_cal.amount <= ?")
            params.append(max_calories)
        
        if category:
            where_clauses.append("fc.description = ?")
            params.append(category)
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        sql += f" LIMIT {limit}"
        
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Enrich with nutrients
        for food in results:
            food['nutrients'] = get_food_nutrients(food['fdc_id'])
        
        return results


def get_food_categories() -> List[str]:
    """Get list of all food categories"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT description FROM food_categories ORDER BY description")
        return [row['description'] for row in cursor.fetchall()]


def get_random_foods(category: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get random food items for variety in meal plans
    
    Args:
        category: Optional category filter
        limit: Number of random items
    
    Returns:
        List of random foods
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        sql = """
            SELECT f.fdc_id, f.description, f.data_type, fc.description as category
            FROM foods f
            LEFT JOIN food_categories fc ON f.food_category_id = fc.id
        """
        
        params = []
        if category:
            sql += " WHERE fc.description = ?"
            params.append(category)
        
        sql += f" ORDER BY RANDOM() LIMIT {limit}"
        
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        for food in results:
            food['nutrients'] = get_food_nutrients(food['fdc_id'])
        
        return results


# Test function
if __name__ == '__main__':
    print("Testing Food Database Service...")
    
    # Test search
    print("\n1. Searching for 'chicken breast':")
    results = search_foods('chicken breast', limit=3)
    for food in results:
        print(f"  - {food['description']}")
        print(f"    Nutrients: {food.get('nutrients', {})}")
    
    # Test nutrient search
    print("\n2. High protein, low calorie foods:")
    results = search_by_nutrients(min_protein=20, max_calories=200, limit=5)
    for food in results:
        print(f"  - {food['description']}")
        print(f"    Nutrients: {food.get('nutrients', {})}")
    
    # Test categories
    print("\n3. Food categories:")
    categories = get_food_categories()
    print(f"  Found {len(categories)} categories")
    print(f"  Sample: {categories[:5]}")



