export type FoodRow = {
  id: string;
  name: string;
  category: string | null;
  kcal_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  fiber_per_100g: number;
};

export type Item = { query: string; grams: number; food: FoodRow; };
export type Computed = { query: string; matched: string; grams: number; kcal: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g: number; };
export type Totals = { kcal: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g: number; };

const round1 = (n: number) => Math.round(n * 10) / 10;

export function computeItem(item: Item): Computed {
  const f = item.food;
  const k = item.grams / 100;
  return {
    query: item.query, matched: f.name, grams: item.grams,
    kcal: Math.round(f.kcal_per_100g * k),
    protein_g: round1(f.protein_per_100g * k),
    carbs_g: round1(f.carbs_per_100g * k),
    fat_g: round1(f.fat_per_100g * k),
    fiber_g: round1(f.fiber_per_100g * k),
  };
}

export function totals(items: Computed[]): Totals {
  return items.reduce<Totals>((a, c) => ({
      kcal: a.kcal + c.kcal,
      protein_g: round1(a.protein_g + c.protein_g),
      carbs_g: round1(a.carbs_g + c.carbs_g),
      fat_g: round1(a.fat_g + c.fat_g),
      fiber_g: round1(a.fiber_g + c.fiber_g),
    }), { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 });
}

