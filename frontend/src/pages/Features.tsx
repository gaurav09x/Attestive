import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  ClipboardCheck,
  Code2,
  Compass,
  Flame,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { MarketingLayout } from "../components/layout/MarketingLayout";
import { Badge, Button, Panel } from "../components/ui";

const modules = [
  {
    icon: Target,
    phase: "Phase 2",
    title: "Adaptive assessment",
    summary: "Find the real starting point.",
    points: [
      "Diagnostics generated per subject, mixing multiple choice, short answer, conceptual and coding questions.",
      "Per-skill scoring instead of a single grade, with weak concepts recorded explicitly.",
      "Proficiency is revised as lessons, exercises and later assessments add evidence.",
    ],
  },
  {
    icon: Route,
    phase: "Phase 2",
    title: "Personalised roadmap",
    summary: "A sequence you can actually finish.",
    points: [
      "Modules with prerequisites, objectives and realistic time estimates.",
      "Practice, assessments and projects placed where they reinforce the concept.",
      "The plan adapts when your performance shows a gap or a shortcut.",
    ],
  },
  {
    icon: BrainCircuit,
    phase: "Phase 3",
    title: "AI teacher",
    summary: "Explanations at your level, not a wall of text.",
    points: [
      "Beginner-to-advanced explanations with real-world examples and line-by-line code walkthroughs.",
      "Progressive hints before solutions; misconceptions named and corrected.",
      "Session memory backed by the database, plus retrieval from your subject material.",
    ],
  },
  {
    icon: Code2,
    phase: "Phase 4",
    title: "Coding lab",
    summary: "Write it, run it, understand the failure.",
    points: [
      "Python, JavaScript and C++ with an editor, syntax highlighting and visible test results.",
      "AI review that explains errors rather than quietly rewriting your code.",
      "Execution in an isolated worker with timeouts, memory limits and no network access.",
    ],
  },
  {
    icon: BarChart3,
    phase: "Phase 5",
    title: "Learning analytics",
    summary: "Evidence, not vanity metrics.",
    points: [
      "Study time and streaks from recorded activity, not page loads.",
      "Subject proficiency, assessment history and improvement trends.",
      "Revision topics ranked by weak concepts and time since practice.",
    ],
  },
  {
    icon: Flame,
    phase: "Phase 5",
    title: "Gamification",
    summary: "Reward mastery, not clicks.",
    points: [
      "XP ledger for completed lessons, solved exercises, projects and assessments.",
      "Levels, achievements and weekly challenges with transparent criteria.",
      "Streaks that count genuine study days.",
    ],
  },
  {
    icon: Compass,
    phase: "Phase 6",
    title: "Career development",
    summary: "Map learning to the role you want.",
    points: [
      "Skill-gap analysis against a target role, with prioritised next steps.",
      "Portfolio project recommendations that demonstrate the missing skills.",
      "Technical mock interviews with structured feedback — never a readiness guarantee.",
    ],
  },
  {
    icon: ClipboardCheck,
    phase: "Phase 1 · live",
    title: "Accounts and onboarding",
    summary: "A real identity and a real profile.",
    points: [
      "JWT access tokens with rotating refresh tokens stored as hashes.",
      "Argon2 password hashing, role-based access control and per-user data scoping.",
      "Progressive three-step onboarding that stores education, goals, subjects and study time.",
    ],
  },
  {
    icon: Sparkles,
    phase: "Phase 1 · live",
    title: "Student dashboard",
    summary: "Your actual state, not a mock-up.",
    points: [
      "XP, level, streak and weekly goal computed from your own records.",
      "Course progress, skills acquired and upcoming assessments from the database.",
      "Empty states that tell the truth when there is no evidence yet.",
    ],
  },
];

export default function Features() {
  return (
    <MarketingLayout>
      <section className="relative border-b border-line">
        <div className="absolute inset-0 bg-grid opacity-50" aria-hidden />
        <div className="relative mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 lg:py-20">
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge tone="blue">Product map</Badge>
            <h1 className="mt-5 max-w-2xl text-4xl font-semibold leading-tight sm:text-5xl">
              Built in phases. <span className="text-gradient">Nothing faked.</span>
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-fog-300">
              Each module below is a real system with a data model, an API boundary and a test
              surface. Phase 1 is running today; later phases are labelled so you always know what
              is live.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8">
        <div className="grid gap-4 md:grid-cols-2">
          {modules.map((module, index) => (
            <motion.div
              key={module.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: (index % 2) * 0.05 }}
            >
              <Panel className="h-full p-6">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex size-10 items-center justify-center rounded-lg border border-line bg-ink-800 text-electric">
                    <module.icon className="size-5" aria-hidden />
                  </div>
                  <Badge tone={module.phase.includes("live") ? "emerald" : "neutral"}>{module.phase}</Badge>
                </div>
                <h2 className="mt-4 text-lg font-semibold">{module.title}</h2>
                <p className="mt-1 text-sm text-fog-400">{module.summary}</p>
                <ul className="mt-5 space-y-2.5">
                  {module.points.map((point) => (
                    <li key={point} className="flex gap-2.5 text-sm leading-relaxed text-fog-300">
                      <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-electric/70" />
                      {point}
                    </li>
                  ))}
                </ul>
              </Panel>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-t border-line bg-ink-900/40">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-16 sm:px-8 md:grid-cols-3">
          {[
            {
              icon: ShieldCheck,
              title: "Security is not a phase",
              body: "Hashed refresh tokens, strict per-user queries, origin checks on cookie endpoints, and a sandboxed runner for untrusted code.",
            },
            {
              icon: BrainCircuit,
              title: "Model independence",
              body: "Agents talk to a provider abstraction. Ollama locally today; another provider later without touching product logic.",
            },
            {
              icon: BarChart3,
              title: "Postgres is the truth",
              body: "Vector search is for retrieval only. Your progress, attempts and XP live in relational tables with real constraints.",
            },
          ].map((item) => (
            <div key={item.title}>
              <item.icon className="size-5 text-violet" aria-hidden />
              <h2 className="mt-3 text-sm font-semibold">{item.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-fog-400">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-5 py-16 text-center sm:px-8">
        <h2 className="text-2xl font-semibold sm:text-3xl">See the honest baseline for yourself.</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-fog-400">
          Phase 1 accounts, onboarding and dashboard are live. Your first dashboard will show zeros —
          because you haven't studied yet.
        </p>
        <Link to="/register" className="mt-7 inline-block">
          <Button size="lg">
            Create your account
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        </Link>
      </section>
    </MarketingLayout>
  );
}
