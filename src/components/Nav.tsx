import { Link, useNavigate } from "@tanstack/react-router";
import { Leaf, LogIn, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/auth";

export function Nav() {
  const { user, signOut } = useAuth();
  const nav = useNavigate();
  const linkCls = "px-3 py-2 rounded-full text-sm font-medium text-foreground/70 hover:text-foreground hover:bg-white/60 transition-colors";
  const activeCls = "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground";
  return (
    <header className="sticky top-4 z-50 mx-auto max-w-6xl px-4">
      <nav className="glass rounded-full px-4 py-2 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-semibold">
          <span className="grid place-items-center h-8 w-8 rounded-full bg-primary text-primary-foreground">
            <Leaf className="h-4 w-4" />
          </span>
          NutriBot
        </Link>
        <div className="flex items-center gap-1">
          <Link to="/" className={linkCls} activeOptions={{ exact: true }} activeProps={{ className: `${linkCls} ${activeCls}` }}>Home</Link>
          <Link to="/chat" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }}>Chat</Link>
          <Link to="/bmi" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }}>BMI</Link>
          <Link to="/planner" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }}>Planner</Link>
          {user ? (
            <>
              <Link to="/profile" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }}>
                <UserIcon className="h-4 w-4 inline mr-1" />Profile
              </Link>
              <button onClick={async () => { await signOut(); nav({ to: "/" }); }} className={linkCls}>Sign out</button>
            </>
          ) : (
            <Link to="/login" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }}>
              <LogIn className="h-4 w-4 inline mr-1" />Sign in
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}

export function Blobs() {
  return (
    <>
      <div className="blob bg-primary -top-20 -left-20 h-80 w-80" />
      <div className="blob bg-citrus top-40 -right-20 h-96 w-96" />
      <div className="blob bg-sun top-[60%] left-[30%] h-72 w-72" />
    </>
  );
}
