import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  BrainCircuit,
  Check,
  Clock3,
  Flag,
  Play,
  Route,
  Sparkles,
} from "lucide-react";
import { Badge, Button, EmptyState, Panel, Progress, Spinner, cn } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import { formatMinutes } from "../lib/format";
import type { RoadmapData } from "../lib/types";

interface RoadmapList {
  items: RoadmapData[];
}

export default function RoadmapPage() {
  const [searchParams] = useSearchParams();
  const subjectParam = searchParams.get("subject");

  const [paths, setPaths] = useState<RoadmapData[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [updatingItem, setUpdatingItem] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<RoadmapList>("/roadmaps")
      .then((data) => {
        if (!active) return;
        setPaths(data.items);
        const preferred =
          data.items.find((item) => subjectParam && item.subject_slug === subjectParam) ??
          data.items.find((item) => item.status === "active") ??
          data.items[0];
        setSelectedId(preferred?.id ?? null);
      })
      .catch(
        (caught) =>
          active &&
          setError(caught instanceof ApiError ? caught.message : "Could not load your roadmaps."),
      );
    return () => {
      active = false;
    };
  }, [subjectParam]);

  if (error) {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Roadmaps unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{error}</p>
        <Link to="/dashboard" className="mt-5 inline-block">
          <Button>Back to dashboard</Button>
        </Link>
      </Panel>
    );
  }

  if (!paths) return <Spinner label="Loading your roadmap…" />;

  if (paths.length === 0) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">Your roadmap</h1>
          <p className="mt-1 text-sm text-fog-400">
            A sequence built from measured gaps, not a generic syllabus.
          </p>
        </header>
        <Panel className="p-6">
          <EmptyState
            icon={<Route className="size-5" aria-hidden />}
            title="No roadmap yet"
            description="Take a diagnostic for one of your subjects. Your roadmap is generated from the skills it identifies as needing work."
            action={
              <Link to="/assessments">
                <Button>
                  Take a diagnostic
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </Link>
            }
          />
        </Panel>
      </div>
    );
  }

  const selected =
    paths.find((path) => path.id === selectedId) ?? paths.find((path) => path.status === "active") ?? paths[0];
  const subjects = Array.from(
    new Map(paths.map((path) => [path.subject_slug, path.subject_name])).entries(),
  );
  const aiWritten = selected.generated_by.startsWith("ollama:");

  async function updateItem(itemId: string, status: "in_progress" | "completed") {
    setUpdatingItem(itemId);
    try {
      const updated = await apiFetch<RoadmapData>(
        `/roadmaps/${selected.id}/items/${itemId}`,
        { method: "PATCH", body: JSON.stringify({ status }) },
      );
      setPaths((current) =>
        current ? current.map((path) => (path.id === updated.id ? updated : path)) : current,
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not update that step.");
    } finally {
      setUpdatingItem(null);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{selected.title}</h1>
          <p className="mt-1 text-sm text-fog-400">
            {selected.subject_name} · target {selected.target_level} · about {selected.estimated_weeks}{" "}
            {selected.estimated_weeks === 1 ? "week" : "weeks"} at your study goal
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/assessments">
            <Button variant="secondary" size="sm">
              Retake diagnostic
            </Button>
          </Link>
        </div>
      </header>

      {subjects.length > 1 ? (
        <div className="flex flex-wrap gap-2">
          {subjects.map(([slug, name]) => {
            const path = paths.find((item) => item.subject_slug === slug);
            if (!path) return null;
            return (
              <button
                key={slug}
                type="button"
                onClick={() => setSelectedId(path.id)}
                aria-pressed={selected.subject_slug === slug}
                className={cn(
                  "rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
                  selected.subject_slug === slug
                    ? "border-electric/50 bg-electric/10 text-[#a9c7ff]"
                    : "border-line bg-ink-850 text-fog-400 hover:border-line-bright hover:text-fog-200",
                )}
              >
                {name}
              </button>
            );
          })}
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        <Panel className="p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-medium text-fog-200">Plan note</h2>
            <Badge tone={aiWritten ? "violet" : "neutral"}>
              {aiWritten ? (
                <>
                  <Sparkles className="size-3" aria-hidden />
                  Written by {selected.generated_by.replace("ollama:", "")}
                </>
              ) : (
                <>
                  <BrainCircuit className="size-3" aria-hidden />
                  Evidence-based
                </>
              )}
            </Badge>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-fog-300">{selected.rationale}</p>
          <p className="mt-3 text-xs leading-relaxed text-fog-500">
            {aiWritten
              ? "The model wrote this note from your diagnostic. Module selection and order are computed and validated by the backend."
              : "Generated deterministically from your diagnostic. Configure Ollama to have the roadmap agent write the plan note."}
          </p>

          <div className="mt-5 border-t border-line pt-4">
            <div className="flex items-center justify-between text-xs text-fog-400">
              <span>
                {selected.items_completed} of {selected.items_total} steps complete
              </span>
              <span>{selected.progress_percent}%</span>
            </div>
            <Progress value={selected.progress_percent} className="mt-2" />
          </div>
        </Panel>

        <Panel className="p-5">
          <h2 className="text-sm font-medium text-fog-200">How this plan decides</h2>
          <ul className="mt-3 space-y-3 text-xs leading-relaxed text-fog-400">
            <li className="flex gap-2.5">
              <BadgeCheck className="mt-0.5 size-3.5 shrink-0 text-emerald" aria-hidden />
              Modules covering your weakest measured skills come first.
            </li>
            <li className="flex gap-2.5">
              <BadgeCheck className="mt-0.5 size-3.5 shrink-0 text-emerald" aria-hidden />
              Project work is placed after the concepts it depends on.
            </li>
            <li className="flex gap-2.5">
              <BadgeCheck className="mt-0.5 size-3.5 shrink-0 text-emerald" aria-hidden />
              A new diagnostic replaces this plan instead of silently editing it.
            </li>
            <li className="flex gap-2.5">
              <BadgeCheck className="mt-0.5 size-3.5 shrink-0 text-emerald" aria-hidden />
              Completing a step awards XP once; it does not invent study minutes.
            </li>
          </ul>
        </Panel>
      </div>

      <div className="space-y-3">
        {selected.items.map((item, index) => {
          const completed = item.status === "completed";
          const inProgress = item.status === "in_progress";
          return (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: index * 0.03 }}
            >
              <Panel
                className={cn(
                  "p-4 transition-colors",
                  completed ? "border-emerald/20 bg-emerald/[0.03]" : "",
                )}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={cn(
                      "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-medium",
                      completed
                        ? "bg-emerald/15 text-emerald"
                        : inProgress
                          ? "bg-electric/15 text-electric"
                          : "bg-ink-700 text-fog-400",
                    )}
                  >
                    {completed ? <Check className="size-4" aria-hidden /> : item.position}
                  </span>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3
                        className={cn(
                          "text-sm font-medium",
                          completed ? "text-fog-400 line-through" : "text-fog-100",
                        )}
                      >
                        {item.title}
                      </h3>
                      {item.is_project ? (
                        <Badge tone="amber">
                          <Flag className="size-3" aria-hidden />
                          Project
                        </Badge>
                      ) : null}
                      {inProgress ? <Badge tone="blue">In progress</Badge> : null}
                      {selected.status === "completed" ? (
                        <Badge tone="emerald">Path complete</Badge>
                      ) : null}
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-fog-400">{item.objective}</p>
                    <p className="mt-2 flex items-center gap-1.5 text-[11px] text-fog-500">
                      <Clock3 className="size-3" aria-hidden />
                      {formatMinutes(item.estimated_minutes)}
                    </p>
                  </div>

                  <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
                    {!completed ? (
                      <>
                        {!inProgress ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateItem(item.id, "in_progress")}
                            loading={updatingItem === item.id}
                          >
                            <Play className="size-3.5" aria-hidden />
                            Start
                          </Button>
                        ) : null}
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => updateItem(item.id, "completed")}
                          loading={updatingItem === item.id}
                        >
                          <Check className="size-3.5" aria-hidden />
                          Mark complete
                        </Button>
                      </>
                    ) : (
                      <span className="flex items-center gap-1.5 text-xs text-emerald">
                        <Check className="size-3.5" aria-hidden />
                        Done
                      </span>
                    )}
                  </div>
                </div>
              </Panel>
            </motion.div>
          );
        })}
      </div>

      <p className="text-center text-xs text-fog-500">
        Marking steps complete tracks your plan. Lessons, exercises and projects themselves arrive in
        later phases — this page does not claim otherwise.
      </p>
    </div>
  );
}
