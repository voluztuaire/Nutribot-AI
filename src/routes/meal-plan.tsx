import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/lib/auth";
import { sendChat } from "@/lib/api";
import { Loader2, Sparkles, Salad } from "lucide-react";

export const Route = createFileRoute("/meal-plan")({
  head: () => ({ meta: [{ title: "Meal Plan — NutriBot" }] }),
  component: MealPlanPage,
});

const GOALS = ["Weight Loss", "Maintain", "Muscle Gain"] as const;
const DIETS = ["No restriction", "Vegetarian", "Vegan", "Halal", "Pescatarian", "Low-carb"] as const;

function MealPlanPage() {
  const { user, token } = useAuth();
  const [days, setDays] = useState(3);
  const [calories, setCalories] = useState(2000);
  const [goal, setGoal] = useState<typeof GOALS[number]>("Maintain");
  const [diet, setDiet] = useState<typeof DIETS[number]>("No restriction");
  const [notes, setNotes] = useState("");
  const [plan, setPlan] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    if (!token) { setError("Log in to generate a personalized meal plan."); return; }
    setLoading(true); setError(null); setPlan(null); setSummary(null);
    const prompt =
      `Build me a ${days}-day meal plan around ${calories} kcal/day. ` +
      `Goal: ${goal}. Dietary preference: ${diet}.` +
      (notes ? ` Notes: ${notes}.` : "") +
      ` Format each day with Breakfast / Lunch / Dinner / Snacks, ` +
      `include per-meal calories and a daily macro total.`;
    try {
      const res = await sendChat({ message: prompt, context: user ?? undefined });
      setPlan(res.reply);
      setSummary(res.meal_plan_summary);
    } catch (e: any) {
      setError(e?.response?.data?.error ?? e?.message ?? "Failed to reach NutriBot backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6 md:p-10">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand text-white">
              <Salad className="h-6 w-6" />
            </div>
            <h1 className="text-4xl font-bold">Meal <span className="gradient-text">plan</span></h1>
          </div>
          <p className="text-muted-foreground mb-8">
            Generate a personalized diet schedule built from your profile.
          </p>

          {!token && (
            <div className="mb-6 glass rounded-3xl p-5 border border-secondary/40">
              You need to <Link to="/login" className="font-semibold text-leaf underline">log in</Link> to generate a personalized meal plan.
            </div>
          )}

          <div className="grid lg:grid-cols-[1fr_1.4fr] gap-6">
            <div className="glass-strong rounded-3xl p-6 ring-glow h-fit">
              <Field label="Days">
                <input type="number" min={1} max={14} value={days} onChange={(e) => setDays(Number(e.target.value))} className={cls} />
              </Field>
              <Field label="Calories / day">
                <input type="number" min={1000} max={4500} step={50} value={calories} onChange={(e) => setCalories(Number(e.target.value))} className={cls} />
              </Field>
              <Field label="Goal">
                <select value={goal} onChange={(e) => setGoal(e.target.value as any)} className={cls}>
                  {GOALS.map((g) => <option key={g}>{g}</option>)}
                </select>
              </Field>
              <Field label="Dietary preference">
                <select value={diet} onChange={(e) => setDiet(e.target.value as any)} className={cls}>
                  {DIETS.map((d) => <option key={d}>{d}</option>)}
                </select>
              </Field>
              <Field label="Notes (allergies, dislikes…)">
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} className={cls} />
              </Field>

              <button
                onClick={generate}
                disabled={loading || !token}
                className="mt-2 w-full rounded-2xl px-6 py-3 font-semibold text-white bg-brand disabled:opacity-50 hover:brightness-110 transition-transform inline-flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {loading ? "Cooking up your plan…" : "Generate meal plan"}
              </button>
              {error && <div className="mt-3 text-sm text-secondary">{error}</div>}
            </div>

            <div className="glass-strong rounded-3xl p-6 min-h-[400px]">
              {summary && (
                <div className="mb-4 rounded-2xl bg-sun/20 border border-sun/40 px-4 py-3">
                  <div className="text-xs font-bold uppercase tracking-wider mb-1">Quick summary</div>
                  <div className="md-body text-sm">
                    <ReactMarkdown>{summary}</ReactMarkdown>
                  </div>
                </div>
              )}
              {plan ? (
                <div className="md-body text-[15px]">
                  <ReactMarkdown>{plan}</ReactMarkdown>
                </div>
              ) : !loading ? (
                <div className="h-full grid place-items-center text-center text-muted-foreground">
                  <div>
                    <Salad className="h-10 w-10 mx-auto mb-3 text-leaf" />
                    <p>Your meal plan will appear here.</p>
                  </div>
                </div>
              ) : (
                <div className="grid place-items-center h-full text-muted-foreground">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

const cls = "w-full rounded-2xl glass px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf text-foreground";
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mb-4">
      <span className="block text-xs font-semibold text-muted-foreground mb-1">{label}</span>
      {children}
    </label>
  );
}
