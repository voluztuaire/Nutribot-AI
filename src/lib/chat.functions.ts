import { createServerFn } from "@tanstack/react-start";
import { createClient } from "@supabase/supabase-js";
import type { Database } from "@/integrations/supabase/types";
import { supabaseAdmin } from "@/integrations/supabase/client.server";
import { computeItem, totals, type Computed, type FoodRow, type Item, type Totals } from "./nutrition";

console.log("Chat functions file loaded on server!");

type ChatMsg = { role: "user" | "assistant"; content: string };

const GATEWAY = "https://api.groq.com/openai/v1/chat/completions";
const MODEL = "llama-3.3-70b-versatile"; 

// Stopwords that should never be used as a sole fallback search term
const STOPWORDS = new Set([
  "cooked", "raw", "fresh", "whole", "plain", "boiled", "grilled", "baked",
  "roasted", "fried", "steamed", "sliced", "chopped", "medium", "large",
  "small", "with", "and", "the", "some", "lean", "low", "fat", "free",
]);

// Default piece weights for countable foods (when LLM gives count not grams)
const PIECE_WEIGHTS: Record<string, number> = {
  apple: 180, banana: 120, orange: 150, egg: 50, eggs: 50,
  potato: 170, tomato: 120, carrot: 60, kiwi: 75, peach: 150,
  pear: 180, avocado: 200,
};

