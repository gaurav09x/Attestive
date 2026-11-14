import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Check, Send } from "lucide-react";
import { Alert, Badge, Button, Panel, Spinner, Textarea, cn } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import type { AssessmentAttempt, AttemptResult, SavedResponse } from "../lib/types";

type Answers = Record<string, SavedResponse>;

export default function AssessmentAttemptPage() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState<AssessmentAttempt | null>(null);
  const [answers, setAnswers] = useState<Answers>({});
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    if (!attemptId) return;
    apiFetch<AssessmentAttempt>(`/assessments/attempts/${attemptId}`)
      .then((data) => {
        if (!active) return;
        if (data.status === "completed") {
          navigate(`/assessments/result/${data.id}`, { replace: true });
          return;
        }
        setAttempt(data);
        const restored: Answers = {};
        data.questions.forEach((question) => {
          if (question.saved_response) restored[question.id] = question.saved_response;
        });
        setAnswers(restored);
        const firstUnanswered = data.questions.findIndex((question) => !question.saved_response);
        setIndex(firstUnanswered === -1 ? 0 : firstUnanswered);
      })
      .catch((caught) => {
        if (active) {
          setError(caught instanceof ApiError ? caught.message : "Could not load the diagnostic.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [attemptId, navigate]);

  if (loading) return <Spinner label="Loading your diagnostic…" />;

  if (error || !attempt) {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Diagnostic unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{error ?? "This attempt could not be found."}</p>
        <Link to="/assessments" className="mt-5 inline-block">
          <Button>Back to diagnostics</Button>
        </Link>
      </Panel>
    );
  }

  const question = attempt.questions[index];
  const answeredCount = Object.keys(answers).length;

  function setAnswer(questionId: string, value: SavedResponse) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
    setError(null);
  }

  async function saveCurrent(): Promise<boolean> {
    const current = answers[question.id];
    if (!current) return true;
    setSaving(true);
    try {
      await apiFetch(
        `/assessments/attempts/${attempt!.id}/responses/${question.id}`,
        { method: "PUT", body: JSON.stringify(current) },
      );
      return true;
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not save that answer.");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function goNext() {
    if (!(await saveCurrent())) return;
    setIndex((current) => Math.min(attempt!.questions.length - 1, current + 1));
  }

  function goBack() {
    setIndex((current) => Math.max(0, current - 1));
  }

  async function submit() {
    const unanswered = attempt!.questions.filter((item) => !answers[item.id]);
    if (unanswered.length > 0) {
      setError(`Answer all questions before submitting. ${unanswered.length} remaining.`);
      setIndex(attempt!.questions.indexOf(unanswered[0]));
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await apiFetch<AttemptResult>(`/assessments/attempts/${attempt!.id}/submit`, {
        method: "POST",
        body: JSON.stringify({
          responses: attempt!.questions.map((item) => ({
            question_id: item.id,
            response: answers[item.id],
          })),
        }),
      });
      navigate(`/assessments/result/${attempt!.id}`, { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not submit your attempt.");
    } finally {
      setSubmitting(false);
    }
  }

  const selected = answers[question.id];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/assessments" className="text-xs text-fog-500 hover:text-fog-300">
            ← Diagnostics
          </Link>
          <h1 className="mt-1.5 text-xl font-semibold">{attempt.title}</h1>
          <p className="text-sm text-fog-400">{attempt.subject_name}</p>
        </div>
        <Badge tone="neutral">
          {answeredCount}/{attempt.total_questions} answered
        </Badge>
      </div>

      <div className="flex gap-1.5" aria-hidden>
        {attempt.questions.map((item, itemIndex) => (
          <div
            key={item.id}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors",
              answers[item.id]
                ? "bg-emerald/70"
                : itemIndex === index
                  ? "bg-electric"
                  : "bg-ink-700",
            )}
          />
        ))}
      </div>

      {error ? <Alert>{error}</Alert> : null}

      <AnimatePresence mode="wait">
        <motion.div
          key={question.id}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -10 }}
          transition={{ duration: 0.2 }}
        >
          <Panel className="p-5 sm:p-6">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-fog-500">
                Question {index + 1} of {attempt.total_questions}
              </p>
              <span className="text-[11px] text-fog-500">
                {question.kind === "multiple_choice"
                  ? "Choose one"
                  : question.kind === "short_answer"
                    ? "Short answer"
                    : "Explain in your own words"}
              </span>
            </div>

            <h2 className="mt-3 text-lg font-medium leading-relaxed">{question.prompt}</h2>

            <div className="mt-5">
              {question.kind === "multiple_choice" && question.options ? (
                <div className="space-y-2" role="radiogroup" aria-label="Answer options">
                  {question.options.map((option, optionIndex) => {
                    const isSelected = selected?.index === optionIndex;
                    return (
                      <button
                        key={option}
                        type="button"
                        role="radio"
                        aria-checked={isSelected}
                        onClick={() => setAnswer(question.id, { index: optionIndex })}
                        className={cn(
                          "flex w-full items-start gap-3 rounded-lg border p-3.5 text-left text-sm transition-colors",
                          isSelected
                            ? "border-electric/60 bg-electric/[0.08] text-fog-100"
                            : "border-line bg-ink-900/60 text-fog-300 hover:border-line-bright hover:bg-ink-800/60",
                        )}
                      >
                        <span
                          className={cn(
                            "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border",
                            isSelected
                              ? "border-electric bg-electric text-white"
                              : "border-line-bright",
                          )}
                        >
                          {isSelected ? <Check className="size-2.5" aria-hidden /> : null}
                        </span>
                        {option}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div>
                  <Textarea
                    value={selected?.text ?? ""}
                    onChange={(event) => setAnswer(question.id, { text: event.target.value })}
                    placeholder={
                      question.kind === "short_answer"
                        ? "One or two words, or a short phrase."
                        : "Two or three sentences. You are graded on the key ideas, not exact wording."
                    }
                    maxLength={4000}
                    aria-label="Your answer"
                  />
                  <p className="mt-2 text-xs text-fog-500">
                    {selected?.text?.length ?? 0}/4000 characters
                  </p>
                </div>
              )}
            </div>
          </Panel>
        </motion.div>
      </AnimatePresence>

      <div className="flex items-center justify-between gap-3">
        <Button variant="ghost" onClick={goBack} disabled={index === 0 || submitting || saving}>
          <ArrowLeft className="size-4" aria-hidden />
          Previous
        </Button>

        <div className="flex items-center gap-2">
          {saving ? <span className="text-xs text-fog-500">Saving…</span> : null}
          {index < attempt.questions.length - 1 ? (
            <Button onClick={goNext} loading={saving}>
              Next
              <ArrowRight className="size-4" aria-hidden />
            </Button>
          ) : (
            <Button onClick={submit} loading={submitting}>
              <Send className="size-4" aria-hidden />
              Submit diagnostic
            </Button>
          )}
        </div>
      </div>

      <p className="text-center text-xs text-fog-500">
        Answers save as you move between questions. You can leave and resume this attempt.
      </p>
    </div>
  );
}
