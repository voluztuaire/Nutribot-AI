import axios from "axios";

export const API_BASE_URL =
  (import.meta.env.VITE_NUTRIBOT_API as string | undefined) ??
  "http://localhost:5000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("nutribot_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface UserProfile {
  id?: number;
  username: string;
  email: string;
  height?: number | null;
  weight?: number | null;
  age?: number | null;
  gender?: string | null;
  goal?: string | null;
  activity_level?: string | null;
}

export interface ChatHistoryItem {
  sender: "user" | "ai";
  message: string;
}

export interface ChatResponse {
  reply: string;
  nutrition_summary: any | null;
  meal_plan_summary: string | null;
  meal_calendar: any[] | null;
  error: string | null;
}

export async function sendChat(payload: {
  message: string;
  history?: ChatHistoryItem[];
  context?: Partial<UserProfile> | null;
}) {
  const { data } = await api.post<ChatResponse>("/api/chat", payload);
  return data;
}

export async function calcNutrition(payload: {
  age: number; gender: string; height: number; weight: number;
  activity_level: string; goal: string;
}) {
  const { data } = await api.post("/api/nutrition", payload);
  return data;
}

export async function login(username: string, password: string) {
  const { data } = await api.post("/api/auth/login", { username, password });
  return data as { access_token: string; user: UserProfile };
}
export async function register(payload: {
  username: string; email: string; password: string;
} & Partial<UserProfile>) {
  const { data } = await api.post("/api/auth/register", payload);
  return data;
}
export async function getMe() {
  const { data } = await api.get<UserProfile>("/api/auth/me");
  return data;
}
export async function updateProfile(profile: Partial<UserProfile>) {
  const { data } = await api.put("/api/auth/profile", profile);
  return data as { message: string; user: UserProfile };
}
export async function getHistory(sessionId?: string) {
  const { data } = await api.get("/api/chat/history", {
    params: sessionId ? { session_id: sessionId } : {},
  });
  return data as { messages: any[] };
}
export async function saveMessage(payload: {
  message: string; sender: "user" | "ai"; session_id?: string; model_used?: string;
}) {
  const { data } = await api.post("/api/chat/history", payload);
  return data;
}
