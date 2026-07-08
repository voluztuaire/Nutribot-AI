"""
Food Database Service
Handles queries to FoodData Central database (Turso/libSQL) for meal planning
"""

import os
from typing import List, Dict, Optional
from contextlib import contextmanager
import libsql_client

TURSO_URL = os.getenv("TURSO_FOODS_DB_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_FOODS_AUTH_TOKEN")


@contextmanager
def get_db_connection():
    client = libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_AUTH_TOKEN)
    try:
        yield client
    finally:
        client.close()


def _rows_to_dicts(result) -> List[Dict]:
    columns = result.columns
    return [dict(zip(columns, row)) for row in result.rows]


def search_foods(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict]:
    with get_db_connection() as conn:
        sql = """
            SELECT DISTINCT f.fdc_id, f.description, f.data_type,
                fc.description as category, f.brand_owner, f.brand_name
            FROM foods f
            LEFT JOIN food_categories fc ON f.food_category_id = fc.id
            WHERE (f.description LIKE ? OR f.brand_name LIKE ?)
        """
        params = [f'%{query}%', f'%{query}%']
        if filters:
            if filters.get('category'):
                sql += " AND fc.description = ?"
                params.append(filters['category'])
            if filters.get('data_type'):
                sql += " AND f.data_type = ?"
                params.append(filters['data_type'])
        sql += f" LIMIT {limit}"
        result = conn.execute(sql, params)
        results = _rows_to_dicts(result)
        for food in results:
            food['nutrients'] = get_food_nutrients(food['fdc_id'])
        return results


def get_food_nutrients(fdc_id: int) -> Dict[str, float]:
    with get_db_connection() as conn:
        result = conn.execute("""
            SELECT n.name as nutrient_name, n.unit_name, fn.amount
            FROM food_nutrients fn
            JOIN nutrients n ON fn.nutrient_id = n.id
            WHERE fn.fdc_id = ?
            AND n.name IN (
                'Energy', 'Protein', 'Total lipid (fat)',
                'Carbohydrate, by difference', 'Fiber, total dietary',
                'Sugars, total including NLEA', 'Sodium, Na',
                'Cholesterol', 'Fatty acids, total saturated'
            )
        """, [fdc_id])
        nutrients = {}
        for row in _rows_to_dicts(result):
            nutrient_name = row['nutrient_name']
            amount = row['amount']
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
    with get_db_connection() as conn:
        result = conn.execute("""
            SELECT f.fdc_id, f.description, f.data_type, fc.description as category,
                f.brand_owner, f.brand_name, f.ingredients, f.serving_size, f.serving_size_unit
            FROM foods f
            LEFT JOIN food_categories fc ON f.food_category_id = fc.id
            WHERE f.fdc_id = ?
        """, [fdc_id])
        rows = _rows_to_dicts(result)
        if not rows:
            return None
        food = rows[0]
        food['nutrients'] = get_food_nutrients(fdc_id)
        food['portions'] = get_food_portions(fdc_id)
        return food


def get_food_portions(fdc_id: int) -> List[Dict]:
    with get_db_connection() as conn:
        result = conn.execute("""
            SELECT portion_description, gram_weight, modifier
            FROM food_portions WHERE fdc_id = ? ORDER BY seq_num
        """, [fdc_id])
        return _rows_to_dicts(result)


def search_by_nutrients(
    min_protein: Optional[float] = None,
    max_calories: Optional[float] = None,
    max_fat: Optional[float] = None,
    max_carbs: Optional[float] = None,
    category: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    with get_db_connection() as conn:
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
        result = conn.execute(sql, params)
        results = _rows_to_dicts(result)
        for food in results:
            food['nutrients'] = get_food_nutrients(food['fdc_id'])
        return results


def get_food_categories() -> List[str]:
    with get_db_connection() as conn:
        result = conn.execute("SELECT DISTINCT description FROM food_categories ORDER BY description")
        return [row['description'] for row in _rows_to_dicts(result)]


def get_random_foods(category: Optional[str] = None, limit: int = 10) -> List[Dict]:
    with get_db_connection() as conn:
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
        result = conn.execute(sql, params)
        results = _rows_to_dicts(result)
        for food in results:
            food['nutrients'] = get_food_nutrients(food['fdc_id'])
        return results