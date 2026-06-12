"""
Nutrition Calculator Service
Menghitung BMR, TDEE, dan kebutuhan kalori harian
"""

def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """
    Hitung Basal Metabolic Rate (BMR) menggunakan Mifflin-St Jeor Equation
    
    Args:
        weight: Berat badan dalam kg
        height: Tinggi badan dalam cm
        age: Umur dalam tahun
        gender: 'male' atau 'female'
    
    Returns:
        BMR dalam kalori per hari
    """
    if gender.lower() == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:  # female
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    return round(bmr, 2)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Hitung Total Daily Energy Expenditure (TDEE)
    
    Args:
        bmr: Basal Metabolic Rate
        activity_level: Level aktivitas
            - 'sedentary': Duduk terus, jarang gerak
            - 'lightly active': Olahraga ringan 1-3 hari/minggu
            - 'moderately active': Olahraga sedang 3-5 hari/minggu
            - 'very active': Olahraga berat 6-7 hari/minggu
    
    Returns:
        TDEE dalam kalori per hari
    """
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'extremely active': 1.9
    }
    
    multiplier = activity_multipliers.get(activity_level.lower(), 1.2)
    tdee = bmr * multiplier
    
    return round(tdee, 2)


def calculate_target_calories(tdee: float, goal: str) -> dict:
    """
    Hitung target kalori berdasarkan tujuan
    
    Args:
        tdee: Total Daily Energy Expenditure
        goal: Tujuan user
            - 'turun berat badan' / 'weight loss' / 'defisit': Defisit 500 kcal
            - 'naik berat badan' / 'weight gain' / 'surplus': Surplus 500 kcal
            - 'maintain' / 'maintenance': Sama dengan TDEE
    
    Returns:
        Dictionary dengan target kalori dan deficit/surplus
    """
    goal_lower = goal.lower()
    
    # Defisit untuk turun berat badan
    if any(keyword in goal_lower for keyword in ['turun', 'loss', 'defisit', 'deficit', 'kurus']):
        target = tdee - 500
        adjustment = -500
        goal_type = 'defisit'
    
    # Surplus untuk naik berat badan
    elif any(keyword in goal_lower for keyword in ['naik', 'gain', 'surplus', 'gemuk', 'bulk']):
        target = tdee + 500
        adjustment = +500
        goal_type = 'surplus'
    
    # Maintenance
    else:
        target = tdee
        adjustment = 0
        goal_type = 'maintenance'
    
    return {
        'target_calories': round(target, 2),
        'adjustment': adjustment,
        'goal_type': goal_type
    }


def calculate_macros(calories: float, macro_split: str = 'balanced') -> dict:
    """
    Hitung distribusi makronutrien
    
    Args:
        calories: Total kalori harian
        macro_split: Tipe split makro
            - 'balanced': 30% protein, 40% carbs, 30% fat
            - 'high_protein': 40% protein, 30% carbs, 30% fat
            - 'low_carb': 35% protein, 20% carbs, 45% fat
    
    Returns:
        Dictionary dengan gram protein, carbs, fat
    """
    splits = {
        'balanced': {'protein': 0.30, 'carbs': 0.40, 'fat': 0.30},
        'high_protein': {'protein': 0.40, 'carbs': 0.30, 'fat': 0.30},
        'low_carb': {'protein': 0.35, 'carbs': 0.20, 'fat': 0.45}
    }
    
    split = splits.get(macro_split, splits['balanced'])
    
    # Konversi kalori ke gram
    # 1g protein = 4 kcal, 1g carbs = 4 kcal, 1g fat = 9 kcal
    protein_grams = (calories * split['protein']) / 4
    carbs_grams = (calories * split['carbs']) / 4
    fat_grams = (calories * split['fat']) / 9
    
    return {
        'protein': round(protein_grams, 1),
        'carbs': round(carbs_grams, 1),
        'fat': round(fat_grams, 1),
        'protein_percentage': int(split['protein'] * 100),
        'carbs_percentage': int(split['carbs'] * 100),
        'fat_percentage': int(split['fat'] * 100)
    }


def get_nutrition_summary(weight: float, height: float, age: int, gender: str, 
                         activity_level: str, goal: str, macro_split: str = 'balanced') -> dict:
    """
    Hitung semua informasi nutrisi lengkap
    
    Returns:
        Dictionary lengkap dengan BMR, TDEE, target kalori, dan macros
    """
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, activity_level)
    target = calculate_target_calories(tdee, goal)
    macros = calculate_macros(target['target_calories'], macro_split)
    
    return {
        'bmr': bmr,
        'tdee': tdee,
        'target_calories': target['target_calories'],
        'adjustment': target['adjustment'],
        'goal_type': target['goal_type'],
        'macros': macros
    }


# Contoh penggunaan
if __name__ == '__main__':
    # Test case
    result = get_nutrition_summary(
        weight=70,
        height=170,
        age=25,
        gender='male',
        activity_level='moderately active',
        goal='turun berat badan'
    )
    
    print("Nutrition Summary:")
    print(f"BMR: {result['bmr']} kcal")
    print(f"TDEE: {result['tdee']} kcal")
    print(f"Target Calories: {result['target_calories']} kcal ({result['goal_type']})")
    print(f"Macros: {result['macros']}")



