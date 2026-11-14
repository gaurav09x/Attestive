import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, ShieldCheck, Sparkles, Terminal } from "lucide-react";
import { Logo } from "../Logo";

const highlights = [
  {
    icon: Sparkles,
    title: "A path shaped around you",
    body: "Your goals, current level and available study time decide what comes next.",
  },
  {
    icon: Terminal,
    title: "Practice, not just reading",
    body: "Write real code, get reviewed, and build projects that prove the skill.",
  },
  {
    icon: ShieldCheck,
    title: "Your progress is yours",
    body: "Real records in a relational database. No invented streaks, no fake scores.",
  },
];

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_1.05fr]">
      <div className="flex flex-col px-5 py-8 sm:px-10">
        <Link to="/" className="w-fit rounded-md">
          <Logo />
        </Link>

        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-2 text-sm leading-relaxed text-fog-400">{subtitle}</p>
            <div className="mt-8">{children}</div>
            <div className="mt-6 text-sm text-fog-400">{footer}</div>
          </motion.div>
        </div>

        <p className="text-xs text-fog-500">
          By continuing you agree to use Attestive responsibly. Your data is never sold.
        </p>
      </div>

      <aside className="relative hidden overflow-hidden border-l border-line bg-ink-900/60 lg:block">
        <div className="absolute inset-0 bg-grid opacity-60" aria-hidden />
        <div
          className="absolute -left-24 top-1/3 size-[28rem] rounded-full bg-electric/15 blur-[110px]"
          aria-hidden
        />
        <div
          className="absolute -right-20 bottom-0 size-[24rem] rounded-full bg-violet/15 blur-[100px]"
          aria-hidden
        />

        <div className="relative flex h-full flex-col justify-center px-14">
          <p className="text-xs font-semibold tracking-[0.18em] text-fog-500 uppercase">
            The Attestive approach
          </p>
          <h2 className="mt-4 max-w-md text-3xl font-semibold leading-tight">
            Every student learns differently.
            <span className="text-gradient"> The platform should too.</span>
          </h2>

          <div className="mt-10 space-y-6">
            {highlights.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + index * 0.1, duration: 0.45 }}
                className="flex gap-4"
              >
                <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg border border-line bg-ink-800 text-electric">
                  <item.icon className="size-4" aria-hidden />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-fog-100">{item.title}</h3>
                  <p className="mt-1 max-w-sm text-sm leading-relaxed text-fog-400">{item.body}</p>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-12 flex items-center gap-2 text-xs text-fog-500">
            <CheckCircle2 className="size-3.5 text-emerald" aria-hidden />
            Built with FastAPI, PostgreSQL and a local LLM pipeline
          </div>
        </div>
      </aside>
    </div>
  );
}
