import { Link, useRouterState } from "@tanstack/react-router";
import { useSessions, deleteSession } from "@/lib/sessions";
import {
  Leaf, MessageCircle, Calculator, Salad,
  FilePlus2, PanelLeftClose, PanelLeftOpen, Trash2,
} from "lucide-react";

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  onNewChat?: () => void;
  activeSessionId?: string | null;
  onSelectSession?: (id: string) => void;
}

export function Sidebar({
  collapsed,
  onToggleCollapse,
  onNewChat,
  activeSessionId,
  onSelectSession,
}: SidebarProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const sessions = useSessions();

  // Collapsed rail: just the toggle button so the user can reopen.
  if (collapsed) {
    return (
      <aside className="hidden md:flex w-14 shrink-0 flex-col items-center gap-3 p-3 border-r border-white/20 bg-brand/90 backdrop-blur-xl text-white">
        <button
          onClick={onToggleCollapse}
          title="Open sidebar"
          className="grid h-10 w-10 place-items-center rounded-xl hover:bg-white/20 text-white transition-colors"
        >
          <PanelLeftOpen className="h-5 w-5" />
        </button>
        <button
          onClick={onNewChat}
          title="New chat"
          className="grid h-10 w-10 place-items-center rounded-xl bg-white text-brand hover:bg-white/90 transition-colors"
        >
          <FilePlus2 className="h-5 w-5" />
        </button>
      </aside>
    );
  }

  const navItem = (to: string, icon: React.ReactNode, label: string) => {
    const active = pathname === to;
    return (
      <Link
        to={to}
        className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
          active
            ? "bg-white/20 text-white"
            : "text-white/80 hover:bg-white/10"
        }`}
      >
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-white/20 text-white">
          {icon}
        </span>
        {label}
      </Link>
    );
  };

  return (
    <aside className="hidden md:flex w-72 shrink-0 flex-col gap-3 p-3 border-r border-white/20 bg-brand/90 backdrop-blur-xl text-white">
      {/* Header */}
      <div className="flex items-center justify-between px-2 py-2">
        <div className="flex items-center gap-2">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-white text-brand">
            <Leaf className="h-5 w-5" />
          </div>
          <div>
            <div className="text-base font-bold leading-none">NutriBot</div>
            <div className="text-[10px] text-white/80 mt-0.5">AI nutrition copilot</div>
          </div>
        </div>
        <button
          onClick={onToggleCollapse}
          title="Close sidebar"
          className="grid h-9 w-9 place-items-center rounded-xl hover:bg-white/20 transition-colors"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      {/* New chat */}
      <button
        onClick={onNewChat}
        className="flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm btn-primary hover:btn-primary-hover transition-all"
      >
        <FilePlus2 className="h-4 w-4" /> New chat
      </button>

      {/* Nav */}
      <div className="flex flex-col gap-1">
        {navItem("/", <MessageCircle className="h-4 w-4" />, "Chat")}
        {navItem("/bmi", <Calculator className="h-4 w-4" />, "BMI Calculator")}
        {navItem("/meal-plan", <Salad className="h-4 w-4" />, "Meal Plan")}
      </div>

      {/* History list (inline, ChatGPT-style) */}
      <div className="mt-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
        History
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-0.5 pr-1">
        {sessions.length === 0 ? (
          <div className="px-3 py-2 text-xs text-white/60">No chats yet.</div>
        ) : (
          sessions.map((s) => {
            const active = s.id === activeSessionId && pathname === "/";
            return (
              <div
                key={s.id}
                className={`group flex items-center gap-1 rounded-lg pl-3 pr-1 py-2 text-sm cursor-pointer transition-colors ${
                  active
                    ? "bg-white/20 text-white font-semibold"
                    : "text-white/80 hover:bg-white/10"
                }`}
                onClick={() => onSelectSession?.(s.id)}
                title={s.title}
              >
                <span className="flex-1 truncate">{s.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                  className="opacity-0 group-hover:opacity-100 grid h-7 w-7 place-items-center rounded-md hover:bg-white/20 transition-colors"
                  title="Delete chat"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>


    </aside>
  );
}
