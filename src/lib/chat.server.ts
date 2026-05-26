import { computeItem, totals } from "./nutrition";

// Export the computation logic from here instead of chat.functions.ts
export function computeNutrition(items: any) {
  const computed = items.map(computeItem);
  const totalsRow = totals(computed);
  return { computed, totalsRow };
}