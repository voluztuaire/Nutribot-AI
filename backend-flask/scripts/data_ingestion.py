"""
Data Ingestion Script for FoodData Central
Processes CSV files and creates optimized SQLite database for NutriBot
"""

import sqlite3
import csv
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Paths
# Auto-detect any "FoodData_Central_csv_*" folder inside backend-flask/dataset/.
# Override with env var: NUTRIBOT_DATASET_DIR=/absolute/path/to/folder
DATASET_ROOT = Path(__file__).parent.parent / 'dataset'
_env_dir = os.environ.get('NUTRIBOT_DATASET_DIR')
if _env_dir:
    DATASET_DIR = Path(_env_dir)
else:
    _candidates = sorted(DATASET_ROOT.glob('FoodData_Central_csv_*'))
    DATASET_DIR = _candidates[-1] if _candidates else DATASET_ROOT / 'FoodData_Central_csv'
DB_PATH = DATASET_ROOT / 'nutribot_foods.db'

# CSV files to process
CSV_FILES = {
    'food': 'food.csv',
    'nutrient': 'nutrient.csv',
    'food_nutrient': 'food_nutrient.csv',
    'food_category': 'food_category.csv',
    'food_portion': 'food_portion.csv',
    'branded_food': 'branded_food.csv',
}


def create_database_schema(conn):
    """Create optimized database schema"""
    cursor = conn.cursor()
    
    print("Creating database schema...")
    
    # Foods table (main table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            fdc_id INTEGER PRIMARY KEY,
            data_type TEXT,
            description TEXT NOT NULL,
            food_category_id INTEGER,
            publication_date TEXT,
            brand_owner TEXT,
            brand_name TEXT,
            ingredients TEXT,
            serving_size REAL,
            serving_size_unit TEXT,
            household_serving_fulltext TEXT
        )
    """)
    
    # Nutrients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            unit_name TEXT,
            nutrient_nbr TEXT,
            rank REAL
        )
    """)
    
    # Food nutrients (junction table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_nutrients (
            id INTEGER PRIMARY KEY,
            fdc_id INTEGER,
            nutrient_id INTEGER,
            amount REAL,
            data_points INTEGER,
            derivation_id INTEGER,
            min REAL,
            max REAL,
            median REAL,
            FOREIGN KEY (fdc_id) REFERENCES foods(fdc_id),
            FOREIGN KEY (nutrient_id) REFERENCES nutrients(id)
        )
    """)
    
    # Food categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_categories (
            id INTEGER PRIMARY KEY,
            code TEXT,
            description TEXT
        )
    """)
    
    # Food portions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_portions (
            id INTEGER PRIMARY KEY,
            fdc_id INTEGER,
            seq_num INTEGER,
            amount REAL,
            measure_unit_id INTEGER,
            portion_description TEXT,
            modifier TEXT,
            gram_weight REAL,
            data_points INTEGER,
            FOREIGN KEY (fdc_id) REFERENCES foods(fdc_id)
        )
    """)
    
    # Create indexes for performance
    print("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_foods_description ON foods(description)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(food_category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_foods_brand ON foods(brand_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_nutrients_fdc ON food_nutrients(fdc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_nutrients_nutrient ON food_nutrients(nutrient_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_portions_fdc ON food_portions(fdc_id)")
    
    conn.commit()
    print("Schema created successfully!")


def import_csv_file(conn, table_name, csv_filename, row_processor=None, batch_size=1000):
    """
    Import CSV file into database table
    
    Args:
        conn: Database connection
        table_name: Target table name
        csv_filename: CSV file to import
        row_processor: Optional function to process each row
        batch_size: Number of rows to insert at once
    """
    csv_path = DATASET_DIR / csv_filename
    
    if not csv_path.exists():
        print(f"aš ï¸  Warning: {csv_filename} not found, skipping...")
        return
    
    print(f"\nImporting {csv_filename} into {table_name}...")
    
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        
        # Get column names from CSV
        csv_columns = reader.fieldnames
        
        # Get table columns from database to filter excess CSV columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_columns_info = cursor.fetchall()
        table_columns = [info[1] for info in table_columns_info]
        
        # Intersect columns
        valid_columns = [col for col in csv_columns if col in table_columns]
        
        # Prepare insert statement
        placeholders = ','.join(['?' for _ in valid_columns])
        insert_sql = f"INSERT OR IGNORE INTO {table_name} ({','.join(valid_columns)}) VALUES ({placeholders})"
        
        batch = []
        row_count = 0
        
        for row in reader:
            # Process row if processor provided
            if row_processor:
                row = row_processor(row)
                if row is None:
                    continue
            
            # Convert row to tuple of values (only for valid columns)
            values = tuple(row.get(col, None) for col in valid_columns)
            batch.append(values)
            row_count += 1
            
            # Insert batch
            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                batch = []
                print(f"  Processed {row_count:,} rows...", end='\r')
        
        # Insert remaining rows
        if batch:
            cursor.executemany(insert_sql, batch)
            conn.commit()
        
        print(f"  aœ“ Imported {row_count:,} rows from {csv_filename}")


def process_food_row(row):
    """Process food.csv row - filter and clean data"""
    # Skip if no description
    if not row.get('description'):
        return None
    
    # Only keep relevant data types
    data_type = row.get('data_type', '')
    if data_type not in ['branded_food', 'sr_legacy_food', 'survey_fndds_food', 'foundation_food']:
        return None
    
    return row


def process_branded_food_row(row):
    """Process branded_food.csv and merge into foods table"""
    # This will be handled separately to enrich the foods table
    return row


def enrich_foods_with_branded_data(conn):
    """Add branded food data to foods table"""
    csv_path = DATASET_DIR / 'branded_food.csv'
    
    if not csv_path.exists():
        print("aš ï¸  Warning: branded_food.csv not found, skipping enrichment...")
        return
    
    print("\nEnriching foods with branded data...")
    
    cursor = conn.cursor()
    update_count = 0
    
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            fdc_id = row.get('fdc_id')
            if not fdc_id:
                continue
            
            cursor.execute("""
                UPDATE foods 
                SET brand_owner = ?,
                    brand_name = ?,
                    ingredients = ?,
                    serving_size = ?,
                    serving_size_unit = ?,
                    household_serving_fulltext = ?
                WHERE fdc_id = ?
            """, (
                row.get('brand_owner'),
                row.get('brand_name'),
                row.get('ingredients'),
                row.get('serving_size'),
                row.get('serving_size_unit'),
                row.get('household_serving_fulltext'),
                fdc_id
            ))
            
            update_count += 1
            if update_count % 1000 == 0:
                conn.commit()
                print(f"  Updated {update_count:,} foods...", end='\r')
        
        conn.commit()
        print(f"  aœ“ Enriched {update_count:,} foods with branded data")


def create_optimized_views(conn):
    """Create views for common queries"""
    cursor = conn.cursor()
    
    print("\nCreating optimized views...")
    
    # View for foods with basic macros
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS foods_with_macros AS
        SELECT 
            f.fdc_id,
            f.description,
            f.data_type,
            f.brand_name,
            fc.description as category,
            MAX(CASE WHEN n.name LIKE '%Energy%' THEN fn.amount END) as calories,
            MAX(CASE WHEN n.name LIKE '%Protein%' THEN fn.amount END) as protein,
            MAX(CASE WHEN n.name LIKE '%lipid%' OR n.name LIKE '%fat%' THEN fn.amount END) as fat,
            MAX(CASE WHEN n.name LIKE '%Carbohydrate%' THEN fn.amount END) as carbs,
            MAX(CASE WHEN n.name LIKE '%Fiber%' THEN fn.amount END) as fiber
        FROM foods f
        LEFT JOIN food_categories fc ON f.food_category_id = fc.id
        LEFT JOIN food_nutrients fn ON f.fdc_id = fn.fdc_id
        LEFT JOIN nutrients n ON fn.nutrient_id = n.id
        GROUP BY f.fdc_id
    """)
    
    conn.commit()
    print("  aœ“ Views created successfully!")


