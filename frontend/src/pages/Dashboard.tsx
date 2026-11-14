import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Award,
  BrainCircuit,
  CalendarClock,
  Clock3,
  Compass,
  Flame,
  Layers,
  Lightbulb,
  Route,
  Settings,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { ActivityChart, RadialProgress } from "../components/ActivityChart";
import { Badge, Button, EmptyState, Panel, Progress, Spinner, cn } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatMinutes, greeting, weekdayLabel } from "../lib/format";
import type { DashboardResponse } from "../lib/types";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DashboardResponse };

function StatCard({
  icon,
  label,
  value,
  hint,
  children,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  hint?: string;
  children?: ReactNode;
}) {
  return (
    <Panel className="p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-[0.12em] text-fog-500">
          {label}
        </span>
        <span className="text-fog-400">{icon}</span>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-fog-500">{hint}</p> : null}
      {children ? <div className="mt-3">{children}</div> : null}
    </Panel>
  );
}

function SectionHeader({
  icon,
  title,
  aside,
}: {
  icon: ReactNode;
  title: string;
  aside?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5">
      <div className="flex items-center gap-2 text-sm font-medium text-fog-200">
        <span className="text-fog-400">{icon}</span>
        {title}
      </div>
      {aside}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [reloadKey, setReloadKey] = useState(0);

  const load = useCallback(() => {
    setState({ status: "loading" });
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });

    apiFetch<DashboardResponse>("/dashboard")
      .then((data) => {
        if (active) setState({ status: "ready", data });
      })
      .catch((caught) => {
        if (active) {
          setState({
            status: "error",
            message: caught instanceof ApiError ? caught.message : "Could not load your dashboard.",
          });
        }
      });

    return () => {
      active = false;
    };
  }, [reloadKey]);

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <div className="h-20 animate-pulse rounded-xl bg-ink-850" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="h-28 animate-pulse rounded-xl bg-ink-850" />
          ))}
        </div>
        <Spinner label="Loading your learning state…" />
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">We couldn't load your dashboard</h1>
        <p className="mt-2 text-sm text-fog-400">{state.message}</p>
        <div className="mt-5 flex justify-center gap-2">
          <Button onClick={load}>Try again</Button>
          <Link to="/settings">
            <Button variant="secondary">Open settings</Button>
          </Link>
        </div>
      </Panel>
    );
  }

  const data = state.data;
  const firstName = data.user.first_name || user?.full_name.split(" ")[0] || "there";
  const weeklyPercent = data.weekly_goal.percent;
  const todayLabel = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-6"
    >
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs text-fog-500">{todayLabel}</p>
          <h1 className="mt-1 text-2xl font-semibold sm:text-[1.75rem]">
            {greeting()}, {firstName}.
          </h1>
          <p className="mt-1.5 text-sm text-fog-400">
            {data.current_path
              ? `You're working through ${data.current_path.subject_name}. ${data.current_path.items_completed} of ${data.current_path.items_total} steps complete.`
              : "This is your honest starting point. Nothing here is simulated."}
          </p>
          {data.user.subjects.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {data.user.subjects.map((subject) => (
                <Badge key={subject.id} tone="neutral">
                  {subject.name}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex shrink-0 gap-2">
          <Link to="/settings">
            <Button variant="secondary" size="sm">
              <Settings className="size-4" aria-hidden />
              Settings
            </Button>
          </Link>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={<Zap className="size-4" aria-hidden />}
          label="Level"
          value={String(data.level.level)}
          hint={`${data.level.xp_total} XP total`}
        >
          <Progress value={data.level.progress_percent} />
          <p className="mt-1.5 text-[11px] text-fog-500">
            {data.level.xp_into_level}/{data.level.xp_for_next_level} XP to level {data.level.level + 1}
          </p>
        </StatCard>

        <StatCard
          icon={<Flame className="size-4" aria-hidden />}
          label="Learning streak"
          value={`${data.user.streak_days} ${data.user.streak_days === 1 ? "day" : "days"}`}
          hint={
            data.user.streak_days > 0
              ? "Keep it alive with a session today"
              : "Study today to start a streak"
          }
        />

        <StatCard
          icon={<Clock3 className="size-4" aria-hidden />}
          label="Learning time"
          value={formatMinutes(data.stats.total_learning_minutes)}
          hint={`${data.stats.lessons_completed} lessons completed`}
        />

        <StatCard
          icon={<Target className="size-4" aria-hidden />}
          label="Skills acquired"
          value={String(data.stats.skills_acquired)}
          hint="Proficiency of 60% or higher"
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.55fr_1fr]">
        <div className="space-y-5">
          <Panel>
            <SectionHeader
              icon={<Route className="size-4" aria-hidden />}
              title="Current learning path"
              aside={
                data.current_path ? (
                  <div className="flex items-center gap-2">
                    <Badge tone="blue">{data.current_path.progress_percent}% complete</Badge>
                    <Link
                      to="/roadmap"
                      className="inline-flex items-center gap-1 text-xs text-electric hover:underline"
                    >
                      Open
                      <ArrowUpRight className="size-3" aria-hidden />
                    </Link>
                  </div>
                ) : (
                  <Badge tone="neutral">Not generated</Badge>
                )
              }
            />
            <div className="p-5">
              {data.current_path ? (
                <div>
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h2 className="text-base font-semibold">{data.current_path.title}</h2>
                      <p className="mt-1 text-xs text-fog-400">
                        {data.current_path.subject_name} · {data.current_path.estimated_weeks} weeks ·{" "}
                        {data.current_path.target_level}
                      </p>
                    </div>
                    <Badge tone="violet">{data.current_path.items_completed}/{data.current_path.items_total} steps</Badge>
                  </div>
                  {data.current_path.rationale ? (
                    <p className="mt-3 max-w-2xl text-sm leading-relaxed text-fog-400">
                      {data.current_path.rationale}
                    </p>
                  ) : null}

                  <div className="mt-4 space-y-2">
                    {data.current_path.items.map((item) => (
                      <div
                        key={item.id}
                        className={cn(
                          "flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm",
                          item.status === "completed"
                            ? "border-emerald/20 bg-emerald/[0.04] text-fog-300"
                            : "border-line bg-ink-900/60 text-fog-200",
                        )}
                      >
                        <span
                          className={cn(
                            "flex size-5 shrink-0 items-center justify-center rounded-full text-[10px] font-medium",
                            item.status === "completed"
                              ? "bg-emerald/15 text-emerald"
                              : "bg-ink-700 text-fog-400",
                          )}
                        >
                          {item.status === "completed" ? "✓" : item.position}
                        </span>
                        <span className="flex-1">{item.title}</span>
                        {item.is_project ? <Badge tone="amber">Project</Badge> : null}
                        <span className="font-mono text-[11px] text-fog-500">
                          {formatMinutes(item.estimated_minutes)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={<Compass className="size-5" aria-hidden />}
                  title="No roadmap yet"
                  description="Your roadmap is generated from diagnostic evidence: the skills you miss determine the module order. Take a diagnostic to create your first plan."
                  action={
                    <Link to="/assessments">
                      <Button size="sm">
                        Take a diagnostic
                        <ArrowUpRight className="size-4" aria-hidden />
                      </Button>
                    </Link>
                  }
                />
              )}
            </div>
          </Panel>

          <Panel className="p-5">
            <ActivityChart days={data.activity_series} />
            <div className="mt-5 flex items-center justify-between border-t border-line pt-4 text-xs text-fog-500">
              <span>Recorded study activity</span>
              <span className="flex items-center gap-1.5">
                <TrendingUp className="size-3.5" aria-hidden />
                {formatMinutes(data.stats.total_learning_minutes)} all-time
              </span>
            </div>
          </Panel>

          <Panel>
            <SectionHeader
              icon={<Layers className="size-4" aria-hidden />}
              title="Skills in progress"
              aside={<span className="text-[11px] text-fog-500">Self-reported until assessed</span>}
            />
            <div className="p-5">
              {data.top_skills.length > 0 ? (
                <ul className="space-y-3.5">
                  {data.top_skills.map((skill) => (
                    <li key={skill.name}>
                      <div className="flex items-baseline justify-between gap-3 text-sm">
                        <span className="text-fog-200">{skill.name}</span>
                        <span className="text-xs text-fog-500">
                          {skill.subject_name} · {skill.proficiency}%
                        </span>
                      </div>
                      <Progress value={skill.proficiency} className="mt-1.5" tone="violet" />
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  compact
                  icon={<Target className="size-5" aria-hidden />}
                  title="No proficiency signal yet"
                  description="Complete onboarding and an assessment to establish a first estimate."
                />
              )}
            </div>
          </Panel>
        </div>

        <div className="space-y-5">
          <Panel className="p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-medium text-fog-200">This week's goal</h2>
              <Badge tone={weeklyPercent >= 100 ? "emerald" : "neutral"}>
                {formatMinutes(data.weekly_goal.completed_minutes)} /{" "}
                {formatMinutes(data.weekly_goal.target_minutes)}
              </Badge>
            </div>
            <div className="mt-4 flex flex-col items-center gap-4">
              <RadialProgress
                value={weeklyPercent}
                label={`${weeklyPercent}%`}
                caption={`${formatMinutes(Math.max(0, data.weekly_goal.target_minutes - data.weekly_goal.completed_minutes))} remaining`}
              />
              <p className="text-center text-xs leading-relaxed text-fog-500">
                {weeklyPercent === 0
                  ? "No study sessions recorded this week yet. The goal is based on the time you chose."
                  : "Progress comes only from recorded learning activity."}
              </p>
            </div>
          </Panel>

          <Panel>
            <SectionHeader
              icon={<CalendarClock className="size-4" aria-hidden />}
              title="Upcoming assessments"
            />
            <div className="p-4">
              {data.upcoming_assessments.length > 0 ? (
                <ul className="space-y-2">
                  {data.upcoming_assessments.map((assessment) => (
                    <li
                      key={assessment.id}
                      className="rounded-lg border border-line bg-ink-900/60 px-3 py-2.5"
                    >
                      <p className="text-sm text-fog-200">{assessment.title}</p>
                      <p className="mt-0.5 text-xs text-fog-500">
                        {assessment.subject_name} · {assessment.kind.replace("_", " ")} ·{" "}
                        {formatMinutes(assessment.estimated_minutes)}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  compact
                  icon={<CalendarClock className="size-5" aria-hidden />}
                  title="Nothing scheduled"
                  description="Diagnostics are available now. Subject quizzes and project assessments arrive with later phases."
                  action={
                    <Link to="/assessments">
                      <Button size="sm" variant="secondary">
                        Browse diagnostics
                      </Button>
                    </Link>
                  }
                />
              )}
            </div>
          </Panel>

          <Panel>
            <SectionHeader
              icon={<Award className="size-4" aria-hidden />}
              title="Achievements"
              aside={
                <span className="text-[11px] text-fog-500">
                  {data.achievements.length > 0 ? `${data.achievements.length} unlocked` : "None yet"}
                </span>
              }
            />
            <div className="p-4">
              {data.achievements.length > 0 ? (
                <ul className="space-y-2">
                  {data.achievements.map((achievement) => (
                    <li key={achievement.code} className="flex items-start gap-3 rounded-lg border border-line bg-ink-900/60 p-3">
                      <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber/10 text-amber">
                        <Award className="size-4" aria-hidden />
                      </span>
                      <div>
                        <p className="text-sm font-medium text-fog-200">{achievement.name}</p>
                        <p className="text-xs text-fog-500">{achievement.description}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  compact
                  icon={<Award className="size-5" aria-hidden />}
                  title="Nothing unlocked yet"
                  description="Achievements are awarded for measured milestones such as streaks, solved exercises and completed projects."
                />
              )}
            </div>
          </Panel>

          <Panel>
            <SectionHeader
              icon={<Lightbulb className="size-4" aria-hidden />}
              title="Recommended next"
            />
            <div className="p-4">
              {data.recommendations.length > 0 ? (
                <ul className="space-y-2">
                  {data.recommendations.map((recommendation) => (
                    <li key={recommendation.id} className="rounded-lg border border-line bg-ink-900/60 p-3">
                      <p className="text-sm font-medium text-fog-200">{recommendation.title}</p>
                      <p className="mt-0.5 text-xs leading-relaxed text-fog-500">
                        {recommendation.description || recommendation.reason}
                      </p>
                      {recommendation.target_url ? (
                        <Link
                          to={recommendation.target_url}
                          className="mt-2 inline-flex items-center gap-1 text-xs text-electric hover:underline"
                        >
                          Open
                          <ArrowUpRight className="size-3" aria-hidden />
                        </Link>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  compact
                  icon={<BrainCircuit className="size-5" aria-hidden />}
                  title="No recommendations yet"
                  description="Recommendations are created from assessment evidence. Complete a diagnostic to get your first next step."
                  action={
                    <Link to="/assessments">
                      <Button size="sm" variant="secondary">
                        Start a diagnostic
                      </Button>
                    </Link>
                  }
                />
              )}
            </div>
          </Panel>
        </div>
      </div>

      <p className="text-center text-[11px] text-fog-600">
        Dashboard figures are computed from your own records · Updated{" "}
        {weekdayLabel(new Date().toISOString().slice(0, 10))}
      </p>
    </motion.div>
  );
}
