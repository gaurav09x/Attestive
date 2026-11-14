import { useState, type ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { BarChart3, BriefcaseBusiness, ClipboardCheck, LayoutDashboard, LogOut, Menu, Route as RouteIcon, Settings, Sparkles, X } from "lucide-react";
import { Logo } from "../Logo";
import { cn } from "../ui";
import { useAuth } from "../../lib/auth";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/assessments", label: "Diagnostics", icon: ClipboardCheck },
  { to: "/roadmap", label: "Your roadmap", icon: RouteIcon },
  { to: "/tutor", label: "AI tutor", icon: Sparkles },
  { to: "/career", label: "Career", icon: BriefcaseBusiness },
  { to: "/insights", label: "Insights", icon: BarChart3 },
  { to: "/settings", label: "Profile & settings", icon: Settings },
];

function initials(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("") || "SF"
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [signingOut, setSigningOut] = useState(false);

  async function handleLogout() {
    setSigningOut(true);
    await logout();
    onNavigate?.();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center px-5">
        <Link to="/dashboard" onClick={onNavigate} className="rounded-md" aria-label="Attestive dashboard">
          <Logo />
        </Link>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Primary">
        <p className="px-3 pb-2 text-[11px] font-semibold tracking-[0.16em] text-fog-500 uppercase">
          Learn
        </p>
        {navigation.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-ink-800 text-fog-100"
                  : "text-fog-400 hover:bg-ink-800/60 hover:text-fog-100",
              )
            }
          >
            <item.icon className="size-4 shrink-0" aria-hidden />
            {item.label}
          </NavLink>
        ))}

        <div className="mt-6 rounded-lg border border-line bg-ink-900/60 p-3.5">
          <p className="text-[11px] font-semibold tracking-[0.14em] text-fog-500 uppercase">
            How it works
          </p>
          <p className="mt-2 text-xs leading-relaxed text-fog-400">
            Take a diagnostic, get a roadmap from your weakest skills, and update the plan with a
            new attempt whenever you want fresh evidence.
          </p>
        </div>
      </nav>

      {user ? (
        <div className="border-t border-line p-3">
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-line-bright bg-ink-700 text-xs font-semibold text-fog-200">
              {initials(user.full_name)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fog-100">{user.full_name}</p>
              <p className="truncate text-xs text-fog-500">{user.email}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            disabled={signingOut}
            className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-fog-400 transition-colors hover:bg-ink-800 hover:text-fog-100 disabled:opacity-60"
          >
            <LogOut className="size-4" aria-hidden />
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[16.5rem_1fr]">
      <aside className="sticky top-0 hidden h-screen border-r border-line bg-ink-950/70 lg:block">
        <SidebarContent />
      </aside>

      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-line bg-ink-950/85 px-5 backdrop-blur-xl lg:hidden">
        <Link to="/dashboard" aria-label="Attestive dashboard" className="rounded-md">
          <Logo />
        </Link>
        <button
          type="button"
          className="rounded-md p-2 text-fog-300 hover:bg-ink-800"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </button>
      </header>

      <AnimatePresence>
        {mobileOpen ? (
          <motion.div
            className="fixed inset-0 z-50 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              type="button"
              className="absolute inset-0 bg-black/70"
              aria-label="Close navigation"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="relative h-full w-[17rem] border-r border-line bg-ink-950"
            >
              <button
                type="button"
                className="absolute right-3 top-4 rounded-md p-2 text-fog-400 hover:bg-ink-800"
                onClick={() => setMobileOpen(false)}
                aria-label="Close navigation"
              >
                <X className="size-5" />
              </button>
              <SidebarContent onNavigate={() => setMobileOpen(false)} />
            </motion.aside>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="min-w-0">
        <main className="mx-auto w-full max-w-6xl px-5 py-8 sm:px-8 lg:py-10">{children}</main>
      </div>
    </div>
  );
}
