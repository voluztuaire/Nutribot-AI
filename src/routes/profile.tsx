import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Nav, Blobs } from "@/components/Nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { supabase } from "@/integrations/supabase/client";
import { useEffect, useState } from "react";
import { Loader2, LogOut, Save } from "lucide-react";

export const Route = createFileRoute("/profile")({
  component: ProfilePage,
  head: () => ({ meta: [{ title: "Profile — NutriBot" }] }),
});

function ProfilePage() {
  const { user, loading, signOut } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({
    display_name: "",
    age: "",
    gender: "",
    height_cm: "",
    weight_kg: "",
    activity: "moderate",
    daily_kcal_target: "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!loading && !user) nav({ to: "/login" });
  }, [user, loading, nav]);

  useEffect(() => {
    if (!user) return;
    supabase.from("profiles").select("*").eq("id", user.id).maybeSingle().then(({ data }) => {
      if (data) {
        setForm({
          display_name: data.display_name ?? "",
          age: data.age?.toString() ?? "",
          gender: data.gender ?? "",
          height_cm: data.height_cm?.toString() ?? "",
          weight_kg: data.weight_kg?.toString() ?? "",
          activity: data.activity ?? "moderate",
          daily_kcal_target: data.daily_kcal_target?.toString() ?? "",
        });
      }
    });
  }, [user]);

  async function save() {
    if (!user) return;
    setSaving(true);
    setSaved(false);
    const payload = {
      id: user.id,
      display_name: form.display_name || null,
      age: form.age ? parseInt(form.age) : null,
      gender: form.gender || null,
      height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
      weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      activity: form.activity || null,
      daily_kcal_target: form.daily_kcal_target ? parseInt(form.daily_kcal_target) : null,
    };
    await supabase.from("profiles").upsert(payload);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen grid place-items-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  const fld = (k: keyof typeof form, label: string, type = "text") => (
    <div className="space-y-1.5">
      <Label htmlFor={k}>{label}</Label>
      <Input id={k} type={type} value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
    </div>
  );

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Nav />
      <main className="relative z-10 mx-auto max-w-2xl px-4 pt-10 pb-20">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-semibold">Your profile</h1>
            <p className="text-muted-foreground text-sm mt-1">{user.email}</p>
          </div>
          <Button variant="outline" size="sm" onClick={async () => { await signOut(); nav({ to: "/" }); }}>
            <LogOut className="h-4 w-4 mr-1.5" /> Sign out
          </Button>
        </div>

        <div className="glass rounded-3xl p-6 space-y-4">
          {fld("display_name", "Display name")}
          <div className="grid grid-cols-2 gap-4">
            {fld("age", "Age", "number")}
            <div className="space-y-1.5">
              <Label htmlFor="gender">Gender</Label>
              <select id="gender" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm">
                <option value="">—</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {fld("height_cm", "Height (cm)", "number")}
            {fld("weight_kg", "Weight (kg)", "number")}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="activity">Activity level</Label>
            <select id="activity" value={form.activity} onChange={(e) => setForm({ ...form, activity: e.target.value })}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="sedentary">Sedentary</option>
              <option value="light">Light</option>
              <option value="moderate">Moderate</option>
              <option value="active">Active</option>
              <option value="very_active">Very active</option>
            </select>
          </div>
          {fld("daily_kcal_target", "Daily kcal target", "number")}

          <Button onClick={save} disabled={saving} className="w-full rounded-full">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Save className="h-4 w-4 mr-1.5" /> {saved ? "Saved!" : "Save profile"}</>}
          </Button>
        </div>
      </main>
    </div>
  );
}