def print_database_stats(conn):
    """Print statistics about the imported data"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    # Count foods
    cursor.execute("SELECT COUNT(*) FROM foods")
    food_count = cursor.fetchone()[0]
    print(f"Total Foods: {food_count:,}")
    
    # Count by data type
    cursor.execute("SELECT data_type, COUNT(*) FROM foods GROUP BY data_type")
    print("\nFoods by Type:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]:,}")
    
    # Count nutrients
    cursor.execute("SELECT COUNT(*) FROM nutrients")
    nutrient_count = cursor.fetchone()[0]
    print(f"\nTotal Nutrients: {nutrient_count:,}")
    
    # Count food-nutrient relationships
    cursor.execute("SELECT COUNT(*) FROM food_nutrients")
    fn_count = cursor.fetchone()[0]
    print(f"Total Food-Nutrient Records: {fn_count:,}")
    
    # Count categories
    cursor.execute("SELECT COUNT(*) FROM food_categories")
    cat_count = cursor.fetchone()[0]
    print(f"Total Categories: {cat_count:,}")
    
    # Database size
    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)  # MB
    print(f"\nDatabase Size: {db_size:.2f} MB")
    
    print("="*60)


def main():
    """Main ingestion process"""
    print("="*60)
    print("FoodData Central Data Ingestion")
    print("="*60)
    
    # Check if dataset directory exists
    if not DATASET_DIR.exists():
        print(f"aŒ Error: Dataset directory not found at {DATASET_DIR}")
        print("Please ensure FoodData_Central_csv_2025-12-18 is in the dataset folder")
        return
    
    # Remove existing database
    if DB_PATH.exists():
        print(f"\naš ï¸  Removing existing database at {DB_PATH}")
        os.remove(DB_PATH)
    
    # Create database connection
    print(f"\nCreating database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Create schema
        create_database_schema(conn)
        
        # Import data in order (respecting foreign keys)
        import_csv_file(conn, 'food_categories', 'food_category.csv')
        import_csv_file(conn, 'nutrients', 'nutrient.csv')
        import_csv_file(conn, 'foods', 'food.csv', row_processor=process_food_row)
        import_csv_file(conn, 'food_nutrients', 'food_nutrient.csv', batch_size=5000)
        import_csv_file(conn, 'food_portions', 'food_portion.csv')
        
        # Enrich with branded data
        enrich_foods_with_branded_data(conn)
        
        # Create views
        create_optimized_views(conn)
        
        # Print stats
        print_database_stats(conn)
        
        print("\naœ… Data ingestion completed successfully!")
        print(f"Database ready at: {DB_PATH}")
        
    except Exception as e:
        print(f"\naŒ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()



