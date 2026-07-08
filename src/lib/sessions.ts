// Local chat-session store. Persisted in localStorage so the sidebar
// history list works regardless of backend availability.
import { useEffect, useState } from "react";
import type { ChatHistoryItem } from "./api";

export interface StoredMsg extends ChatHistoryItem {
  id: string;
  summary?: string | null;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: StoredMsg[];
}

const KEY = "nutribot_sessions_v1";

function read(): ChatSession[] {
  if (typeof window === "undefined") return [];
  try { return JSON.parse(localStorage.getItem(KEY) ?? "[]"); } catch { return []; }
}
function write(list: ChatSession[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(list));
  window.dispatchEvent(new Event("nutribot:sessions"));
}

export function listSessions(): ChatSession[] {
  return read().sort((a, b) => b.updatedAt - a.updatedAt);
}

export function getSession(id: string): ChatSession | undefined {
  return read().find((s) => s.id === id);
}

export function upsertSession(s: ChatSession) {
  const list = read();
  const idx = list.findIndex((x) => x.id === s.id);
  if (idx >= 0) list[idx] = s; else list.push(s);
  write(list);
}

export function deleteSession(id: string) {
  write(read().filter((s) => s.id !== id));
}

export function renameSession(id: string, title: string) {
  const list = read();
  const idx = list.findIndex((s) => s.id === id);
  if (idx >= 0) { list[idx].title = title; list[idx].updatedAt = Date.now(); write(list); }
}

/** Derive a short title from the first user message. */
export function titleFromMessage(text: string): string {
  const t = text.trim().replace(/\s+/g, " ");
  return t.length <= 40 ? t : t.slice(0, 40) + "…";
}

/** Reactive hook that re-renders when sessions change. */
export function useSessions() {
  const [items, setItems] = useState<ChatSession[]>([]);
  useEffect(() => {
    const refresh = () => setItems(listSessions());
    refresh();
    window.addEventListener("nutribot:sessions", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("nutribot:sessions", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);
  return items;
}
