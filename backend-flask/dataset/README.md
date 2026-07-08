# Food Dataset Folder

NutriBot uses the USDA FoodData Central CSV bundle as its food database.

## Setup

1. Download the latest "Full Download of All Data Types" CSV ZIP from:
   https://fdc.nal.usda.gov/download-datasets

2. Unzip it directly into this folder. You should end up with a path like:
   `backend-flask/dataset/FoodData_Central_csv_YYYY-MM-DD/` containing
   `food.csv`, `nutrient.csv`, `food_nutrient.csv`, `food_category.csv`,
   `food_portion.csv`, `branded_food.csv`, and other CSVs.

3. From `backend-flask/`, build the SQLite database:
   ```
   python scripts/data_ingestion.py
   ```

   The script auto-detects any `FoodData_Central_csv_*` subfolder (latest by
   name wins). To force a specific path, set the env var
   `NUTRIBOT_DATASET_DIR=/absolute/path/to/folder`.

4. Output: `backend-flask/dataset/nutribot_foods.db`. Only these CSVs are
   imported (everything else in the bundle is ignored):
   `food_category.csv`, `nutrient.csv`, `food.csv`, `food_nutrient.csv`,
   `food_portion.csv`, `branded_food.csv`.

The full bundle is ~3 GB on disk; the generated SQLite DB is much smaller
and is what the RAG service queries at runtime.
