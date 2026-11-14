import { useState, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Menu, X } from "lucide-react";
import { Logo } from "../Logo";
import { Button, cn } from "../ui";
import { useAuth } from "../../lib/auth";

const navItems = [
  { to: "/features", label: "Features" },
  { to: "/about", label: "About" },
];

export function MarketingLayout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { status } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-line/70 bg-ink-950/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-5 sm:px-8">
          <Link to="/" aria-label="Attestive home" className="rounded-md">
            <Logo />
          </Link>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3.5 py-2 text-sm transition-colors",
                    isActive ? "text-fog-100" : "text-fog-400 hover:text-fog-100",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            {status === "authenticated" ? (
              <Link to="/dashboard">
                <Button size="sm">
                  Open dashboard
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Sign in
                  </Button>
                </Link>
                <Link to="/register">
                  <Button size="sm">Start learning free</Button>
                </Link>
              </>
            )}
          </div>

          <button
            type="button"
            className="rounded-md p-2 text-fog-300 hover:bg-ink-800 md:hidden"
            onClick={() => setOpen((value) => !value)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>

        <AnimatePresence>
          {open ? (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden border-t border-line bg-ink-950 md:hidden"
            >
              <div className="space-y-1 px-5 py-4">
                {navItems.map((item) => (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setOpen(false)}
                    className="block rounded-md px-3 py-2.5 text-sm text-fog-300 hover:bg-ink-800 hover:text-fog-100"
                  >
                    {item.label}
                  </Link>
                ))}
                <div className="flex flex-col gap-2 pt-3">
                  {status === "authenticated" ? (
                    <Link to="/dashboard" onClick={() => setOpen(false)}>
                      <Button className="w-full">Open dashboard</Button>
                    </Link>
                  ) : (
                    <>
                      <Link to="/login" onClick={() => setOpen(false)}>
                        <Button variant="secondary" className="w-full">
                          Sign in
                        </Button>
                      </Link>
                      <Link to="/register" onClick={() => setOpen(false)}>
                        <Button className="w-full">Start learning free</Button>
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-line bg-ink-950">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 py-12 sm:px-8 md:grid-cols-[1.4fr_1fr_1fr]">
          <div className="max-w-sm space-y-4">
            <Logo />
            <p className="text-sm leading-relaxed text-fog-400">
              An adaptive learning platform for people building technical careers. Assess honestly,
              learn deliberately, prove it with real work.
            </p>
          </div>
          <div>
            <h2 className="text-xs font-semibold tracking-[0.14em] text-fog-500 uppercase">Product</h2>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <Link to="/features" className="text-fog-300 hover:text-fog-100">
                  Features
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-fog-300 hover:text-fog-100">
                  About Attestive
                </Link>
              </li>
              <li>
                <Link to="/register" className="text-fog-300 hover:text-fog-100">
                  Create an account
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h2 className="text-xs font-semibold tracking-[0.14em] text-fog-500 uppercase">Account</h2>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <Link to="/login" className="text-fog-300 hover:text-fog-100">
                  Sign in
                </Link>
              </li>
              <li>
                <Link to="/dashboard" className="text-fog-300 hover:text-fog-100">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link to="/settings" className="text-fog-300 hover:text-fog-100">
                  Settings
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-line">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-5 py-5 text-xs text-fog-500 sm:flex-row sm:items-center sm:justify-between sm:px-8">
            <p>© {new Date().getFullYear()} Attestive. Built as an open learning platform.</p>
            <p>Local-first AI · PostgreSQL-backed progress · No fabricated metrics</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
