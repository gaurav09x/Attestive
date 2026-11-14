import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Cpu, Database, Layers, ShieldCheck, Users } from "lucide-react";
import { MarketingLayout } from "../components/layout/MarketingLayout";
import { Badge, Button, Panel } from "../components/ui";

const values = [
  {
    icon: Users,
    title: "Access over exclusivity",
    body: "High-quality technical education should not depend on where you live, what you can pay, or whether you already know someone in the industry.",
  },
  {
    icon: BookOpen,
    title: "Understanding over completion",
    body: "A finished course means little without capability. We optimise for what you can explain, build and debug — and we say so when that isn't proven yet.",
  },
  {
    icon: ShieldCheck,
    title: "Honesty over hype",
    body: "No invented students, no fabricated statistics, no job guarantees. If a capability is not built, the product says which phase it arrives in.",
  },
];

const architecture = [
  {
    icon: Layers,
    title: "Frontend",
    body: "React and TypeScript with Vite, Tailwind and Framer Motion. A small design system keeps typography, surfaces and interaction states consistent.",
  },
  {
    icon: Cpu,
    title: "Backend",
    body: "FastAPI organised by domain: routes stay thin, business rules live in services, and validated schemas define every boundary.",
  },
  {
    icon: Database,
    title: "Data",
    body: "PostgreSQL is authoritative for users, learning state and evidence. ChromaDB is reserved for semantic retrieval, never as a system of record.",
  },
];

export default function About() {
  return (
    <MarketingLayout>
      <section className="relative border-b border-line">
        <div className="absolute inset-0 bg-grid opacity-50" aria-hidden />
        <div className="relative mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 lg:py-24">
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge tone="violet">Our mission</Badge>
            <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
              Make a genuinely personal education
              <span className="text-gradient"> available to anyone.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-relaxed text-fog-300">
              Most online learning is a library with a progress bar. Attestive is an attempt at
              something different: a platform that starts from what you already know, teaches toward
              a specific goal, and changes its mind when the evidence changes.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-6xl gap-12 px-5 py-16 sm:px-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h2 className="text-2xl font-semibold sm:text-3xl">The central idea</h2>
          <p className="mt-4 text-sm leading-relaxed text-fog-400">
            Every student learns differently. A mechanical engineering graduate switching into
            backend development does not need the same sequence as a computer science student
            preparing for algorithms interviews. Treating them identically wastes the one resource
            that actually matters: focused attention.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-fog-400">
            Attestive keeps a measured estimate of your knowledge per skill, plans around your
            available study time, and uses a tutor that can explain the same idea three ways. When
            you fail a question, that is information — not a verdict.
          </p>
        </div>
        <Panel className="p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-fog-500">
            Who it is for
          </p>
          <ul className="mt-4 space-y-4 text-sm leading-relaxed text-fog-300">
            <li>
              <span className="font-medium text-fog-100">College students</span> who want structure
              beyond lecture slides and a way to see their own gaps.
            </li>
            <li>
              <span className="font-medium text-fog-100">Fresh graduates</span> preparing for
              technical roles who need practice, projects and honest feedback.
            </li>
            <li>
              <span className="font-medium text-fog-100">Career switchers</span> with limited weekly
              hours who need a plan that respects that constraint.
            </li>
          </ul>
          <div className="mt-6 border-t border-line pt-4 text-xs leading-relaxed text-fog-500">
            Initial focus: Python, JavaScript and the web, data structures, SQL, machine learning
            foundations and system design.
          </div>
        </Panel>
      </section>

      <section className="border-y border-line bg-ink-900/40">
        <div className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8">
          <h2 className="text-2xl font-semibold sm:text-3xl">What we optimise for</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {values.map((value) => (
              <div key={value.title}>
                <value.icon className="size-5 text-electric" aria-hidden />
                <h3 className="mt-3 text-sm font-semibold">{value.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-fog-400">{value.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold sm:text-3xl">How it is built</h2>
          <p className="mt-3 text-sm leading-relaxed text-fog-400">
            The architecture is deliberately modular so that a model, an execution backend or a
            vector store can be replaced without rewriting the learning experience.
          </p>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {architecture.map((item) => (
            <Panel key={item.title} className="p-5">
              <item.icon className="size-5 text-violet" aria-hidden />
              <h3 className="mt-3 text-sm font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-fog-400">{item.body}</p>
            </Panel>
          ))}
        </div>
        <p className="mt-6 max-w-3xl text-xs leading-relaxed text-fog-500">
          AI agents return structured, schema-validated results and never write to the database
          directly. All state changes pass through backend services that enforce ownership and
          validate input. If the local model is unavailable, the platform degrades to
          deterministic behaviour instead of pretending an answer exists.
        </p>
      </section>

      <section className="border-t border-line">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-6 px-5 py-14 sm:flex-row sm:items-center sm:px-8">
          <div>
            <h2 className="text-2xl font-semibold">Build the skill, not the streak.</h2>
            <p className="mt-2 text-sm text-fog-400">Start with three short onboarding steps.</p>
          </div>
          <Link to="/register">
            <Button size="lg">
              Create your account
              <ArrowRight className="size-4" aria-hidden />
            </Button>
          </Link>
        </div>
      </section>
    </MarketingLayout>
  );
}
