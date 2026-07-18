import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { login } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Login — NutriBot" }] }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null); setLoading(true);
    try {
      const res = await login(username, password);
      setSession(res.access_token, res.user);
      navigate({ to: "/" });
    } catch (e: any) {
      setErr(e?.response?.data?.error ?? "Login failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <main className="flex-1 grid place-items-center p-6">
        <form onSubmit={onSubmit} className="panel w-full max-w-md rounded-3xl p-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">Welcome back</h1>
          <p className="text-muted-foreground mb-6 text-sm">Login to unlock meal plans, history and your profile.</p>
          <label className="block text-xs font-semibold text-muted-foreground mb-1">Username</label>
          <input value={username} onChange={(e) => setU(e.target.value)} required
            className="w-full mb-4 rounded-2xl panel px-4 py-3 outline-none focus:ring-2 focus:ring-brand" />
          <label className="block text-xs font-semibold text-muted-foreground mb-1">Password</label>
          <input type="password" value={password} onChange={(e) => setP(e.target.value)} required
            className="w-full mb-4 rounded-2xl panel px-4 py-3 outline-none focus:ring-2 focus:ring-brand" />
          {err && <div className="mb-4 text-sm text-secondary-foreground bg-secondary/20 rounded-xl px-3 py-2">{err}</div>}
          <button disabled={loading}
            className="w-full rounded-2xl py-3 font-semibold text-white bg-brand flex items-center justify-center gap-2 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Login
          </button>
          <div className="mt-4 text-sm text-center text-muted-foreground">
            No account? <Link to="/register" className="text-brand font-semibold hover:underline">Create one</Link>
          </div>
        </form>
      </main>
    </div>
  );
}