async function userClient(token: string) {
  const SUPABASE_URL = process.env.SUPABASE_URL!;
  const SUPABASE_KEY = process.env.SUPABASE_PUBLISHABLE_KEY!;
  const c = createClient<Database>(SUPABASE_URL, SUPABASE_KEY, {
    global: { headers: { Authorization: `Bearer ${token}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data, error } = await c.auth.getUser(token);
  if (error || !data?.user) throw new Error("Unauthorized");
  return { client: c, userId: data.user.id };
}

// ---------- Phase 1: extract food items from the user message ----------
async function extractItems(history: ChatMsg[], userMsg: string): Promise<Array<{ query: string; grams: number }>> {
  const apiKey = process.env.GROQ_API_KEY!; // Pastikan di .env namaya GROQ_API_KEY
  if (!apiKey) throw new Error("GROQ_API_KEY missing");

  const res = await fetch(GATEWAY, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        {
          role: "system",
          content: "Extract food items from the user's message. Return ONLY valid JSON in this format: { \"items\": [{\"query\": \"food_name\", \"grams\": number}] }. If no food, return {\"items\": []}.",
        },
        ...history.slice(-6),
        { role: "user", content: userMsg },
      ],
      response_format: { type: "json_object" }
    }),
  });

  if (!res.ok) throw new Error(`extract failed: ${res.status} ${await res.text()}`);
  const data = await res.json();
  const content = JSON.parse(data.choices[0].message.content);
  return content.items || [];
}

// Repair grams: if absurdly small, treat as a piece count using PIECE_WEIGHTS
function repairGrams(query: string, grams: number): number {
  if (grams >= 10) return grams;
  const q = query.toLowerCase();
  for (const [k, w] of Object.entries(PIECE_WEIGHTS)) {
    if (q.includes(k)) return Math.round((grams || 1) * w);
  }
  return Math.max(grams, 100); // generic safe default
}

// ---------- Phase 2: RAG retrieve REAL match ----------
async function retrieveFood(query: string): Promise<FoodRow | null> {
  const q = query.toLowerCase().trim();

  // Searching the Supabase 'foods' table
  const { data: rows, error } = await supabaseAdmin
    .from("foods")
    .select("id, name, category, kcal_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g")
    .ilike("name", `%${q}%`)
    .limit(1);

  if (error) {
    console.error("Supabase Database Error:", error);
    return null;
  }

  if (rows && rows.length > 0) {
    const r = rows[0];
    return {
      id: String(r.id),
      name: r.name,
      category: r.category,
      kcal_per_100g: Number(r.kcal_per_100g || 0),
      protein_per_100g: Number(r.protein_per_100g || 0),
      carbs_per_100g: Number(r.carbs_per_100g || 0),
      fat_per_100g: Number(r.fat_per_100g || 0),
      fiber_per_100g: Number(r.fiber_per_100g || 0),
    };
  }
  
  return null;
}

// ---------- Phase 3: Computation ----------
// This handles the math for the requested portion size
function computeNutrition(items: Item[]): { computed: Computed[]; totalsRow: Totals } {
  const computed = items.map(computeItem);
  const totalsRow = totals(computed);
  return { computed, totalsRow };
}

// ---------- Phase 4: format reply around fixed numbers ----------
async function formatReply(
  userMsg: string, computed: Computed[],
  totalsRow: ReturnType<typeof totals>, unmatched: string[],
): Promise<string> {
  const apiKey = process.env.GROQ_API_KEY!;
  const factSheet = { items: computed, totals: totalsRow, unmatched };

    const res = await fetch(GATEWAY, {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: "system",
            content: 
              "You are NutriBot, a friendly and casual AI nutritionist. " +
              "1. Write ONE short, enthusiastic opening sentence. " +
              "2. Follow with max 3 bullet points using '- '. " +
              "3. Use a very natural, conversational tone. " +
              "4. NEVER use double newlines (keep it compact). " +
              "5. Do NOT show tables or numbers in the text (the UI handles that). " +
              "Keep it under 60 words total."
          },
          { role: "user", content: `User asked: ${userMsg}\n\nDATA: ${JSON.stringify(factSheet)}` },
        ],
      }),
    });

  const data = await res.json();
  let text = data.choices?.[0]?.message?.content ?? "";
  return text.replace(/\n\n+/g, '\n').trim();
}

// ---------- Public server fns ----------
export const chat = createServerFn({ method: "POST" })
  .inputValidator((d: { token?: string; message: string; history: ChatMsg[] }) => d)
  .handler(async ({ data }) => {
    try {
      console.log("Chat request received:", data.message);
      
      const { computeItem, totals } = await import("./nutrition");
      const message = data.message.slice(0, 1000);
      const history = (data.history ?? []).slice(-10);

      const extracted = await extractItems(history, message);
      console.log("Extracted items:", extracted); // See if Gemini is working

      const items: Item[] = [];
      const unmatched: string[] = [];
      for (const e of extracted) {
        const grams = repairGrams(e.query, e.grams);
        const food = await retrieveFood(e.query);
        if (food) items.push({ query: e.query, grams, food });
        else unmatched.push(e.query);
      }

      const computed = items.map(computeItem);
      const totalsRow = totals(computed);
      const reply = await formatReply(message, computed, totalsRow, unmatched);

      return { reply, summary: computed.length ? { items: computed, totals: totalsRow, unmatched } : null };
    } catch (e) {
      console.error("SERVER ERROR in chat function:", e); // THIS IS THE IMPORTANT LINE
      throw e;
    }
  });

export const loadHistory = createServerFn({ method: "POST" })
  .inputValidator((d: { token: string }) => d)
  .handler(async ({ data }) => {
    const { client, userId } = await userClient(data.token);
    const { data: rows } = await client
      .from("chat_messages")
      .select("role, content, summary, created_at")
      .eq("user_id", userId)
      .order("created_at", { ascending: true })
      .limit(200);
    return rows ?? [];
  });

export const clearHistory = createServerFn({ method: "POST" })
  .inputValidator((d: { token: string }) => d)
  .handler(async ({ data }) => {
    const { client, userId } = await userClient(data.token);
    await client.from("chat_messages").delete().eq("user_id", userId);
    return { ok: true };
  });


export const summarizeChat = createServerFn({ method: "POST" })
  .inputValidator((d: { messages: ChatMsg[] }) => d)
  .handler(async ({ data }) => {
    const apiKey = process.env.GROQ_API_KEY!;
    if (!apiKey) throw new Error("GROQ_API_KEY missing");

    const transcript = data.messages
      .filter((m) => m.content?.trim())
      .map((m) => `${m.role === "user" ? "User" : "NutriBot"}: ${m.content}`)
      .join("\n");

    const res = await fetch(GATEWAY, {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: "system",
            content:
              "You write a SHORT nutrition consultation summary. Output plain text only. Sections: TOPIC, KEY NUMBERS, RECOMMENDATIONS, NEXT STEPS. Max 180 words.",
          },
          { role: "user", content: `Conversation:\n\n${transcript}` },
        ],
      }),
    });
    
    if (!res.ok) throw new Error(`summary failed: ${res.status} ${await res.text()}`);
    const j = await res.json();
    return { summary: (j.choices?.[0]?.message?.content ?? "").trim() };
  });