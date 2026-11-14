import { useEffect, useMemo, useState } from "react";
import {
  Award,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  Compass,
  FileText,
  MessageSquare,
  Plus,
  ShieldQuestion,
  Target,
  Trash2,
} from "lucide-react";
import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Field,
  Input,
  Panel,
  Progress,
  Select,
  Spinner,
  Textarea,
  cn,
} from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import type {
  CareerRoleDetail,
  CareerRoleList,
  MockInterview,
  MockInterviewList,
  ResumeSkill,
  ResumeSkillList,
} from "../lib/types";

const readinessTone = {
  interview_ready: "emerald",
  developing: "amber",
  foundation_building: "neutral",
} as const;

function readinessLabel(value: string): string {
  return value.replace(/_/g, " ");
}

export default function Career() {
  const [roles, setRoles] = useState<CareerRoleList | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<CareerRoleDetail | null>(null);
  const [interviews, setInterviews] = useState<MockInterviewList | null>(null);
  const [active, setActive] = useState<MockInterview | null>(null);
  const [claims, setClaims] = useState<ResumeSkillList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState("");
  const [claimLabel, setClaimLabel] = useState("");
  const [claimLevel, setClaimLevel] = useState("unspecified");

  useEffect(() => {
    let live = true;
    Promise.all([
      apiFetch<CareerRoleList>("/career/roles"),
      apiFetch<MockInterviewList>("/career/interviews"),
      apiFetch<ResumeSkillList>("/career/resume-skills"),
    ])
      .then(([roleList, interviewList, claimList]) => {
        if (!live) return;
        setRoles(roleList);
        setInterviews(interviewList);
        setClaims(claimList);
        setSelected(roleList.items[0]?.slug ?? null);
        const inProgress = interviewList.items.find((item) => item.status === "in_progress");
        if (inProgress) {
          void apiFetch<MockInterview>(`/career/interviews/${inProgress.id}`).then((full) => {
            if (live) setActive(full);
          });
        }
      })
      .catch((caught) => {
        if (live) {
          setError(caught instanceof ApiError ? caught.message : "Could not load career tools.");
        }
      });
    return () => {
      live = false;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let live = true;
    setDetail(null);
    apiFetch<CareerRoleDetail>(`/career/roles/${selected}`)
      .then((payload) => {
        if (live) setDetail(payload);
      })
      .catch((caught) => {
        if (live) {
          setError(caught instanceof ApiError ? caught.message : "Could not load this role.");
        }
      });
    return () => {
      live = false;
    };
  }, [selected]);

  const currentQuestion = useMemo(() => {
    if (!active) return null;
    return (
      active.questions.find((question) => question.answer === null) ??
      active.questions[active.questions.length - 1] ??
      null
    );
  }, [active]);

  async function startInterview() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const interview = await apiFetch<MockInterview>("/career/interviews", {
        method: "POST",
        body: JSON.stringify({ role_slug: selected }),
      });
      setActive(interview);
      setDraft("");
      setInterviews(await apiFetch<MockInterviewList>("/career/interviews"));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not start the interview.");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswer() {
    if (!active || !currentQuestion || draft.trim().length < 2) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await apiFetch<MockInterview>(
        `/career/interviews/${active.id}/responses`,
        {
          method: "POST",
          body: JSON.stringify({ question_id: currentQuestion.id, answer: draft }),
        },
      );
      setActive(updated);
      setDraft("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not save that answer.");
    } finally {
      setBusy(false);
    }
  }

  async function completeInterview() {
    if (!active) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await apiFetch<MockInterview>(
        `/career/interviews/${active.id}/complete`,
        { method: "POST" },
      );
      setActive(updated);
      setInterviews(await apiFetch<MockInterviewList>("/career/interviews"));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not complete the interview.");
    } finally {
      setBusy(false);
    }
  }

  async function addClaim() {
    if (claimLabel.trim().length < 2) return;
    setBusy(true);
    setError(null);
    try {
      const created = await apiFetch<ResumeSkill>("/career/resume-skills", {
        method: "POST",
        body: JSON.stringify({ label: claimLabel, claimed_level: claimLevel }),
      });
      setClaims((previous) =>
        previous
          ? { items: [created, ...previous.items] }
          : { items: [created] },
      );
      setClaimLabel("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not add that skill.");
    } finally {
      setBusy(false);
    }
  }

  async function removeClaim(id: string) {
    setBusy(true);
    try {
      await apiFetch<void>(`/career/resume-skills/${id}`, { method: "DELETE" });
      setClaims((previous) =>
        previous ? { items: previous.items.filter((item) => item.id !== id) } : previous,
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not remove that skill.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !roles) {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Career tools unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{error}</p>
      </Panel>
    );
  }

  if (!roles) return <Spinner label="Analysing role requirements against your evidence…" />;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <BriefcaseBusiness className="size-5 text-fog-400" aria-hidden />
            Career readiness
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-fog-400">
            Compare your measured skills with a target role, practise a rubric-scored mock
            interview, and keep your resume claims honest about their evidence.
          </p>
        </div>
        <Badge tone="neutral">
          <Compass className="size-3" aria-hidden />
          {roles.items.length} curated role maps
        </Badge>
      </header>

      {error ? <Alert>{error}</Alert> : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {roles.items.map((role) => (
          <button
            key={role.slug}
            type="button"
            onClick={() => setSelected(role.slug)}
            className={cn(
              "rounded-xl border p-4 text-left transition-colors",
              selected === role.slug
                ? "border-electric/60 bg-ink-800"
                : "border-line bg-ink-850/70 hover:border-line-bright hover:bg-ink-800/70",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-medium text-fog-100">{role.title}</p>
                <p className="mt-0.5 text-[11px] text-fog-500">
                  {role.met_count}/{role.skill_count} required skills met · v{role.version}
                </p>
              </div>
              <Badge tone={readinessTone[role.readiness_label as keyof typeof readinessTone] ?? "neutral"}>
                {role.readiness_score}%
              </Badge>
            </div>
            <Progress value={role.readiness_score} className="mt-3" />
          </button>
        ))}
      </div>

      {detail ? (
        <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
          <Panel className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">{detail.title}</h2>
                <p className="mt-1 max-w-xl text-sm leading-relaxed text-fog-400">
                  {detail.summary}
                </p>
              </div>
              <div className="text-right">
                <p className="font-mono text-2xl text-fog-100">{detail.readiness_score}%</p>
                <p className="text-[11px] uppercase tracking-wide text-fog-500">
                  {readinessLabel(detail.readiness_label)}
                </p>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {detail.skills.map((skill) => (
                <div key={`${skill.subject_name}-${skill.skill_slug}`}>
                  <div className="flex items-baseline justify-between gap-3 text-xs">
                    <span className="text-fog-200">
                      {skill.name}
                      <span className="text-fog-500"> · {skill.subject_name}</span>
                    </span>
                    <span className="text-fog-500">
                      {skill.proficiency}% / {skill.target}%
                      {skill.status === "met" ? (
                        <CheckCircle2 className="ml-1 inline size-3 text-emerald" aria-hidden />
                      ) : null}
                    </span>
                  </div>
                  <Progress
                    value={skill.proficiency}
                    className="mt-1.5"
                    tone={skill.status === "met" ? "emerald" : skill.status === "close" ? "violet" : "blue"}
                  />
                </div>
              ))}
            </div>

            <p className="mt-4 flex items-start gap-2 rounded-lg border border-line bg-ink-900/60 px-3 py-2.5 text-[11px] leading-relaxed text-fog-500">
              <ShieldQuestion className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              {detail.disclaimer}
            </p>
          </Panel>

          <div className="space-y-5">
            <Panel className="p-5">
              <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
                <Target className="size-4 text-fog-400" aria-hidden />
                Priorities from your evidence
              </h2>
              <ul className="mt-3 space-y-3">
                {detail.recommendations.map((item) => (
                  <li key={item.title} className="rounded-lg border border-line bg-ink-900/60 p-3">
                    <p className="text-sm text-fog-200">{item.title}</p>
                    <p className="mt-1 text-xs leading-relaxed text-fog-400">{item.description}</p>
                    <p className="mt-1 text-[11px] text-fog-500">{item.reason}</p>
                  </li>
                ))}
              </ul>
            </Panel>

            <Panel className="p-5">
              <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
                <FileText className="size-4 text-fog-400" aria-hidden />
                Portfolio briefs
              </h2>
              <ul className="mt-3 space-y-3">
                {detail.portfolio_briefs.map((brief) => (
                  <li key={brief.title} className="rounded-lg border border-line bg-ink-900/60 p-3">
                    <p className="text-sm text-fog-200">{brief.title}</p>
                    <p className="mt-1 text-xs leading-relaxed text-fog-400">{brief.brief}</p>
                    {brief.missing_skills.length > 0 ? (
                      <p className="mt-2 text-[11px] text-amber">
                        Demonstrates skills you have not met yet: {brief.missing_skills.join(", ")}
                      </p>
                    ) : (
                      <p className="mt-2 text-[11px] text-emerald">
                        Your measured skills already cover this brief.
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
        </div>
      ) : (
        <Spinner label="Loading role detail…" />
      )}

      <Panel className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
            <MessageSquare className="size-4 text-fog-400" aria-hidden />
            Mock interview{detail ? ` · ${detail.title}` : ""}
          </h2>
          {(!active || active.status === "completed") && (
            <Button size="sm" onClick={startInterview} loading={busy} disabled={!selected}>
              {active ? "Start another interview" : "Start mock interview"}
            </Button>
          )}
        </div>

        {active ? (
          <div className="mt-4 space-y-4">
            <div className="flex flex-wrap items-center gap-3 text-xs text-fog-500">
              <Badge tone={active.status === "completed" ? "emerald" : "blue"}>
                {active.status === "completed" ? "Completed" : "In progress"}
              </Badge>
              <span>
                {active.answered}/{active.total} answered
              </span>
              {active.overall_score !== null ? (
                <span className="font-mono text-fog-300">{active.overall_score}% overall</span>
              ) : null}
              {active.readiness ? (
                <Badge tone={readinessTone[active.readiness as keyof typeof readinessTone] ?? "neutral"}>
                  {readinessLabel(active.readiness)}
                </Badge>
              ) : null}
            </div>

            {active.status === "in_progress" && currentQuestion ? (
              <div className="rounded-lg border border-line bg-ink-900/60 p-4">
                <p className="text-[11px] uppercase tracking-wide text-fog-500">
                  Question {currentQuestion.position} · {currentQuestion.kind.replace(/_/g, " ")}
                  {currentQuestion.skill_name ? ` · ${currentQuestion.skill_name}` : ""}
                </p>
                <p className="mt-1.5 text-sm text-fog-100">{currentQuestion.prompt}</p>
                <Textarea
                  className="mt-3"
                  rows={6}
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Structure it: situation, decision, trade-off, result."
                />
                <div className="mt-2 flex items-center justify-between gap-3">
                  <p className="text-[11px] text-fog-500">
                    Scored against the rubric; the model answer appears after you finish.
                  </p>
                  <Button size="sm" onClick={submitAnswer} loading={busy} disabled={draft.trim().length < 2}>
                    Save answer
                  </Button>
                </div>
              </div>
            ) : null}

            <ol className="space-y-2">
              {active.questions.map((question) => (
                <li
                  key={question.id}
                  className="rounded-lg border border-line bg-ink-900/40 px-3 py-2.5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-xs text-fog-300">{question.prompt}</p>
                    <span className="shrink-0 font-mono text-[11px] text-fog-500">
                      {question.score !== null ? `${question.score}%` : `Q${question.position}`}
                    </span>
                  </div>
                  {question.feedback ? (
                    <p className="mt-1.5 text-[11px] leading-relaxed text-fog-500">
                      {question.feedback}
                    </p>
                  ) : null}
                  {question.model_answer ? (
                    <p className="mt-1.5 rounded border border-line bg-ink-950/60 px-2 py-1.5 text-[11px] leading-relaxed text-fog-400">
                      <span className="text-fog-300">Model answer: </span>
                      {question.model_answer}
                    </p>
                  ) : null}
                </li>
              ))}
            </ol>

            {active.status === "in_progress" ? (
              <Button
                onClick={completeInterview}
                loading={busy}
                disabled={active.answered < active.total}
              >
                Finish and score the interview
              </Button>
            ) : (
              <ul className="space-y-1.5 rounded-lg border border-line bg-ink-900/60 p-3 text-xs leading-relaxed text-fog-400">
                {active.feedback.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="text-fog-600">·</span>
                    {line}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          <p className="mt-3 text-xs leading-relaxed text-fog-500">
            A mock interview asks curated questions for the selected role and scores each answer
            against its rubric. It practises explanation, not memorisation — and it does not
            guarantee an interview or an offer.
          </p>
        )}

        {interviews && interviews.items.length > 0 ? (
          <div className="mt-5 border-t border-line pt-3">
            <p className="text-[11px] uppercase tracking-wide text-fog-500">Past sessions</p>
            <ul className="mt-2 space-y-1.5">
              {interviews.items.slice(0, 5).map((item) => (
                <li key={item.id} className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-fog-400">
                    {item.role_title} · {new Date(item.started_at).toLocaleDateString()}
                  </span>
                  <span className="text-fog-500">
                    {item.status === "completed" && item.overall_score !== null
                      ? `${item.overall_score}%`
                      : `${item.answered}/${item.total} answered`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Panel>

      <Panel className="p-5">
        <h2 className="flex items-center gap-2 text-sm font-medium text-fog-200">
          <ClipboardList className="size-4 text-fog-400" aria-hidden />
          Resume skill map
        </h2>
        <p className="mt-1 max-w-2xl text-xs leading-relaxed text-fog-500">
          Type the skills you list on your resume. Each claim is matched to a platform skill and
          labelled with the evidence behind it — a claim never raises your measured proficiency.
        </p>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <div className="min-w-48 flex-1">
            <Field label="Skill on your resume" htmlFor="claim">
              <Input
                id="claim"
                value={claimLabel}
                onChange={(event) => setClaimLabel(event.target.value)}
                placeholder="e.g. Testing, SQL joins, React components"
              />
            </Field>
          </div>
          <div className="w-40">
            <Field label="Your claim" htmlFor="claim-level">
              <Select
                id="claim-level"
                value={claimLevel}
                onChange={(event) => setClaimLevel(event.target.value)}
              >
                <option value="unspecified">Unspecified</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </Select>
            </Field>
          </div>
          <Button variant="secondary" onClick={addClaim} loading={busy} disabled={claimLabel.trim().length < 2}>
            <Plus className="size-4" aria-hidden />
            Add claim
          </Button>
        </div>

        {claims && claims.items.length > 0 ? (
          <ul className="mt-4 space-y-2">
            {claims.items.map((claim) => (
              <li
                key={claim.id}
                className="flex items-start justify-between gap-3 rounded-lg border border-line bg-ink-900/60 px-3 py-2.5"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm text-fog-200">{claim.label}</p>
                    {claim.verified ? (
                      <Badge tone="emerald">
                        <Award className="size-3" aria-hidden />
                        Verified
                      </Badge>
                    ) : (
                      <Badge tone="amber">Unverified</Badge>
                    )}
                    {claim.skill_name ? (
                      <span className="text-[11px] text-fog-500">
                        mapped to {claim.skill_name}
                        {claim.subject_name ? ` · ${claim.subject_name}` : ""}
                      </span>
                    ) : (
                      <span className="text-[11px] text-fog-500">
                        no matching platform skill
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-[11px] leading-relaxed text-fog-500">{claim.evidence}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeClaim(claim.id)}
                  className="rounded-md p-1.5 text-fog-500 hover:bg-ink-800 hover:text-rose"
                  aria-label={`Remove ${claim.label}`}
                >
                  <Trash2 className="size-3.5" />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-4">
            <EmptyState
              compact
              icon={<ClipboardList className="size-5" aria-hidden />}
              title="No resume skills yet"
              description="Add the skills you list on your resume to see which claims have real evidence behind them."
            />
          </div>
        )}
      </Panel>
    </div>
  );
}
