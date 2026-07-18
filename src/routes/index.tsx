import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatInterface } from "@/components/ChatInterface";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "NutriBot — AI Nutrition Copilot" },
      { name: "description", content: "Futuristic AI nutrition chatbot with meal plans, BMI and personalised summaries." },
    ],
  }),
  component: ChatPage,
});

const COLLAPSE_KEY = "nutribot_sidebar_collapsed";

function ChatPage() {
  const [collapsed, setCollapsed] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");

  useEffect(() => {
    setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
    setSessionId(crypto.randomUUID());
  }, []);

  const toggleCollapse = () => {
    setCollapsed((c) => {
      const next = !c;
      localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      return next;
    });
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden text-foreground">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={toggleCollapse}
        onNewChat={() => setSessionId(crypto.randomUUID())}
        activeSessionId={sessionId}
        onSelectSession={(id) => setSessionId(id)}
      />
      <main className="flex-1 flex flex-col min-w-0">
        {sessionId && (
          <ChatInterface
            key={sessionId}
            sessionId={sessionId}
            onSessionChange={(id) => setSessionId(id)}
          />
        )}
      </main>
    </div>
  );
}
