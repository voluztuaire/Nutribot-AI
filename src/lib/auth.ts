import { useEffect, useState } from "react";
import type { UserProfile } from "./api";

const TOKEN_KEY = "nutribot_token_v2";
const USER_KEY = "nutribot_user_v2";

// One-time cleanup of legacy keys so existing local sessions are cleared.
if (typeof window !== "undefined") {
  try {
    localStorage.removeItem("nutribot_token");
    localStorage.removeItem("nutribot_user");
  } catch {}
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
}

type Listener = () => void;
const listeners = new Set<Listener>();
let state: AuthState = { token: null, user: null };
let hydrated = false;

function update(patch: Partial<AuthState>) {
  state = { ...state, ...patch };
  listeners.forEach((l) => l());
}

export const auth = {
  get state() { return state; },
  setSession(token: string, user: UserProfile) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    update({ token, user });
  },
  setUser(user: UserProfile) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    update({ user });
  },
  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    update({ token: null, user: null });
  },
  hydrate() {
    if (hydrated || typeof window === "undefined") return;
    hydrated = true;
    const token = localStorage.getItem(TOKEN_KEY);
    const userRaw = localStorage.getItem(USER_KEY);
    update({
      token,
      user: userRaw ? (JSON.parse(userRaw) as UserProfile) : null,
    });
  },
};

export function useAuth() {
  const [, setTick] = useState(0);
  useEffect(() => {
    auth.hydrate();
    const l = () => setTick((t) => t + 1);
    listeners.add(l);
    return () => { listeners.delete(l); };
  }, []);
  return { ...state, ...auth };
}
