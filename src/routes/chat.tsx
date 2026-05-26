import { createFileRoute, Link } from "@tanstack/react-router";
import { Nav, Blobs } from "@/components/Nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRef, useState, useEffect } from "react";
import { useServerFn } from "@tanstack/react-start";
import { Send, Sparkles, Bot, User, Loader2, FileDown, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chat, loadHistory, clearHistory, summarizeChat } from "@/lib/chat.functions";
import { useAuth } from "@/lib/auth";
import jsPDF from "jspdf";

export const Route = createFileRoute("/chat")({
  component: ChatPage,
  head: () => ({ meta: [{ title: "Chat — NutriBot" }, { name: "description", content: "Chat with NutriBot about nutrition and meal planning." }] }),
});

type Summary = {
  items: Array<{ matched: string; grams: number; kcal: number; protein_g: number; carbs_g: number; fat_g: number }>;
  totals: { kcal: number; protein_g: number; carbs_g: number; fat_g: number };
  unmatched: string[];
};

type Msg = { role: "user" | "assistant"; content: string; summary?: Summary | null };

const WELCOME: Msg = {
  role: "assistant",
  content: "Hi! I'm **NutriBot** 🌱 Ask me about any food or request a meal plan. Every number is computed by a server-side calculator from a real food database — I can't fake macros.",
};

const SAMPLES = [
  "How much protein in 150g of chicken breast?",
  "Build me a 2000 kcal vegetarian day",
  "I ate 2 eggs, 50g oats and a banana — macros?",
];

