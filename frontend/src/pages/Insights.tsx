import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  BarChart3,
  ClipboardCheck,
  Clock3,
  Flame,
  Lightbulb,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Badge, Button, EmptyState, Panel, Progress, Spinner, cn } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import { formatMinutes } from "../lib/format";
import type { AnalyticsResponse } from "../lib/types";

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Panel className="p-4">
      <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-fog-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
      <p className="mt-0.5 text-xs text-fog-500">{hint}</p>
    </Panel>
  );
}

function dayLabel(day: string): string {
  const parsed = new Date(`${day}T00:00:00`);
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function Insights() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<AnalyticsResponse>("/analytics/overview")
      .then((payload) => active && setData(payload))
      .catch((caught) => {
        if (active) {
          setError(caught instanceof ApiError ? caught.message : "Could not load your analytics.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Analytics unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{error}</p>
        <Link to="/dashboard" className="mt-5 inline-block">
          <Button>Back to dashboard</Button>
        </Link>
      </Panel>
    );
  }

  if (!data) return <Spinner label="Computing your analytics…" />;

  const maxMinutes = Math.max(10, ...data.activity.map((point) => point.minutes));
  const activeDays = data.activity.filter((point) => point.minutes > 0).length;
  const kindTotal = data.study_by_kind.reduce((sum, item) => sum + item.minutes, 0);
  const hasActivity = data.totals.minutes > 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Insights</h1>
          <p className="mt-1 text-sm text-fog-400">
            Every figure is computed from recorded activity and assessment evidence.
          </p>
        </div>
        <Badge tone="neutral">
          <BarChart3 className="size-3" aria-hidden />
          Last {data.range_days} days
        </Badge>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="Study time"
          value={formatMinutes(data.totals.minutes)}
          hint={`${activeDays} active ${activeDays === 1 ? "day" : "days"} in range`}
        />
        <Stat label="XP earned" value={`${data.totals.xp} XP`} hint="From recorded activity only" />
        <Stat
          label="Streak"
          value={`${data.totals.streak_days} ${data.totals.streak_days === 1 ? "day" : "days"}`}
          hint={data.totals.streak_days > 0 ? "Keep it alive today" : "Study today to start one"}
        />
        <Stat
          label="Diagnostics"
          value={String(data.totals.assessments_completed)}
          hint={`${data.totals.roadmap_items_completed} roadmap steps completed`}
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        <Panel className="p-5">
          <div className="flex items-end justify-between gap-3">
            <div>
              <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
                <Clock3 className="size-4 text-fog-400" aria-hidden />
                Daily study minutes
              </h2>
              <p className="mt-0.5 text-xs text-fog-500">
                {hasActivity
                  ? `${formatMinutes(data.totals.minutes)} across ${activeDays} days`
                  : "Nothing recorded yet"}
              </p>
            </div>
            <span className="font-mono text-xs text-fog-500">peak {maxMinutes}m</span>
          </div>

          <div
            className="mt-5 flex h-36 items-end gap-[3px]"
            role="img"
            aria-label={`Study minutes for the last ${data.range_days} days`}
          >
            {data.activity.map((point) => {
              const height = point.minutes > 0 ? Math.max(4, (point.minutes / maxMinutes) * 100) : 2;
              return (
                <div
                  key={point.day}
                  className="group relative flex-1"
                  title={`${dayLabel(point.day)}: ${point.minutes} minutes, ${point.xp} XP`}
                >
                  <div className="flex h-36 items-end">
                    <div
                      style={{ height: `${height}%` }}
                      className={cn(
                        "w-full rounded-t-[2px]",
                        point.minutes > 0
                          ? "bg-gradient-to-t from-electric/30 to-cyan/80"
                          : "bg-ink-700",
                      )}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-fog-500">
            <span>{dayLabel(data.activity[0]?.day ?? "")}</span>
            <span>{dayLabel(data.activity[data.activity.length - 1]?.day ?? "")}</span>
          </div>
        </Panel>

        <Panel className="p-5">
          <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
            <TrendingUp className="size-4 text-fog-400" aria-hidden />
            Where your time went
          </h2>
          {data.study_by_kind.length > 0 && kindTotal > 0 ? (
            <ul className="mt-4 space-y-3">
              {data.study_by_kind.map((item) => (
                <li key={item.kind}>
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="capitalize text-fog-300">{item.kind.replace(/_/g, " ")}</span>
                    <span className="text-fog-500">{formatMinutes(item.minutes)}</span>
                  </div>
                  <Progress
                    value={kindTotal ? (item.minutes / kindTotal) * 100 : 0}
                    className="mt-1.5"
                    tone="violet"
                  />
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-xs leading-relaxed text-fog-500">
              Study minutes appear here once you complete a diagnostic or close a roadmap step.
              Tutoring records a study event without inventing minutes.
            </p>
          )}
        </Panel>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5">
          <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
            <ClipboardCheck className="size-4 text-fog-400" aria-hidden />
            Assessment trend
          </h2>
          {data.assessment_trend.length > 0 ? (
            <div className="mt-4 flex h-32 items-end gap-2">
              {data.assessment_trend.map((point) => (
                <div key={point.attempt_id} className="flex flex-1 flex-col items-center gap-1.5">
                  <div className="flex h-24 w-full items-end">
                    <div
                      title={`${point.subject_name}: ${Math.round(point.score_percent)}%`}
                      style={{ height: `${Math.max(4, point.score_percent)}%` }}
                      className="w-full rounded-t-[3px] bg-gradient-to-t from-violet/30 to-violet/80"
                    />
                  </div>
                  <span className="text-[10px] text-fog-500">{Math.round(point.score_percent)}%</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-xs leading-relaxed text-fog-500">
              No completed diagnostics yet.{" "}
              <Link to="/assessments" className="text-fog-300 underline-offset-4 hover:underline">
                Take one
              </Link>{" "}
              to start the trend.
            </p>
          )}
        </Panel>

        <Panel className="p-5">
          <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
            <Target className="size-4 text-fog-400" aria-hidden />
            Subject proficiency
          </h2>
          {data.subjects.length > 0 ? (
            <ul className="mt-4 space-y-3.5">
              {data.subjects.map((subject) => (
                <li key={subject.subject_id}>
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <span className="text-fog-200">{subject.subject_name}</span>
                    <span className="text-xs text-fog-500">
                      {subject.average_proficiency}% · {subject.skills_tracked} skills
                    </span>
                  </div>
                  <Progress value={subject.average_proficiency} className="mt-1.5" />
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              compact
              icon={<Target className="size-5" aria-hidden />}
              title="No proficiency yet"
              description="Finish onboarding and a diagnostic to establish per-skill estimates."
            />
          )}
        </Panel>
      </div>

      <Panel className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
            <Flame className="size-4 text-fog-400" aria-hidden />
            Weakest measured skills
          </h2>
          <Link to="/tutor">
            <Button variant="secondary" size="sm">
              <Zap className="size-3.5" aria-hidden />
              Work on these with the tutor
            </Button>
          </Link>
        </div>

        {data.weak_skills.length > 0 ? (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <ul className="space-y-2">
              {data.weak_skills.map((skill) => (
                <li
                  key={skill.skill_id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-line bg-ink-900/60 px-3 py-2.5"
                >
                  <div>
                    <p className="text-sm text-fog-200">{skill.name}</p>
                    <p className="text-[11px] text-fog-500">
                      {skill.subject_name} · confidence {skill.confidence}%
                    </p>
                  </div>
                  <span className="font-mono text-xs text-amber">{skill.proficiency}%</span>
                </li>
              ))}
            </ul>

            <div className="rounded-lg border border-line bg-ink-900/60 p-4">
              <p className="flex items-center gap-2 text-xs font-medium text-fog-300">
                <Lightbulb className="size-3.5 text-amber" aria-hidden />
                Revision suggestions
              </p>
              <ul className="mt-2 space-y-2 text-xs leading-relaxed text-fog-400">
                {data.revision_suggestions.map((suggestion) => (
                  <li key={suggestion} className="flex gap-2">
                    <span className="text-fog-600">·</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
              <Link
                to="/assessments"
                className="mt-3 inline-flex items-center gap-1 text-xs text-electric hover:underline"
              >
                Retake a diagnostic
                <ArrowUpRight className="size-3" aria-hidden />
              </Link>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-xs leading-relaxed text-fog-500">
            No measured weak skills yet. Proficiency comes from diagnostic evidence, not from
            time on the site.
          </p>
        )}
      </Panel>
    </div>
  );
}
