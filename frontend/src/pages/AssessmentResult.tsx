import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  CircleSlash,
  ClipboardCheck,
  Route,
  XCircle,
} from "lucide-react";
import { RadialProgress } from "../components/ActivityChart";
import { Alert, Badge, Button, Panel, Progress, Spinner, cn } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import { formatDate } from "../lib/format";
import type { AttemptReview } from "../lib/types";

export default function AssessmentResult() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [review, setReview] = useState<AttemptReview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!attemptId) return;
    apiFetch<AttemptReview>(`/assessments/attempts/${attemptId}/review`)
      .then((data) => active && setReview(data))
      .catch(
        (caught) =>
          active &&
          setError(caught instanceof ApiError ? caught.message : "Could not load this result."),
      );
    return () => {
      active = false;
    };
  }, [attemptId]);

  if (error) {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Result unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{error}</p>
        <Link to="/assessments" className="mt-5 inline-block">
          <Button>Back to diagnostics</Button>
        </Link>
      </Panel>
    );
  }

  if (!review) return <Spinner label="Loading your result…" />;

  const score = Math.round(review.score_percent ?? 0);
  const correct = review.questions.filter((question) => question.is_correct).length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-6"
    >
      <div>
        <Link to="/assessments" className="text-xs text-fog-500 hover:text-fog-300">
          ← Diagnostics
        </Link>
        <h1 className="mt-1.5 text-2xl font-semibold">{review.title} result</h1>
        <p className="mt-1 text-sm text-fog-400">
          {review.subject_name}
          {review.completed_at ? ` · submitted ${formatDate(review.completed_at)}` : ""}
        </p>
      </div>

      <Panel className="p-6">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-6">
            <RadialProgress value={score} label={`${score}%`} caption="diagnostic score" />
            <div>
              <p className="text-sm text-fog-400">Proficiency estimate</p>
              <p className="text-2xl font-semibold">{Math.round(review.proficiency_estimate ?? 0)}%</p>
              <p className="mt-1 text-xs leading-relaxed text-fog-500">
                {correct} of {review.questions.length} answers fully correct. This estimate updates
                as you complete lessons and retake diagnostics.
              </p>
            </div>
          </div>

          <div className="flex w-full flex-col gap-2 sm:w-auto">
            {review.roadmap_id ? (
              <Link to={`/roadmap?subject=${review.subject_slug}`}>
                <Button className="w-full">
                  <Route className="size-4" aria-hidden />
                  Open your roadmap
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </Link>
            ) : (
              <Link to="/assessments">
                <Button className="w-full">Back to diagnostics</Button>
              </Link>
            )}
            <Link to="/assessments">
              <Button variant="secondary" className="w-full">
                <ClipboardCheck className="size-4" aria-hidden />
                All diagnostics
              </Button>
            </Link>
          </div>
        </div>

        {review.weak_skills.length > 0 ? (
          <div className="mt-6 border-t border-line pt-5">
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-fog-500">
              Concepts to strengthen
            </p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {review.weak_skills.map((skill) => (
                <Badge key={skill} tone="amber">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-6 flex items-center gap-2 border-t border-line pt-5 text-sm text-emerald">
            <CheckCircle2 className="size-4" aria-hidden />
            No weak concepts detected in this diagnostic.
          </div>
        )}
      </Panel>

      {review.skills.length > 0 ? (
        <Panel className="p-5">
          <h2 className="text-sm font-medium text-fog-200">Skill breakdown</h2>
          <p className="mt-1 text-xs text-fog-500">
            Attempt score per skill (bar colour) next to your updated proficiency estimate.
          </p>
          <ul className="mt-4 space-y-3.5">
            {review.skills.map((skill) => (
              <li key={skill.skill_id}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="text-fog-200">{skill.name}</span>
                  <span className="text-xs text-fog-500">
                    scored {skill.score}% · now {skill.proficiency}% ({skill.confidence}% confidence)
                  </span>
                </div>
                <div className="mt-1.5 flex gap-2">
                  <div className="flex-1">
                    <Progress value={skill.score} tone={skill.score >= 60 ? "emerald" : "violet"} />
                  </div>
                  <div className="flex-1">
                    <Progress value={skill.proficiency} tone="blue" />
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex gap-4 text-[11px] text-fog-500">
            <span className="flex items-center gap-1.5">
              <span className="h-1 w-4 rounded-full bg-gradient-to-r from-violet to-electric" />
              diagnostic score
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-1 w-4 rounded-full bg-gradient-to-r from-electric to-cyan" />
              stored proficiency
            </span>
          </div>
        </Panel>
      ) : null}

      <div>
        <h2 className="text-lg font-semibold">Review every answer</h2>
        <p className="mt-1 text-sm text-fog-400">
          Compare your reasoning with the expected answer and explanation.
        </p>

        <div className="mt-4 space-y-3">
          {review.questions.map((question, index) => {
            const yourAnswer =
              question.kind === "multiple_choice" && question.options
                ? question.options[question.response?.index ?? -1] ?? "No answer"
                : question.response?.text ?? "No answer";
            const status =
              question.score === null
                ? "unscored"
                : question.is_correct
                  ? "correct"
                  : question.score > 0
                    ? "partial"
                    : "incorrect";

            return (
              <Panel key={question.id} className="p-5">
                <div className="flex items-start gap-3">
                  <span
                    className={cn(
                      "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full",
                      status === "correct"
                        ? "bg-emerald/15 text-emerald"
                        : status === "partial"
                          ? "bg-amber/15 text-amber"
                          : status === "incorrect"
                            ? "bg-rose/15 text-rose"
                            : "bg-ink-700 text-fog-400",
                    )}
                  >
                    {status === "correct" ? (
                      <CheckCircle2 className="size-4" aria-hidden />
                    ) : status === "unscored" ? (
                      <CircleSlash className="size-4" aria-hidden />
                    ) : (
                      <XCircle className="size-4" aria-hidden />
                    )}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-medium text-fog-100">
                        {index + 1}. {question.prompt}
                      </p>
                      {question.skill_name ? (
                        <Badge tone="neutral">{question.skill_name}</Badge>
                      ) : null}
                    </div>

                    <dl className="mt-3 space-y-2 text-sm">
                      <div>
                        <dt className="text-xs text-fog-500">Your answer</dt>
                        <dd className="mt-0.5 text-fog-300">{yourAnswer}</dd>
                      </div>
                      {question.correct_answer ? (
                        <div>
                          <dt className="text-xs text-fog-500">Expected answer</dt>
                          <dd className="mt-0.5 text-fog-200">{question.correct_answer}</dd>
                        </div>
                      ) : null}
                    </dl>

                    {question.feedback ? (
                      <p className="mt-2 text-xs text-fog-400">{question.feedback}</p>
                    ) : null}
                    {question.explanation ? (
                      <p className="mt-2 rounded-lg border border-line bg-ink-900/60 px-3 py-2 text-xs leading-relaxed text-fog-400">
                        {question.explanation}
                      </p>
                    ) : null}
                  </div>
                </div>
              </Panel>
            );
          })}
        </div>
      </div>

      <Alert tone="info">
        A diagnostic is a snapshot. Your proficiency estimate improves with lessons, exercises and
        later assessments — it is never locked to one result.
      </Alert>
    </motion.div>
  );
}