function ChatPage() {
  const chatFn = useServerFn(chat);
  const loadFn = useServerFn(loadHistory);
  const clearFn = useServerFn(clearHistory);
  const summFn = useServerFn(summarizeChat);
  const { user, token, loading: authLoading } = useAuth();

  const [messages, setMessages] = useState<Msg[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  // Load history when signed in
  useEffect(() => {
    if (!token) return;
    loadFn({ data: { token } }).then((rows: any[]) => {
      if (rows && rows.length) {
        setMessages([
          WELCOME,
          ...rows.map((r) => ({ role: r.role, content: r.content, summary: r.summary })),
        ]);
      }
    }).catch(() => {});
  }, [token, loadFn]);

  async function send(text?: string) {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    setInput("");
    const next: Msg[] = [...messages, { role: "user", content: q }];
    setMessages(next);
    setLoading(true);
    try {
      const history = next.map((m) => ({ role: m.role, content: m.content }));
      const res = await chatFn({ data: { token, message: q, history } });
      setMessages((m) => [...m, { role: "assistant", content: res.reply, summary: res.summary }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  async function clearAll() {
    if (!confirm("Clear all chat history?")) return;
    if (token) await clearFn({ data: { token } });
    setMessages([WELCOME]);
  }

  async function downloadSummary() {
    if (summarizing) return;
    setSummarizing(true);
    try {
      const convo = messages.filter((m) => m !== WELCOME);
      if (convo.length === 0) { alert("Nothing to summarize yet — send a message first."); return; }
      const { summary } = await summFn({
        data: { messages: convo.map((m) => ({ role: m.role, content: m.content })) },
      });
      buildPdf(summary, user?.email);
    } catch (e) {
      alert("Couldn't build summary. Please try again.");
    } finally {
      setSummarizing(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Nav />
      <main className="relative z-10 mx-auto max-w-3xl px-4 pt-10 pb-36">
        <div className="flex items-end justify-between gap-3 flex-wrap">
          <div>
            <h1 className="font-display text-3xl font-semibold">Chat with NutriBot</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {user ? "Signed in — your history is saved." : <>Not signed in — <Link to="/login" className="text-primary underline">sign in</Link> to save history.</>}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={downloadSummary} disabled={summarizing || authLoading}>
              {summarizing ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <FileDown className="h-4 w-4 mr-1.5" />}
              Summary PDF
            </Button>
            {messages.length > 1 && (
              <Button variant="ghost" size="sm" onClick={clearAll}>
                <Trash2 className="h-4 w-4 mr-1.5" /> Clear
              </Button>
            )}
          </div>
        </div>

        <div className="mt-8 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`grid place-items-center h-9 w-9 rounded-full shrink-0 ${m.role === "user" ? "bg-citrus text-citrus-foreground" : "bg-primary text-primary-foreground"}`}>
                {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>
              <div className={`glass rounded-2xl px-4 py-3 max-w-[88%] ${m.role === "user" ? "rounded-tr-sm" : "rounded-tl-sm"}`}>
                <div className="text-sm leading-relaxed prose prose-sm max-w-none prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5 prose-strong:text-foreground">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                </div>
                {m.summary && m.summary.items.length > 0 && (
                  <div className="mt-3 rounded-xl overflow-hidden border border-border bg-background/70">
                    <div className="flex items-center gap-1.5 px-3 py-2 bg-primary/10 text-xs font-semibold text-primary">
                      <Sparkles className="h-3 w-3" /> Verified math · server-computed
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs tabular-nums">
                        <thead>
                          <tr className="bg-muted/40 text-muted-foreground">
                            <th className="text-left font-semibold py-2 px-3">Food</th>
                            <th className="text-right font-semibold py-2 px-2">Amount</th>
                            <th className="text-right font-semibold py-2 px-2">kcal</th>
                            <th className="text-right font-semibold py-2 px-2">P (g)</th>
                            <th className="text-right font-semibold py-2 px-2">C (g)</th>
                            <th className="text-right font-semibold py-2 px-2">F (g)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {m.summary.items.map((it, j) => (
                            <tr key={j} className="border-t border-border">
                            <td className="py-1.5 px-3">{capitalize(it.matched)}</td> 
                            <td className="py-1.5 px-2 text-right">{it.grams}g</td>
                            <td className="py-1.5 px-2 text-right font-medium">{it.kcal}</td>
                            <td className="py-1.5 px-2 text-right">{it.protein_g}</td>
                            <td className="py-1.5 px-2 text-right">{it.carbs_g}</td>
                            <td className="py-1.5 px-2 text-right">{it.fat_g}</td>
                          </tr>
                          ))}
                          {m.summary.items.length > 1 && (
                            <tr className="border-t-2 border-primary/40 bg-primary/5 font-semibold">
                              <td className="py-2 px-3">Total</td>
                              <td className="py-2 px-2 text-right text-muted-foreground">—</td>
                              <td className="py-2 px-2 text-right">{m.summary.totals.kcal}</td>
                              <td className="py-2 px-2 text-right">{m.summary.totals.protein_g}</td>
                              <td className="py-2 px-2 text-right">{m.summary.totals.carbs_g}</td>
                              <td className="py-2 px-2 text-right">{m.summary.totals.fat_g}</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                    {m.summary.unmatched.length > 0 && (
                      <div className="text-[11px] text-muted-foreground px-3 py-2 border-t border-border italic">
                        Not in database: {m.summary.unmatched.join(", ")}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="grid place-items-center h-9 w-9 rounded-full bg-primary text-primary-foreground"><Bot className="h-4 w-4" /></div>
              <div className="glass rounded-2xl px-4 py-3 flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Looking up foods…
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {SAMPLES.map((s) => (
            <button key={s} onClick={() => send(s)} disabled={loading} className="text-xs px-3 py-1.5 rounded-full glass hover:bg-white/80 transition-colors disabled:opacity-50">
              {s}
            </button>
          ))}
        </div>
      </main>

      <div className="fixed bottom-0 inset-x-0 z-20 px-4 pb-6 pt-4 bg-gradient-to-t from-background to-transparent">
        <form
          onSubmit={(e) => { e.preventDefault(); send(); }}
          className="mx-auto max-w-3xl glass rounded-full p-1.5 flex items-center gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about a food or request a meal plan…"
            className="border-0 bg-transparent focus-visible:ring-0 shadow-none text-sm"
            disabled={loading}
          />
          <Button type="submit" size="icon" className="rounded-full shrink-0" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}

function capitalize(str: string) {
  if (!str) return str;
  return str
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function buildPdf(summary: string, email?: string) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const margin = 48;
  const maxW = pageW - margin * 2;

  // Brand palette (green / yellow / orange)
  const GREEN: [number, number, number] = [76, 159, 90];
  const YELLOW: [number, number, number] = [245, 200, 66];
  const ORANGE: [number, number, number] = [240, 138, 56];
  const DARK: [number, number, number] = [40, 54, 44];
  const MUTED: [number, number, number] = [120, 130, 124];

  // Header band
  doc.setFillColor(...GREEN);
  doc.rect(0, 0, pageW, 110, "F");
  doc.setFillColor(...YELLOW);
  doc.rect(0, 110, pageW, 6, "F");
  doc.setFillColor(...ORANGE);
  doc.rect(0, 116, pageW, 3, "F");

  // Logo dot
  doc.setFillColor(...YELLOW);
  doc.circle(margin + 14, 56, 14, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.setTextColor(...DARK);
  doc.text("N", margin + 9, 62);

  // Title
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.text("NutriBot", margin + 40, 52);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(12);
  doc.text("Session Summary", margin + 40, 72);

  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  const meta = `${new Date().toLocaleString()}${email ? `  ·  ${email}` : ""}`;
  doc.text(meta, margin + 40, 90);

  // Body — section cards
  let y = 150;
  const sections = parseSections(summary || "No summary available.");
  const sectionColors: Array<[number, number, number]> = [GREEN, ORANGE, YELLOW, GREEN];

  sections.forEach((sec, idx) => {
    const color = sectionColors[idx % sectionColors.length];
    const bullets = sec.lines;
    const blockH = 36 + bullets.length * 16 + 14;
    if (y + blockH > pageH - 60) { doc.addPage(); y = 60; }

    // Card background
    doc.setFillColor(252, 250, 245);
    doc.roundedRect(margin, y, maxW, blockH, 10, 10, "F");
    // Left accent bar
    doc.setFillColor(...color);
    doc.roundedRect(margin, y, 6, blockH, 3, 3, "F");

    // Title
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.setTextColor(...color);
    doc.text(sec.title, margin + 18, y + 22);

    // Bullets
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10.5);
    doc.setTextColor(...DARK);
    let by = y + 42;
    for (const b of bullets) {
      const wrapped = doc.splitTextToSize(b, maxW - 40);
      doc.setFillColor(...color);
      doc.circle(margin + 22, by - 3, 1.8, "F");
      doc.text(wrapped, margin + 30, by);
      by += 16 * wrapped.length;
    }
    y += blockH + 14;
  });

  // Footer
  doc.setDrawColor(...YELLOW);
  doc.setLineWidth(2);
  doc.line(margin, pageH - 40, pageW - margin, pageH - 40);
  doc.setFont("helvetica", "italic");
  doc.setFontSize(9);
  doc.setTextColor(...MUTED);
  doc.text("Generated by NutriBot · numbers verified by server-side calculator", margin, pageH - 24);

  doc.save(`nutribot-summary-${new Date().toISOString().slice(0, 10)}.pdf`);
}

function parseSections(text: string): Array<{ title: string; lines: string[] }> {
  const out: Array<{ title: string; lines: string[] }> = [];
  let current: { title: string; lines: string[] } | null = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    if (/^[A-Z][A-Z\s]{2,}$/.test(line)) {
      if (current) out.push(current);
      current = { title: line, lines: [] };
    } else {
      const clean = line.replace(/^[-•*]\s*/, "");
      if (!current) current = { title: "Summary", lines: [] };
      current.lines.push(clean);
    }
  }
  if (current) out.push(current);
  return out.length ? out : [{ title: "Summary", lines: [text] }];
}
