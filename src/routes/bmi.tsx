import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/bmi")({
  head: () => ({ meta: [{ title: "BMI Calculator — NutriBot" }] }),
  component: BmiPage,
});

function classify(bmi: number) {
  if (bmi < 18.5) return { label: "Underweight", color: "from-sun to-citrus", tip: "Add nutrient-dense, calorie-rich foods like nuts, avocado, oats and lean protein. Aim for 3 meals + 2 snacks." };
  if (bmi < 25)   return { label: "Normal",      color: "from-leaf to-sun",    tip: "Maintain your balance: 0.8–1g protein/kg body weight, plenty of vegetables, and 30 min of movement most days." };
  if (bmi < 30)   return { label: "Overweight",  color: "from-citrus to-secondary", tip: "Aim for a ~500 kcal/day deficit, prioritise whole foods, fibre and strength training 2–3x/week." };
  return { label: "Obese", color: "from-secondary to-secondary", tip: "Consider a structured plan with a healthcare professional. Focus on sustainable habits, sleep, hydration and movement." };
}

function BmiPage() {
  const { user } = useAuth();

  // Defaults read from the user's profile on mount; users may temporarily
  // change them for what-if checks, but a page refresh re-reads from profile.
  const [height, setH] = useState("0");
  const [weight, setW] = useState("0");

  useEffect(() => {
    setH(user?.height ? String(user.height) : "0");
    setW(user?.weight ? String(user.weight) : "0");
  }, [user?.height, user?.weight]);

  const bmi = useMemo(() => {
    const h = Number(height) / 100; const w = Number(weight);
    if (!h || !w) return null;
    return +(w / (h * h)).toFixed(1);
  }, [height, weight]);
  const verdict = bmi ? classify(bmi) : null;

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6 md:p-10">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">BMI <span className="gradient-text">calculator</span></h1>
          <p className="text-muted-foreground mb-8">
            {user?.height && user?.weight
              ? "Starting from your saved profile — change the numbers to explore. Refresh to reset."
              : "Enter your height and weight, or save them on your profile to auto-fill."}
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="glass-strong rounded-3xl p-6 ring-glow">
              <Field label="Height (cm)"><input type="number" value={height} onChange={(e) => setH(e.target.value)} className={cls} /></Field>
              <Field label="Weight (kg)"><input type="number" value={weight} onChange={(e) => setW(e.target.value)} className={cls} /></Field>
            </div>

            <div className="glass-strong rounded-3xl p-6 flex flex-col items-center justify-center">
              {bmi != null && verdict ? (
                <>
                  <div className="text-6xl font-bold text-brand">
                    {bmi}
                  </div>
                  <div className="mt-2 text-lg font-semibold">{verdict.label}</div>
                  <p className="mt-4 text-sm text-muted-foreground text-center">{verdict.tip}</p>
                </>
              ) : (
                <div className="text-muted-foreground text-sm">Enter your height and weight</div>
              )}
            </div>
          </div>

          <div className="mt-8 glass rounded-3xl p-6">
            <div className="grid grid-cols-4 gap-3 text-xs text-center">
              {[
                { l: "Underweight", r: "< 18.5", c: "bg-sun/30" },
                { l: "Normal",      r: "18.5 – 24.9", c: "bg-leaf/30" },
                { l: "Overweight",  r: "25 – 29.9", c: "bg-citrus/30" },
                { l: "Obese",       r: "≥ 30", c: "bg-secondary/40" },
              ].map((x) => (
                <div key={x.l} className={`rounded-2xl p-3 ${x.c}`}>
                  <div className="font-semibold">{x.l}</div>
                  <div className="text-foreground/70">{x.r}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

const cls = "w-full rounded-2xl glass px-4 py-3 outline-none focus:ring-2 focus:ring-leaf text-lg text-foreground";
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mb-4">
      <span className="block text-xs font-semibold text-muted-foreground mb-1">{label}</span>
      {children}
    </label>
  );
}
