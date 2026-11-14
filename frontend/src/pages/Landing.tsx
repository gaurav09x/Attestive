import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Boxes,
  BrainCircuit,
  Check,
  Code2,
  Compass,
  Gauge,
  GraduationCap,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
  Terminal,
} from "lucide-react";
import { MarketingLayout } from "../components/layout/MarketingLayout";
import { Badge, Button, Panel } from "../components/ui";

const fadeUp = {
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
};

const pillars = [
  {
    icon: Target,
    title: "Assess what you actually know",
    body: "A diagnostic mixes multiple choice, short answers and code. Weak concepts are identified per skill, not per course.",
    tag: "Phase 2",
  },
  {
    icon: Route,
    title: "A roadmap with reasons",
    body: "Modules, prerequisites, practice and projects sequenced around your goal and the time you really have.",
    tag: "Phase 2",
  },
  {
    icon: BrainCircuit,
    title: "A tutor that teaches",
    body: "Explanations adapt to your level. Hints come before answers, and misunderstandings are named and corrected.",
    tag: "Phase 3",
  },
  {
    icon: Terminal,
    title: "A lab that runs real code",
    body: "Python, JavaScript and C++ exercises with test cases and review — executed in a sandbox, never on the API server.",
    tag: "Phase 4",
  },
  {
    icon: BarChart3,
    title: "Analytics you can trust",
    body: "Study time, proficiency trends and revision topics computed from recorded activity — no invented numbers.",
    tag: "Phase 5",
  },
  {
    icon: Compass,
    title: "Career preparation",
    body: "Skill-gap analysis, portfolio project suggestions and technical mock interviews. No job guarantees, ever.",
    tag: "Phase 6",
  },
];

const principles = [
  "Proficiency is an estimate that improves with evidence — never a one-off verdict.",
  "XP is awarded for demonstrated learning, not for clicking through screens.",
  "The AI proposes; validated backend services decide what gets stored.",
  "Every number on your dashboard traces back to a database row.",
];

