import { createFileRoute } from "@tanstack/react-router";
import { Nav, Blobs } from "@/components/Nav";
import plate from "@/assets/plate.jpg";
import bowl from "@/assets/bowl.jpg";
import citrus from "@/assets/citrus.jpg";

export const Route = createFileRoute("/planner")({
  component: PlannerPage,
  head: () => ({ meta: [{ title: "Meal Planner — NutriBot" }, { name: "description", content: "Weekly AI-curated meal plan with accurate macros." }] }),
});

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MEALS = [
  { name: "Breakfast", img: bowl, items: ["Greek yogurt", "Berries", "Granola"], kcal: 420 },
  { name: "Lunch", img: plate, items: ["Grilled chicken", "Quinoa", "Broccoli"], kcal: 620 },
  { name: "Snack", img: citrus, items: ["Orange", "Almonds"], kcal: 220 },
  { name: "Dinner", img: plate, items: ["Salmon", "Sweet potato", "Spinach"], kcal: 580 },
];

function PlannerPage() {
  const total = MEALS.reduce((s, m) => s + m.kcal, 0);
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Nav />
      <main className="relative z-10 mx-auto max-w-6xl px-4 pt-10 pb-24">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-4xl font-semibold">Your Week</h1>
            <p className="text-muted-foreground mt-1">AI picks the foods. Math is exact.</p>
          </div>
          <div className="glass rounded-2xl px-5 py-3">
            <div className="text-xs text-muted-foreground">Daily target</div>
            <div className="font-display text-2xl font-semibold text-primary">{total} <span className="text-sm text-muted-foreground font-sans">kcal</span></div>
          </div>
        </div>

        {/* Macro bars */}
        <div className="mt-6 grid sm:grid-cols-3 gap-4">
          <Macro label="Protein" value={132} target={150} color="bg-primary" />
          <Macro label="Carbs" value={210} target={250} color="bg-sun" />
          <Macro label="Fat" value={62} target={70} color="bg-citrus" />
        </div>

        {/* Calendar */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {DAYS.map((d, i) => (
            <div key={d} className={`glass rounded-2xl p-3 ${i === 0 ? "ring-2 ring-primary" : ""}`}>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold">{d}</span>
                <span className="text-muted-foreground">{total} kcal</span>
              </div>
              <div className="mt-2 space-y-1">
                {MEALS.map((m) => (
                  <div key={m.name} className="rounded-lg bg-white/60 px-2 py-1.5 text-[11px]">
                    <div className="font-medium">{m.name}</div>
                    <div className="text-muted-foreground truncate">{m.items[0]}…</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Today */}
        <h2 className="mt-12 font-display text-2xl font-semibold">Today's plate</h2>
        <div className="mt-4 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {MEALS.map((m) => (
            <div key={m.name} className="glass rounded-3xl overflow-hidden">
              <div className="aspect-[4/3] overflow-hidden">
                <img src={m.img} alt={m.name} loading="lazy" className="w-full h-full object-cover" />
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-display text-lg font-semibold">{m.name}</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{m.kcal} kcal</span>
                </div>
                <ul className="mt-2 text-sm text-muted-foreground space-y-0.5">
                  {m.items.map((i) => <li key={i}>• {i}</li>)}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function Macro({ label, value, target, color }: { label: string; value: number; target: number; color: string }) {
  const pct = Math.min(100, (value / target) * 100);
  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground text-xs">{value}g / {target}g</span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-white/70 overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
