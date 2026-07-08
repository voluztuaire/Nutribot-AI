import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";

// Inline theme toggle — rendered next to the login/profile button in the sidebar.
export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      onClick={toggle}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={`grid h-9 w-9 place-items-center rounded-lg btn-ghost hover:bg-[var(--color-surface-2)] transition-colors ${className}`}
    >
      <span className="relative grid h-5 w-5 place-items-center">
        <Sun className={`absolute h-5 w-5 transition-all duration-300 ${isDark ? "opacity-0 scale-50" : "opacity-100 scale-100"}`} />
        <Moon className={`absolute h-5 w-5 transition-all duration-300 ${isDark ? "opacity-100 scale-100" : "opacity-0 scale-50"}`} />
      </span>
    </button>
  );
}