export default function Landing() {
  const reduceMotion = useReducedMotion();

  return (
    <MarketingLayout>
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid opacity-70" aria-hidden />
        {/* Slow-drifting brand glow behind the hero. The same colours the logo
            tile uses, so the mark and the page share one light source. */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
          <motion.div
            className="absolute -left-32 -top-10 size-[26rem] rounded-full bg-electric/20 blur-[120px]"
            animate={
              reduceMotion
                ? undefined
                : { x: [0, 60, 10, 0], y: [0, 30, 60, 0], scale: [1, 1.15, 0.95, 1] }
            }
            transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute -right-24 top-24 size-[22rem] rounded-full bg-violet/20 blur-[110px]"
            animate={
              reduceMotion
                ? undefined
                : { x: [0, -50, -10, 0], y: [0, 40, -20, 0], scale: [1, 0.92, 1.1, 1] }
            }
            transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
        <div className="relative mx-auto grid w-full max-w-6xl gap-14 px-5 pb-20 pt-16 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:pb-28 lg:pt-24">
          <div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
              <Badge tone="blue">
                <Sparkles className="size-3.5" aria-hidden />
                Adaptive learning, not a video library
              </Badge>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.05 }}
              className="mt-6 text-4xl font-semibold leading-[1.06] sm:text-5xl lg:text-[3.6rem]"
            >
              A university that
              <br />
              <span className="text-gradient">adapts to you.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.12 }}
              className="mt-6 max-w-lg text-base leading-relaxed text-fog-300 sm:text-lg"
            >
              Attestive measures what you know, builds a roadmap around your career goal, and pairs
              you with an AI teacher that explains at your level — then makes you prove it in code.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.18 }}
              className="mt-8 flex flex-col gap-3 sm:flex-row"
            >
              <Link to="/register">
                <Button size="lg" className="w-full sm:w-auto">
                  Start learning free
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </Link>
              <Link to="/features">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                  Explore the platform
                </Button>
              </Link>
            </motion.div>

            <motion.ul
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-xs text-fog-400"
            >
              {["No credit card", "AI tutor that adapts to you", "Your data stays yours"].map((item) => (
                <li key={item} className="flex items-center gap-1.5">
                  <Check className="size-3.5 text-emerald" aria-hidden />
                  {item}
                </li>
              ))}
            </motion.ul>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="relative"
          >
            <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-br from-electric/15 via-violet/10 to-transparent blur-2xl" aria-hidden />
            <Panel className="relative overflow-hidden p-1.5 shadow-2xl">
              <div className="rounded-lg border border-line bg-ink-900">
                <div className="flex items-center justify-between border-b border-line px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="size-2 rounded-full bg-rose/70" />
                    <span className="size-2 rounded-full bg-amber/70" />
                    <span className="size-2 rounded-full bg-emerald/70" />
                  </div>
                  <span className="text-[11px] tracking-wide text-fog-500">learning-path.preview</span>
                  <Gauge className="size-3.5 text-fog-500" aria-hidden />
                </div>

                <div className="space-y-4 p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.14em] text-fog-500">Your path</p>
                      <p className="mt-1 text-sm font-medium text-fog-100">Backend engineering</p>
                    </div>
                    <Badge tone="violet">Personalised</Badge>
                  </div>

                  <div className="space-y-2">
                    {[
                      { title: "Python foundations", state: "done" },
                      { title: "Functions, scope & data", state: "active" },
                      { title: "Testing with pytest", state: "next" },
                      { title: "Project · CLI task tracker", state: "project" },
                    ].map((item) => (
                      <div
                        key={item.title}
                        className="flex items-center gap-3 rounded-lg border border-line bg-ink-850 px-3 py-2.5"
                      >
                        <span
                          className={
                            item.state === "done"
                              ? "flex size-5 items-center justify-center rounded-full bg-emerald/15 text-emerald"
                              : item.state === "active"
                                ? "flex size-5 items-center justify-center rounded-full bg-electric/15 text-electric"
                                : "flex size-5 items-center justify-center rounded-full border border-line text-fog-500"
                          }
                        >
                          {item.state === "done" ? (
                            <Check className="size-3" aria-hidden />
                          ) : item.state === "active" ? (
                            <span className="size-1.5 rounded-full bg-electric" />
                          ) : (
                            <span className="size-1.5 rounded-full bg-fog-500/60" />
                          )}
                        </span>
                        <span className="flex-1 text-xs text-fog-200">{item.title}</span>
                        {item.state === "project" ? (
                          <span className="font-mono text-[10px] text-fog-500">build</span>
                        ) : null}
                      </div>
                    ))}
                  </div>

                  <div className="rounded-lg border border-line bg-ink-850 p-3">
                    <div className="flex items-center gap-2 text-xs text-fog-300">
                      <BrainCircuit className="size-3.5 text-violet" aria-hidden />
                      Tutor note
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-fog-400">
                      You understood closures quickly but mixed up mutable default arguments. Let's
                      fix that with a three-line exercise before moving on.
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-fog-500">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="size-3.5" aria-hidden />
                      Sandboxed practice
                    </span>
                    <span>Illustrative preview</span>
                  </div>
                </div>
              </div>
            </Panel>
          </motion.div>
        </div>
      </section>

      <section className="border-y border-line bg-ink-900/40">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-14 sm:px-8 md:grid-cols-3">
          {[
            {
              step: "01",
              title: "Tell us where you're headed",
              body: "Education, experience, available hours and the role you want. Three short steps, not a survey.",
            },
            {
              step: "02",
              title: "Find out what you really know",
              body: "A diagnostic maps strengths and weak concepts, then seeds a proficiency estimate you can improve.",
            },
            {
              step: "03",
              title: "Learn, build, prove",
              body: "Work through an adaptive roadmap with a tutor at your side, then demonstrate mastery in projects.",
            },
          ].map((item) => (
            <motion.div key={item.step} {...fadeUp} className="flex gap-4">
              <span className="font-mono text-xs text-fog-500">{item.step}</span>
              <div>
                <h2 className="text-sm font-semibold text-fog-100">{item.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-fog-400">{item.body}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-5 py-20 sm:px-8">
        <motion.div {...fadeUp} className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-fog-500">The platform</p>
          <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">
            Seven systems, one learning loop
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-fog-400">
            Attestive is built from specialised services rather than one oversized prompt. Each
            agent has a validated input, a validated output, and no direct write access to your data.
          </p>
        </motion.div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {pillars.map((pillar, index) => (
            <motion.div
              key={pillar.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: (index % 3) * 0.06 }}
            >
              <Panel className="group h-full p-5 transition-colors hover:border-line-bright">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex size-9 items-center justify-center rounded-lg border border-line bg-ink-800 text-electric transition-colors group-hover:text-violet">
                    <pillar.icon className="size-4" aria-hidden />
                  </div>
                  <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-fog-500">
                    {pillar.tag}
                  </span>
                </div>
                <h3 className="mt-4 text-sm font-semibold text-fog-100">{pillar.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-fog-400">{pillar.body}</p>
              </Panel>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-ink-900/40">
        <div className="mx-auto grid w-full max-w-6xl gap-12 px-5 py-20 sm:px-8 lg:grid-cols-2 lg:items-center">
          <motion.div {...fadeUp}>
            <Badge tone="violet">
              <GraduationCap className="size-3.5" aria-hidden />
              Teaching principles
            </Badge>
            <h2 className="mt-5 text-3xl font-semibold sm:text-4xl">
              Answers are cheap.
              <br />
              Understanding is the product.
            </h2>
            <p className="mt-4 max-w-lg text-sm leading-relaxed text-fog-400">
              The tutor is deliberately restrained. It recognises confusion, offers progressively
              stronger hints, and only shows a full solution once reasoning has been attempted.
            </p>

            <ul className="mt-8 space-y-3">
              {principles.map((principle) => (
                <li key={principle} className="flex gap-3 text-sm text-fog-300">
                  <Check className="mt-0.5 size-4 shrink-0 text-emerald" aria-hidden />
                  <span className="leading-relaxed">{principle}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div {...fadeUp} className="space-y-3">
            <Panel className="overflow-hidden">
              <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
                <span className="font-mono text-[11px] text-fog-500">exercise.py</span>
                <Badge tone="amber">Hint 1 of 3</Badge>
              </div>
              <pre className="overflow-x-auto p-4 font-mono text-[12.5px] leading-relaxed text-fog-300">
                <code>{`def average(values):
    total = 0
    for value in values:
        total += value
    return total / len(values)

print(average([]))   # what happens here?`}</code>
              </pre>
            </Panel>
            <Panel className="border-electric/25 bg-electric/[0.04] p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-[#a9c7ff]">
                <BrainCircuit className="size-4" aria-hidden />
                Tutor
              </div>
              <p className="mt-2 text-sm leading-relaxed text-fog-300">
                Before I show you the fix: what is <code className="font-mono text-fog-100">len(values)</code>{" "}
                when the list is empty, and what does dividing by it mean? Decide how you want the
                function to behave, then we'll write it.
              </p>
            </Panel>
            <div className="grid gap-3 sm:grid-cols-2">
              <Panel className="p-4">
                <Code2 className="size-4 text-cyan" aria-hidden />
                <h3 className="mt-2 text-sm font-medium text-fog-100">Isolated execution</h3>
                <p className="mt-1 text-xs leading-relaxed text-fog-400">
                  Timeouts, memory caps and no network for every submission.
                </p>
              </Panel>
              <Panel className="p-4">
                <Boxes className="size-4 text-violet" aria-hidden />
                <h3 className="mt-2 text-sm font-medium text-fog-100">Modular by design</h3>
                <p className="mt-1 text-xs leading-relaxed text-fog-400">
                  Swap models or providers without rewriting the product.
                </p>
              </Panel>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-5 py-20 sm:px-8">
        <Panel className="relative overflow-hidden px-6 py-12 text-center sm:px-12">
          <div
            className="absolute inset-x-0 -top-24 mx-auto size-72 rounded-full bg-violet/20 blur-[100px]"
            aria-hidden
          />
          <div className="relative">
            <h2 className="text-3xl font-semibold sm:text-4xl">Start with what you know.</h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-fog-400">
              Create an account, complete a three-step profile, and see an honest baseline. Your
              roadmap follows the evidence.
            </p>
            <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
              <Link to="/register">
                <Button size="lg">
                  Create your account
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </Link>
              <Link to="/about">
                <Button size="lg" variant="secondary">
                  Why we built this
                </Button>
              </Link>
            </div>
          </div>
        </Panel>
      </section>
    </MarketingLayout>
  );
}
