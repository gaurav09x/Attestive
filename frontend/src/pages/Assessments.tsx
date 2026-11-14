import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Loader2,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { Alert, Badge, Button, EmptyState, Panel, Spinner } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import type { AssessmentAttempt, AssessmentOverview } from "../lib/types";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: AssessmentOverview };

export default function Assessments() {
  const navigate = useNavigate();
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [startingSubject, setStartingSubject] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    apiFetch<AssessmentOverview>("/assessments")
      .then((data) => active && setState({ status: "ready", data }))
      .catch(
        (caught) =>
          active &&
          setState({
            status: "error",
            message: caught instanceof ApiError ? caught.message : "Could not load assessments.",
          }),
      );
    return () => {
      active = false;
    };
  }, [reloadKey]);

  const startAttempt = useCallback(
    async (assessmentId: string) => {
      setStartingSubject(assessmentId);
      setActionError(null);
      try {
        const attempt = await apiFetch<AssessmentAttempt>(
          `/assessments/${assessmentId}/attempts`,
          { method: "POST" },
        );
        navigate(`/assessments/attempt/${attempt.id}`);
      } catch (caught) {
        setActionError(
          caught instanceof ApiError ? caught.message : "Could not start the diagnostic.",
        );
      } finally {
        setStartingSubject(null);
      }
    },
    [navigate],
  );

  if (state.status === "loading") return <Spinner label="Loading your diagnostics…" />;

  if (state.status === "error") {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Diagnostics unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{state.message}</p>
        <Button className="mt-5" onClick={() => setReloadKey((value) => value + 1)}>
          Try again
        </Button>
      </Panel>
    );
  }

  const subjects = state.data.subjects;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Diagnostics</h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-fog-400">
            Six questions per subject, scored per skill. This is evidence, not a verdict — your
            estimate changes as you learn.
          </p>
        </div>
        <Link to="/roadmap">
          <Button variant="secondary" size="sm">
            View roadmaps
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        </Link>
      </header>

      {actionError ? <Alert>{actionError}</Alert> : null}

      {subjects.length === 0 ? (
        <Panel className="p-6">
          <EmptyState
            icon={<ClipboardCheck className="size-5" aria-hidden />}
            title="No subjects selected"
            description="Choose your focus subjects in your learning profile, then return here to take a diagnostic."
            action={
              <Link to="/onboarding?edit=1">
                <Button>Update learning preferences</Button>
              </Link>
            }
          />
        </Panel>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {subjects.map((subject, index) => {
            const completed = Boolean(subject.last_attempt_id);
            const inProgress = Boolean(subject.in_progress_attempt_id);
            return (
              <motion.div
                key={subject.subject_id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: index * 0.04 }}
              >
                <Panel className="flex h-full flex-col p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="text-base font-semibold">{subject.subject_name}</h2>
                      <p className="mt-1 text-xs leading-relaxed text-fog-400">
                        {subject.subject_description}
                      </p>
                    </div>
                    {inProgress ? (
                      <Badge tone="amber">In progress</Badge>
                    ) : completed ? (
                      <Badge tone="emerald">
                        <CheckCircle2 className="size-3" aria-hidden />
                        {Math.round(subject.last_score ?? 0)}%
                      </Badge>
                    ) : (
                      <Badge tone="neutral">Not started</Badge>
                    )}
                  </div>

                  <div className="mt-4 flex items-center gap-4 text-xs text-fog-500">
                    <span className="flex items-center gap-1.5">
                      <ClipboardCheck className="size-3.5" aria-hidden />
                      {subject.question_count} questions
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock3 className="size-3.5" aria-hidden />
                      ~{subject.estimated_minutes ?? 10} min
                    </span>
                  </div>

                  <div className="mt-auto flex flex-wrap items-center gap-2 pt-5">
                    {subject.assessment_id ? (
                      <>
                        {inProgress && subject.in_progress_attempt_id ? (
                          <Link to={`/assessments/attempt/${subject.in_progress_attempt_id}`}>
                            <Button size="sm">
                              Resume diagnostic
                              <ArrowRight className="size-4" aria-hidden />
                            </Button>
                          </Link>
                        ) : (
                          <Button
                            size="sm"
                            onClick={() => startAttempt(subject.assessment_id!)}
                            loading={startingSubject === subject.assessment_id}
                          >
                            {completed ? (
                              <RotateCcw className="size-4" aria-hidden />
                            ) : (
                              <Sparkles className="size-4" aria-hidden />
                            )}
                            {completed ? "Retake diagnostic" : "Start diagnostic"}
                          </Button>
                        )}

                        {completed && subject.last_attempt_id ? (
                          <Link to={`/assessments/result/${subject.last_attempt_id}`}>
                            <Button variant="secondary" size="sm">
                              Review result
                            </Button>
                          </Link>
                        ) : null}
                      </>
                    ) : (
                      <span className="flex items-center gap-2 text-xs text-fog-500">
                        <Loader2 className="size-3.5" aria-hidden />
                        Diagnostic content is not published for this subject yet.
                      </span>
                    )}
                  </div>
                </Panel>
              </motion.div>
            );
          })}
        </div>
      )}

      <p className="text-xs leading-relaxed text-fog-500">
        Diagnostics are curated for each subject so they work offline. Your roadmap note can be
        written by the AI tutor when a model provider is configured; the sequencing always comes
        from your measured weak skills.
      </p>
    </div>
  );
}
