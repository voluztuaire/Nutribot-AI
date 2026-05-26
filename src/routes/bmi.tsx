import { createFileRoute } from "@tanstack/react-router";
import { Nav, Blobs } from "@/components/Nav";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useState, useMemo } from "react";
import bowl from "@/assets/bowl.jpg";

export const Route = createFileRoute("/bmi")({
  component: BmiPage,
  head: () => ({ meta: [{ title: "BMI Calculator — NutriBot" }, { name: "description", content: "Calculate your BMI and daily calorie needs." }] }),
});

const ACTIVITY = [
  { k: "sedentary", label: "Sedentary (little exercise)", mult: 1.2 },
  { k: "light", label: "Light (1–3 days/wk)", mult: 1.375 },
  { k: "moderate", label: "Moderate (3–5 days/wk)", mult: 1.55 },
  { k: "active", label: "Active (6–7 days/wk)", mult: 1.725 },
];

function BmiPage() {
  const [age, setAge] = useState(28);
  const [gender, setGender] = useState<"male" | "female">("male");
  const [height, setHeight] = useState(175);
  const [weight, setWeight] = useState(70);
  const [act, setAct] = useState("moderate");

  const { bmi, category, tdee, bmr } = useMemo(() => {
    const h = height / 100;
    const bmi = weight / (h * h);
    const bmr = gender === "male"
      ? 10 * weight + 6.25 * height - 5 * age + 5
      : 10 * weight + 6.25 * height - 5 * age - 161;
    const mult = ACTIVITY.find((a) => a.k === act)?.mult ?? 1.55;
    const tdee = bmr * mult;
    let category = "Normal";
    if (bmi < 18.5) category = "Underweight";
    else if (bmi >= 25 && bmi < 30) category = "Overweight";
    else if (bmi >= 30) category = "Obese";
    return { bmi, category, tdee, bmr };
  }, [age, gender, height, weight, act]);

  const catColor =
    category === "Normal" ? "text-primary" :
    category === "Underweight" ? "text-sun-foreground" :
    "text-citrus";

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Nav />
      <main className="relative z-10 mx-auto max-w-5xl px-4 pt-10 pb-24">
        <h1 className="font-display text-4xl font-semibold">Body Metrics</h1>
        <p className="text-muted-foreground mt-1">Get your BMI and daily calorie needs.</p>

        <div className="mt-10 grid lg:grid-cols-[1fr_360px] gap-6">
          <div className="glass rounded-3xl p-6 md:p-8">
            <div className="grid sm:grid-cols-2 gap-5">
              <Field label="Age"><Input type="number" value={age} onChange={(e) => setAge(+e.target.value)} /></Field>
              <Field label="Gender">
                <div className="flex gap-2">
                  {(["male", "female"] as const).map((g) => (
                    <button key={g} type="button" onClick={() => setGender(g)}
                      className={`flex-1 rounded-full px-4 py-2 text-sm capitalize border transition-colors ${gender === g ? "bg-primary text-primary-foreground border-primary" : "bg-white/60 border-border hover:bg-white"}`}>
                      {g}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Height (cm)"><Input type="number" value={height} onChange={(e) => setHeight(+e.target.value)} /></Field>
              <Field label="Weight (kg)"><Input type="number" value={weight} onChange={(e) => setWeight(+e.target.value)} /></Field>
              <div className="sm:col-span-2">
                <Field label="Activity level">
                  <div className="grid sm:grid-cols-2 gap-2">
                    {ACTIVITY.map((a) => (
                      <button key={a.k} type="button" onClick={() => setAct(a.k)}
                        className={`text-left rounded-xl px-4 py-3 text-sm border transition-colors ${act === a.k ? "bg-primary/10 border-primary" : "bg-white/60 border-border hover:bg-white"}`}>
                        {a.label}
                      </button>
                    ))}
                  </div>
                </Field>
              </div>
            </div>
            <Button className="mt-6 rounded-full" disabled>Save profile (enable Cloud)</Button>
          </div>

          <aside className="space-y-4">
            <div className="glass rounded-3xl p-6 relative overflow-hidden">
              <img src={bowl} alt="" className="absolute -right-10 -bottom-10 w-48 opacity-20" loading="lazy" />
              <div className="text-xs text-muted-foreground uppercase tracking-wider">Your BMI</div>
              <div className="font-display text-6xl font-semibold mt-2">{bmi.toFixed(1)}</div>
              <div className={`mt-1 font-medium ${catColor}`}>{category}</div>
            </div>
            <div className="glass rounded-3xl p-6">
              <div className="text-xs text-muted-foreground uppercase tracking-wider">Daily energy</div>
              <div className="mt-3 flex items-end justify-between">
                <div>
                  <div className="text-xs text-muted-foreground">BMR</div>
                  <div className="font-display text-2xl font-semibold">{Math.round(bmr)}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">TDEE</div>
                  <div className="font-display text-3xl font-semibold text-primary">{Math.round(tdee)}</div>
                  <div className="text-xs text-muted-foreground">kcal/day</div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label className="text-xs uppercase tracking-wider text-muted-foreground">{label}</Label>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}
