import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/lib/auth";
import { getMe, updateProfile, type UserProfile } from "@/lib/api";
import { useAvatar, setAvatar, clearAvatar, fileToAvatarDataUrl } from "@/lib/avatar";
import { Camera, Loader2, Trash2 } from "lucide-react";

export const Route = createFileRoute("/profile")({
  head: () => ({ meta: [{ title: "Profile — NutriBot" }] }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user, token, setUser } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<UserProfile | null>(user);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const avatar = useAvatar(form?.id);

  useEffect(() => {
    if (!token) { navigate({ to: "/login" }); return; }
    getMe().then((u) => { setUser(u); setForm(u); }).catch(() => {});
  }, [token]);

  if (!form) {
    return (
      <div className="flex h-screen w-screen"><Sidebar /><main className="flex-1 grid place-items-center"><Loader2 className="animate-spin" /></main></div>
    );
  }

  const set = (k: keyof UserProfile, v: any) => setForm({ ...form, [k]: v });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setSaving(true); setMsg(null);
    try {
      const res = await updateProfile({
        height: form.height ? Number(form.height) : null,
        weight: form.weight ? Number(form.weight) : null,
        age: form.age ? Number(form.age) : null,
        gender: form.gender, goal: form.goal, activity_level: form.activity_level,
      });
      setUser(res.user); setMsg("Profile updated ✓");
    } catch (e: any) {
      setMsg(e?.response?.data?.error ?? "Failed to update profile");
    } finally { setSaving(false); }
  }

  async function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !form?.id) return;
    try {
      const dataUrl = await fileToAvatarDataUrl(file);
      setAvatar(form.id, dataUrl);
    } catch {
      setMsg("Could not read that image");
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6 md:p-10">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">Your <span className="gradient-text">profile</span></h1>
          <p className="text-muted-foreground mb-8">Keep this fresh so meal plans stay accurate.</p>

          {/* Avatar card */}
          <div className="glass-strong rounded-3xl p-6 mb-6 flex items-center gap-5">
            <div className="relative group">
              <div className="absolute -inset-1 rounded-3xl bg-brand blur opacity-70 animate-float" />
              <div className="relative h-24 w-24 rounded-3xl overflow-hidden grid place-items-center bg-brand text-white text-3xl font-bold">
                {avatar ? (
                  <img src={avatar} alt="Avatar" className="absolute inset-0 h-full w-full object-cover" />
                ) : (
                  (form.username || "U").slice(0, 1).toUpperCase()
                )}
              </div>
            </div>
            <div className="flex-1">
              <div className="text-lg font-semibold">{form.username}</div>
              <div className="text-xs text-muted-foreground">{form.email}</div>
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  className="inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold text-white bg-brand hover:brightness-110 transition-transform"
                >
                  <Camera className="h-4 w-4" /> {avatar ? "Change photo" : "Upload photo"}
                </button>
                {avatar && form.id != null && (
                  <button
                    type="button"
                    onClick={() => clearAvatar(form.id!)}
                    className="inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground glass"
                  >
                    <Trash2 className="h-4 w-4" /> Remove
                  </button>
                )}
                <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onPickFile} />
              </div>
            </div>
          </div>

          <form onSubmit={save} className="glass-strong rounded-3xl p-6 md:p-8 grid grid-cols-2 gap-4">
            <Field label="Username"><input value={form.username} disabled className={cls + " opacity-70"} /></Field>
            <Field label="Email"><input value={form.email} disabled className={cls + " opacity-70"} /></Field>
            <Field label="Age"><input type="number" value={form.age ?? ""} onChange={(e) => set("age", e.target.value)} className={cls} /></Field>
            <Field label="Gender">
              <select value={form.gender ?? ""} onChange={(e) => set("gender", e.target.value)} className={cls}>
                <option value="">—</option><option>male</option><option>female</option><option>other</option>
              </select>
            </Field>
            <Field label="Height (cm)"><input type="number" value={form.height ?? ""} onChange={(e) => set("height", e.target.value)} className={cls} /></Field>
            <Field label="Weight (kg)"><input type="number" value={form.weight ?? ""} onChange={(e) => set("weight", e.target.value)} className={cls} /></Field>
            <Field label="Goal">
              <select value={form.goal ?? ""} onChange={(e) => set("goal", e.target.value)} className={cls}>
                <option value="">—</option><option>Weight Loss</option><option>Maintain</option><option>Muscle Gain</option>
              </select>
            </Field>
            <Field label="Activity Level">
              <select value={form.activity_level ?? ""} onChange={(e) => set("activity_level", e.target.value)} className={cls}>
                <option value="">—</option><option>sedentary</option><option>lightly active</option><option>moderately active</option><option>very active</option>
              </select>
            </Field>
            <div className="col-span-2 flex items-center gap-3 mt-2">
              <button disabled={saving}
                className="rounded-2xl px-6 py-3 font-semibold text-white bg-brand disabled:opacity-60">
                {saving ? "Saving…" : "Save changes"}
              </button>
              {msg && <span className="text-sm text-muted-foreground">{msg}</span>}
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

const cls = "w-full rounded-2xl glass px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf text-foreground";
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="col-span-2 md:col-span-1">
      <span className="block text-xs font-semibold text-muted-foreground mb-1">{label}</span>
      {children}
    </label>
  );
}
