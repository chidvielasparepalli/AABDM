import { NavLink } from "react-router-dom";
import { UserButton, useUser } from "@clerk/clerk-react";
import { MockUserButton, useMockAuth } from "../mockAuth";

const NAV = [
  { to: "/", label: "Dashboard", icon: "◈" },
  { to: "/clients", label: "Clients", icon: "◐" },
  { to: "/meetings", label: "Meetings", icon: "◉" },
  { to: "/learning", label: "Learning", icon: "✳" },
];

export function Sidebar() {
  const MOCK = import.meta.env.VITE_MOCK_AUTH === "true";
  const mock = useMockAuth();
  const { user } = MOCK ? { user: mock?.user ?? null } : useUser();
  const email = MOCK ? mock?.user?.primaryEmailAddress?.emailAddress : user?.primaryEmailAddress?.emailAddress;
  const UserButtonEl = MOCK ? MockUserButton : UserButton;
  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex w-16 flex-col items-center gap-1 border-r border-glass-line bg-black/20 py-4 backdrop-blur-2xl lg:w-56 lg:items-stretch lg:px-3">
      <div className="mb-4 flex items-center justify-center gap-2 lg:px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-aurora-violet/80 to-aurora-cyan/70 font-display text-lg font-bold text-white shadow-glow">
          A
        </div>
        <span className="hidden font-display text-sm font-semibold tracking-wide text-white lg:block">
          AABDM
        </span>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.to === "/"}
            className={({ isActive }) =>
              `flex items-center justify-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all lg:justify-start ${
                isActive
                  ? "bg-white/[0.10] text-white shadow-glow"
                  : "text-ink-dim hover:bg-white/[0.05] hover:text-ink"
              }`
            }
          >
            <span className="text-base leading-none">{n.icon}</span>
            <span className="hidden lg:inline">{n.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto flex flex-col items-center gap-2 lg:items-start">
        <div className="hidden w-full rounded-xl border border-glass-line bg-white/[0.04] px-3 py-2 lg:block">
          {email && <p className="truncate text-xs text-ink-dim">{email}</p>}
        </div>
        <div className="scale-90">
          <UserButtonEl />
        </div>
      </div>
    </aside>
  );
}
