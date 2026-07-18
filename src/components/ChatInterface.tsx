import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link } from "@tanstack/react-router";
import { Send, Sparkles, Loader2, Download, Pencil, Check, LogOut, LogIn } from "lucide-react";
import { sendChat, saveMessage, type ChatHistoryItem } from "@/lib/api";
import { useAvatar } from "@/lib/avatar";
import { useAuth } from "@/lib/auth";
import {
  getSession, upsertSession, renameSession, titleFromMessage,
  type ChatSession, type StoredMsg,
} from "@/lib/sessions";
import { generateSummaryPdf } from "@/lib/pdf";

const SUGGESTIONS = [
  "Build me a 3-day, 2000 kcal meal plan",
  "How many calories are in 200g of chicken breast?",
  "Beginner tips for a calorie-deficit diet",
  "High-protein breakfast recipes",
];

interface Props {
  sessionId: string;
  onSessionChange?: (id: string) => void;
}

export function ChatInterface({ sessionId, onSessionChange }: Props) {
  const { user, token, logout } = useAuth();
  const avatar = useAvatar(user?.id);
  const [messages, setMessages] = useState<StoredMsg[]>([]);
  const [title, setTitle] = useState<string>("New chat");
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load session whenever the active id changes.
  useEffect(() => {
    const s = getSession(sessionId);
    if (s) {
      setMessages(s.messages);
      setTitle(s.title);
    } else {
      setMessages([]);
      setTitle("New chat");
    }
    setError(null);
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const isFresh = messages.length === 0;

  const askMealPlan = (text: string) => /meal plan|diet plan|schedule/i.test(text);

  function persist(next: StoredMsg[], nextTitle?: string) {
    const now = Date.now();
    const existing = getSession(sessionId);
    const session: ChatSession = {
      id: sessionId,
      title: nextTitle ?? existing?.title ?? title,
      createdAt: existing?.createdAt ?? now,
      updatedAt: now,
      messages: next,
    };
    upsertSession(session);
  }

  async function submit(text: string) {
    if (!text.trim() || loading) return;
    setError(null);
    if (askMealPlan(text) && !token) {
      setError("Login required for personalized meal/diet plan generation.");
      return;
    }
    const userMsg: StoredMsg = { id: crypto.randomUUID(), sender: "user", message: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");

    // Auto-title from first user message.
    let nextTitle = title;
    if (messages.length === 0) {
      nextTitle = titleFromMessage(text);
      setTitle(nextTitle);
    }
    persist(next, nextTitle);
    onSessionChange?.(sessionId);

    setLoading(true);
    try {
      const res = await sendChat({
        message: text,
        history: messages.map((m) => ({ sender: m.sender, message: m.message })),
        context: user ?? undefined,
      });
      const aiMsg: StoredMsg = {
        id: crypto.randomUUID(),
        sender: "ai",
        message: res.reply,
        summary: res.meal_plan_summary,
      };
      const after = [...next, aiMsg];
      setMessages(after);
      persist(after, nextTitle);

      if (token) {
        saveMessage({ message: text, sender: "user", session_id: sessionId }).catch(() => {});
        saveMessage({ message: res.reply, sender: "ai", session_id: sessionId, model_used: "groq" }).catch(() => {});
      }
    } catch (e: any) {
      const detail = e?.response?.data?.error || e?.message || "Failed to reach NutriBot backend.";
      setError(`${detail}  •  Is the Flask backend running on :5000?`);
    } finally {
      setLoading(false);
    }
  }

  function commitTitle() {
    const t = titleDraft.trim() || title;
    setTitle(t);
    setEditingTitle(false);
    if (getSession(sessionId)) renameSession(sessionId, t);
    else persist(messages, t);
  }

  async function exportPdf() {
    if (!messages.length) { setError("Chat with NutriBot first, then export."); return; }
    try { await generateSummaryPdf(messages as ChatHistoryItem[] as any, user); }
    catch (e: any) { setError("Failed to generate PDF: " + (e?.message ?? e)); }
  }

  return (
    <div className="flex flex-1 flex-col min-h-0">
      {/* Title bar (always present, even on fresh chat) */}
      <div className="flex items-center gap-2 px-4 md:px-8 py-3 border-b border-white/30 bg-white/40 backdrop-blur-xl">
        <div className="flex-1 min-w-0 flex items-center gap-2">
          {editingTitle ? (
            <input
              autoFocus
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={(e) => { if (e.key === "Enter") commitTitle(); if (e.key === "Escape") setEditingTitle(false); }}
              className="flex-1 min-w-0 bg-transparent border-b border-brand px-1 py-0.5 text-base font-semibold outline-none"
            />
          ) : (
            <button
              onClick={() => { setTitleDraft(title); setEditingTitle(true); }}
              className="flex items-center gap-2 min-w-0 text-left group"
              title="Rename chat"
            >
              <span className="truncate text-base font-semibold">{title}</span>
              <Pencil className="h-3.5 w-3.5 opacity-0 group-hover:opacity-60 shrink-0" />
            </button>
          )}
          {editingTitle && (
            <button onClick={commitTitle} className="grid h-7 w-7 place-items-center rounded-md btn-ghost hover:bg-[var(--color-surface-2)]">
              <Check className="h-4 w-4" />
            </button>
          )}
        </div>
          <button
          onClick={exportPdf}
          disabled={!messages.length}
          className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm btn-brand hover:btn-brand-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          title="Export conversation summary as PDF"
        >
          <Download className="h-4 w-4" /> Export PDF
        </button>
        <div className="ml-2 pl-4 border-l border-border flex items-center gap-3">
          {user ? (
            <>
              <Link
                to="/profile"
                title="Open profile"
                className="relative grid h-10 w-10 place-items-center rounded-xl overflow-hidden bg-brand text-white font-bold shrink-0"
              >
                {avatar ? (
                  <img src={avatar} alt={user.username} className="absolute inset-0 h-full w-full object-cover" />
                ) : (
                  user.username.slice(0, 1).toUpperCase()
                )}
              </Link>
              <button
                onClick={logout}
                className="grid h-10 w-10 place-items-center rounded-xl btn-ghost hover:bg-[var(--color-surface-2)]"
                title="Log out"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm btn-brand hover:btn-brand-hover"
            >
              <LogIn className="h-4 w-4" /> Log in
            </Link>
          )}
        </div>
      </div>

      {isFresh ? (
        <div className="flex flex-1 flex-col items-center justify-center px-6 animate-fade-up">
          <div className="grid h-16 w-16 place-items-center rounded-2xl bg-brand text-white mb-6">
            <Sparkles className="h-8 w-8" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-center">
            Hello, <span className="text-brand">{user?.username ?? "friend"}</span>
          </h1>
          <p className="mt-3 text-muted-foreground text-center max-w-md">
            What can I help you eat today? Ask about nutrition, build a meal plan, or check your BMI.
          </p>

          <div className="mt-8 w-full max-w-2xl">
            <Composer value={input} onChange={setInput} onSubmit={() => submit(input)} loading={loading} />
          </div>

          <div className="mt-6 flex flex-wrap justify-center gap-2 max-w-2xl">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => submit(s)}
                className="rounded-full panel-2 px-4 py-2 text-xs md:text-sm text-foreground hover:bg-[var(--color-background)] transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
          {error && <ErrorBanner message={error} />}
        </div>
      ) : (
        <>
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-10 py-6">
            <div className="mx-auto max-w-3xl flex flex-col gap-5">
              {messages.map((m) => <Bubble key={m.id} msg={m} />)}
              {loading && <TypingBubble />}
            </div>
          </div>
          <div className="border-t border-white/30 px-4 md:px-10 py-4 bg-white/40 backdrop-blur-xl">
            <div className="mx-auto max-w-3xl">
              <Composer value={input} onChange={setInput} onSubmit={() => submit(input)} loading={loading} />
              {error && <ErrorBanner message={error} />}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Composer({
  value, onChange, onSubmit, loading,
}: { value: string; onChange: (v: string) => void; onSubmit: () => void; loading: boolean }) {
  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit(); }}
      className="panel p-2 flex items-center gap-2"
    >
      <input
        autoFocus
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Ask NutriBot anything about food, calories, or meal plans…"
        className="flex-1 bg-transparent px-4 py-3 text-base outline-none placeholder:text-muted-foreground"
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="grid h-11 w-11 place-items-center rounded-xl btn-primary hover:btn-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
      </button>
    </form>
  );
}

function Bubble({ msg }: { msg: StoredMsg }) {
  const isUser = msg.sender === "user";
  return (
    <div className={`flex gap-3 animate-fade-up ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand text-white text-sm font-bold">
          N
        </div>
      )}
      <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
        isUser
          ? "bg-brand text-white rounded-tr-md"
          : "panel-2 text-foreground rounded-tl-md"
      }`}>
        {msg.summary && (
          <div className="mb-3 rounded-xl bg-amber/30 border border-amber px-3 py-2 text-xs" style={{ backgroundColor: "color-mix(in oklab, var(--color-amber) 30%, transparent)", borderColor: "var(--color-amber)" }}>
            <div className="font-bold mb-1">Quick Summary</div>
            <div className="md-body">
              <ReactMarkdown>{msg.summary}</ReactMarkdown>
            </div>
          </div>
        )}
        <div className="md-body text-[15px]">
          {isUser ? msg.message : <ReactMarkdown>{msg.message}</ReactMarkdown>}
        </div>
      </div>
      {isUser && (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl panel-2 text-foreground text-sm font-bold">
          U
        </div>
      )}
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex gap-3 animate-fade-up">
      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand text-white text-sm font-bold">N</div>
      <div className="panel-2 rounded-2xl rounded-tl-md px-5 py-4 flex items-center gap-1.5">
        <span className="block h-2 w-2 rounded-full bg-brand typing-dot" style={{ animationDelay: "0ms" }} />
        <span className="block h-2 w-2 rounded-full bg-brand typing-dot" style={{ animationDelay: "150ms" }} />
        <span className="block h-2 w-2 rounded-full bg-brand typing-dot" style={{ animationDelay: "300ms" }} />
      </div>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mt-4 rounded-xl border border-border panel-2 px-4 py-3 text-sm text-foreground">
      ⚠️ {message}
    </div>
  );
}
