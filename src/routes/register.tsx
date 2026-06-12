import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { login, register } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Sidebar } from "@/components/Sidebar";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Sign up — NutriBot" }] }),
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [form, setForm] = useState({
    username: "", email: "", password: "",
    age: "", gender: "", height: "", weight: "",
    goal: "Maintain", activity_level: "moderately active",
  });
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null); setLoading(true);
    try {
      await register({
        username: form.username, email: form.email, password: form.password,
        age: form.age ? Number(form.age) : undefined,
        gender: form.gender || undefined,
        height: form.height ? Number(form.height) : undefined,
        weight: form.weight ? Number(form.weight) : undefined,
        goal: form.goal, activity_level: form.activity_level,
      });
      const res = await login(form.username, form.password);
      setSession(res.access_token, res.user);
      navigate({ to: "/" });
    } catch (e: any) {
      setErr(e?.response?.data?.error ?? "Sign up failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto grid place-items-center p-6">
        <form onSubmit={onSubmit} className="glass-strong w-full max-w-xl rounded-3xl p-8 ring-glow">
          <h1 className="text-3xl font-bold gradient-text mb-2">Create your account</h1>
          <p className="text-muted-foreground mb-6 text-sm">A few details so NutriBot can personalise your plans.</p>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Username"><input required value={form.username} onChange={(e) => set("username", e.target.value)} className={fieldCls} /></Field>
            <Field label="Email"><input required type="email" value={form.email} onChange={(e) => set("email", e.target.value)} className={fieldCls} /></Field>
            <Field label="Password" full><input required type="password" value={form.password} onChange={(e) => set("password", e.target.value)} className={fieldCls} /></Field>
            <Field label="Age"><input type="number" value={form.age} onChange={(e) => set("age", e.target.value)} className={fieldCls} /></Field>
            <Field label="Gender">
              <select value={form.gender} onChange={(e) => set("gender", e.target.value)} className={fieldCls}>
                <option value="">—</option><option>male</option><option>female</option><option>other</option>
              </select>
            </Field>
            <Field label="Height (cm)"><input type="number" value={form.height} onChange={(e) => set("height", e.target.value)} className={fieldCls} /></Field>
            <Field label="Weight (kg)"><input type="number" value={form.weight} onChange={(e) => set("weight", e.target.value)} className={fieldCls} /></Field>
            <Field label="Goal">
              <select value={form.goal} onChange={(e) => set("goal", e.target.value)} className={fieldCls}>
                <option>Weight Loss</option><option>Maintain</option><option>Muscle Gain</option>
              </select>
            </Field>
            <Field label="Activity">
              <select value={form.activity_level} onChange={(e) => set("activity_level", e.target.value)} className={fieldCls}>
                <option>sedentary</option><option>lightly active</option><option>moderately active</option><option>very active</option>
              </select>
            </Field>
          </div>
          {err && <div className="mt-4 text-sm text-secondary-foreground bg-secondary/20 rounded-xl px-3 py-2">{err}</div>}
          <button disabled={loading}
            className="mt-5 w-full rounded-2xl py-3 font-semibold text-white bg-brand flex items-center justify-center gap-2 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Sign up
          </button>
          <div className="mt-4 text-sm text-center text-muted-foreground">
            Already have an account? <Link to="/login" className="text-leaf font-semibold">Login</Link>
          </div>
        </form>
      </main>
    </div>
  );
}

const fieldCls = "w-full rounded-2xl glass px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf";
function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <label className={full ? "col-span-2" : ""}>
      <span className="block text-xs font-semibold text-muted-foreground mb-1">{label}</span>
      {children}
    </label>
  );
}
