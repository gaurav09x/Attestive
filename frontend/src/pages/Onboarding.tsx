import { useEffect, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  Check,
  Code2,
  GraduationCap,
  Loader2,
  Sparkles,
  Target,
  Timer,
} from "lucide-react";
import { Logo } from "../components/Logo";
import { Alert, Badge, Button, Field, Input, Panel, Select, cn } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { MeResponse, OnboardingPayload, Page, Subject } from "../lib/types";

const educationOptions = [
  { value: "high_school", label: "High school", hint: "Preparing for university" },
  { value: "undergraduate", label: "Undergraduate", hint: "Currently studying" },
  { value: "graduate", label: "Graduate", hint: "Degree completed" },
  { value: "self_taught", label: "Self-taught", hint: "Learning independently" },
  { value: "professional", label: "Working professional", hint: "Building new skills" },
];

const experienceOptions = [
  { value: "none", label: "Starting out", hint: "Little or no technical background" },
  { value: "beginner", label: "Beginner", hint: "I know the basics" },
  { value: "intermediate", label: "Intermediate", hint: "I've built small projects" },
  { value: "advanced", label: "Advanced", hint: "I work with this regularly" },
];

const learningStyles = [
  { value: "practical", label: "Learning by building", hint: "Examples and exercises first" },
  { value: "visual", label: "Visual explanations", hint: "Diagrams and walkthroughs" },
  { value: "reading", label: "Reading deeply", hint: "Structured written material" },
  { value: "audio", label: "Listening & discussing", hint: "Explanations and conversation" },
];

const careerOptions = [
  { value: "software_engineer", label: "Software engineer" },
  { value: "frontend_developer", label: "Frontend developer" },
  { value: "backend_developer", label: "Backend developer" },
  { value: "data_scientist", label: "Data scientist" },
  { value: "ml_engineer", label: "Machine learning engineer" },
  { value: "devops_engineer", label: "DevOps engineer" },
  { value: "mobile_developer", label: "Mobile developer" },
  { value: "undecided", label: "Still exploring" },
];

const steps = [
  { title: "Where you are now", description: "Your starting point" },
  { title: "Where you're going", description: "Subjects and goal" },
  { title: "How you learn", description: "Time and style" },
];

interface FormState {
  education_level: string;
  experience_level: string;
  career_goal: string;
  target_role: string;
  subject_slugs: string[];
  learning_style: string;
  session_minutes: number;
  weekly_minutes_goal: number;
  prefers_projects: boolean;
  prefers_theory_first: boolean;
}

const initialForm: FormState = {
  education_level: "",
  experience_level: "",
  career_goal: "",
  target_role: "",
  subject_slugs: [],
  learning_style: "practical",
  session_minutes: 30,
  weekly_minutes_goal: 300,
  prefers_projects: true,
  prefers_theory_first: false,
};

function ChoiceCard({
  selected,
  label,
  hint,
  onClick,
}: {
  selected: boolean;
  label: string;
  hint?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "flex w-full items-start gap-3 rounded-lg border p-3.5 text-left transition-all",
        selected
          ? "border-electric/60 bg-electric/[0.08] shadow-[0_0_0_1px_rgba(76,141,255,0.15)]"
          : "border-line bg-ink-900/60 hover:border-line-bright hover:bg-ink-800/60",
      )}
    >
      <span
        className={cn(
          "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border",
          selected ? "border-electric bg-electric text-white" : "border-line-bright",
        )}
      >
        {selected ? <Check className="size-2.5" aria-hidden /> : null}
      </span>
      <span>
        <span className="block text-sm font-medium text-fog-100">{label}</span>
        {hint ? <span className="mt-0.5 block text-xs text-fog-500">{hint}</span> : null}
      </span>
    </button>
  );
}

export default function Onboarding() {
  const { user, reloadUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const editMode = searchParams.get("edit") === "1";

  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(initialForm);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(true);
  const [subjectsError, setSubjectsError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    apiFetch<Page<Subject>>("/catalog/subjects")
      .then((page) => {
        if (active) setSubjects(page.items);
      })
      .catch((caught) => {
        if (active) {
          setSubjectsError(
            caught instanceof ApiError ? caught.message : "Could not load subjects.",
          );
        }
      })
      .finally(() => {
        if (active) setSubjectsLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!editMode) return;
    let active = true;
    apiFetch<MeResponse>("/users/me")
      .then((payload) => {
        if (!active) return;
        const profile = payload.user.profile;
        setForm({
          education_level: profile?.education_level ?? "",
          experience_level: profile?.experience_level ?? "",
          career_goal: profile?.career_goal ?? "",
          target_role: profile?.target_role ?? "",
          subject_slugs: payload.interests.map((subject) => subject.slug),
          learning_style: payload.user.preferences?.learning_style ?? "practical",
          session_minutes: payload.user.preferences?.session_minutes ?? 30,
          weekly_minutes_goal: profile?.weekly_minutes_goal ?? 300,
          prefers_projects: payload.user.preferences?.prefers_projects ?? true,
          prefers_theory_first: payload.user.preferences?.prefers_theory_first ?? false,
        });
      })
      .catch((caught) => {
        if (active) {
          setError(caught instanceof ApiError ? caught.message : "Could not load your current preferences.");
        }
      });
    return () => {
      active = false;
    };
  }, [editMode]);

  if (user?.onboarding_completed && !editMode) {
    return <Navigate to="/dashboard" replace />;
  }

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setError(null);
  }

  function toggleSubject(slug: string) {
    setForm((current) => {
      if (current.subject_slugs.includes(slug)) {
        return { ...current, subject_slugs: current.subject_slugs.filter((item) => item !== slug) };
      }
      if (current.subject_slugs.length >= 5) return current;
      return { ...current, subject_slugs: [...current.subject_slugs, slug] };
    });
    setError(null);
  }

  function validateCurrentStep(): string | null {
    if (step === 0) {
      if (!form.education_level) return "Choose your current education level.";
      if (!form.experience_level) return "Choose your current technical experience.";
    }
    if (step === 1) {
      if (form.subject_slugs.length === 0) return "Pick at least one subject to focus on.";
      if (!form.career_goal) return "Choose a career direction. “Still exploring” is fine.";
    }
    if (step === 2) {
      if (!form.learning_style) return "Choose a preferred learning style.";
    }
    return null;
  }

  function next() {
    const problem = validateCurrentStep();
    if (problem) {
      setError(problem);
      return;
    }
    setStep((current) => Math.min(2, current + 1));
  }

  async function submit() {
    const problem = validateCurrentStep();
    if (problem) {
      setError(problem);
      return;
    }
    setSubmitting(true);
    setError(null);
    const payload: OnboardingPayload = {
      education_level: form.education_level,
      experience_level: form.experience_level,
      learning_style: form.learning_style,
      session_minutes: form.session_minutes,
      weekly_minutes_goal: form.weekly_minutes_goal,
      career_goal: form.career_goal,
      target_role: form.target_role.trim() || null,
      subject_slugs: form.subject_slugs,
      prefers_projects: form.prefers_projects,
      prefers_theory_first: form.prefers_theory_first,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    };

    try {
      await apiFetch<MeResponse>("/users/me/onboarding", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      await reloadUser();
      navigate(editMode ? "/settings" : "/assessments", { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not save your profile.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-line">
        <div className="mx-auto flex h-16 w-full max-w-3xl items-center justify-between px-5">
          <Logo />
          <span className="text-xs text-fog-500">Step {step + 1} of {steps.length}</span>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl px-5 py-10 sm:py-14">
        <div className="flex items-center gap-2">
          {steps.map((item, index) => (
            <div key={item.title} className="flex flex-1 flex-col gap-2">
              <div
                className={cn(
                  "h-1 rounded-full transition-colors",
                  index <= step ? "bg-gradient-to-r from-electric to-violet" : "bg-ink-700",
                )}
              />
              <span className={cn("text-[11px]", index === step ? "text-fog-200" : "text-fog-500")}>
                {item.title}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-8">
          <Badge tone="blue">
            <Sparkles className="size-3.5" aria-hidden />
            {editMode ? "Update your learning plan" : "Personalisation setup"}
          </Badge>
          <h1 className="mt-4 text-2xl font-semibold sm:text-3xl">{steps[step].title}</h1>
          <p className="mt-2 text-sm leading-relaxed text-fog-400">
            {step === 0 && "This calibrates your first recommendations. It is not a test."}
            {step === 1 && "Choose up to five subjects. Your roadmap will start with these."}
            {step === 2 && "Be realistic about time — a plan you can keep beats an ambitious one."}
          </p>
        </div>

        {error ? <div className="mt-5"><Alert>{error}</Alert></div> : null}

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.22 }}
            className="mt-6"
          >
            {step === 0 ? (
              <Panel className="space-y-6 p-5 sm:p-6">
                <div>
                  <div className="mb-2.5 flex items-center gap-2 text-sm font-medium text-fog-200">
                    <GraduationCap className="size-4 text-electric" aria-hidden />
                    Current education
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {educationOptions.map((option) => (
                      <ChoiceCard
                        key={option.value}
                        label={option.label}
                        hint={option.hint}
                        selected={form.education_level === option.value}
                        onClick={() => update("education_level", option.value)}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-2.5 flex items-center gap-2 text-sm font-medium text-fog-200">
                    <Code2 className="size-4 text-violet" aria-hidden />
                    Technical experience
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {experienceOptions.map((option) => (
                      <ChoiceCard
                        key={option.value}
                        label={option.label}
                        hint={option.hint}
                        selected={form.experience_level === option.value}
                        onClick={() => update("experience_level", option.value)}
                      />
                    ))}
                  </div>
                </div>
              </Panel>
            ) : null}

            {step === 1 ? (
              <Panel className="space-y-6 p-5 sm:p-6">
                <div>
                  <div className="mb-2.5 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-medium text-fog-200">
                      <Target className="size-4 text-electric" aria-hidden />
                      Subjects to focus on
                    </div>
                    <span className="text-xs text-fog-500">{form.subject_slugs.length}/5 selected</span>
                  </div>

                  {subjectsLoading ? (
                    <div className="flex items-center gap-2 py-6 text-sm text-fog-400">
                      <Loader2 className="size-4 animate-spin" aria-hidden />
                      Loading subject catalogue…
                    </div>
                  ) : subjectsError ? (
                    <Alert>{subjectsError} Restart the backend and reload this page.</Alert>
                  ) : (
                    <div className="grid gap-2 sm:grid-cols-2">
                      {subjects.map((subject) => {
                        const selected = form.subject_slugs.includes(subject.slug);
                        const disabled = !selected && form.subject_slugs.length >= 5;
                        return (
                          <button
                            key={subject.id}
                            type="button"
                            onClick={() => toggleSubject(subject.slug)}
                            disabled={disabled}
                            aria-pressed={selected}
                            className={cn(
                              "rounded-lg border p-3.5 text-left transition-all disabled:cursor-not-allowed disabled:opacity-40",
                              selected
                                ? "border-electric/60 bg-electric/[0.08]"
                                : "border-line bg-ink-900/60 hover:border-line-bright",
                            )}
                          >
                            <span className="flex items-center justify-between gap-3">
                              <span className="text-sm font-medium text-fog-100">{subject.name}</span>
                              {selected ? <Check className="size-4 text-electric" aria-hidden /> : null}
                            </span>
                            <span className="mt-1 block text-xs leading-relaxed text-fog-500">
                              {subject.description}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Career direction" htmlFor="career_goal">
                    <Select
                      id="career_goal"
                      value={form.career_goal}
                      onChange={(event) => update("career_goal", event.target.value)}
                    >
                      <option value="">Choose a direction</option>
                      {careerOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Target role" htmlFor="target_role" optional hint="e.g. Backend Engineer">
                    <Input
                      id="target_role"
                      value={form.target_role}
                      onChange={(event) => update("target_role", event.target.value)}
                      placeholder="Backend Engineer"
                      maxLength={120}
                    />
                  </Field>
                </div>
              </Panel>
            ) : null}

            {step === 2 ? (
              <Panel className="space-y-6 p-5 sm:p-6">
                <div>
                  <div className="mb-2.5 flex items-center gap-2 text-sm font-medium text-fog-200">
                    <Sparkles className="size-4 text-violet" aria-hidden />
                    How you prefer to learn
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {learningStyles.map((option) => (
                      <ChoiceCard
                        key={option.value}
                        label={option.label}
                        hint={option.hint}
                        selected={form.learning_style === option.value}
                        onClick={() => update("learning_style", option.value)}
                      />
                    ))}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Typical session length" htmlFor="session_minutes">
                    <Select
                      id="session_minutes"
                      value={String(form.session_minutes)}
                      onChange={(event) => update("session_minutes", Number(event.target.value))}
                    >
                      {[15, 25, 30, 45, 60, 90].map((minutes) => (
                        <option key={minutes} value={minutes}>
                          {minutes} minutes
                        </option>
                      ))}
                    </Select>
                  </Field>

                  <div>
                    <div className="flex items-baseline justify-between">
                      <label htmlFor="weekly_goal" className="text-sm font-medium text-fog-200">
                        Weekly study goal
                      </label>
                      <span className="font-mono text-xs text-fog-300">
                        {Math.floor(form.weekly_minutes_goal / 60)}h{" "}
                        {form.weekly_minutes_goal % 60 > 0 ? `${form.weekly_minutes_goal % 60}m` : ""}
                      </span>
                    </div>
                    <input
                      id="weekly_goal"
                      type="range"
                      min={60}
                      max={1200}
                      step={30}
                      value={form.weekly_minutes_goal}
                      onChange={(event) =>
                        update("weekly_minutes_goal", Number(event.target.value))
                      }
                      className="mt-4 w-full accent-[#4c8dff]"
                      aria-valuetext={`${form.weekly_minutes_goal} minutes per week`}
                    />
                    <div className="mt-1 flex justify-between text-[11px] text-fog-500">
                      <span>1h</span>
                      <span>20h</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2.5 border-t border-line pt-5">
                  <label className="flex cursor-pointer items-start gap-3 text-sm text-fog-300">
                    <input
                      type="checkbox"
                      checked={form.prefers_projects}
                      onChange={(event) => update("prefers_projects", event.target.checked)}
                      className="mt-0.5 size-4 accent-[#4c8dff]"
                    />
                    <span>
                      Include practical projects
                      <span className="mt-0.5 block text-xs text-fog-500">
                        Apply concepts in small builds rather than only exercises.
                      </span>
                    </span>
                  </label>
                  <label className="flex cursor-pointer items-start gap-3 text-sm text-fog-300">
                    <input
                      type="checkbox"
                      checked={form.prefers_theory_first}
                      onChange={(event) => update("prefers_theory_first", event.target.checked)}
                      className="mt-0.5 size-4 accent-[#4c8dff]"
                    />
                    <span>
                      Explain the theory before practice
                      <span className="mt-0.5 block text-xs text-fog-500">
                        Start each topic with the underlying idea, then apply it.
                      </span>
                    </span>
                  </label>
                </div>

                <div className="flex items-start gap-3 rounded-lg border border-line bg-ink-900/60 p-3.5 text-xs leading-relaxed text-fog-400">
                  <Briefcase className="mt-0.5 size-4 shrink-0 text-electric" aria-hidden />
                  Your selections create a self-reported starting estimate only. The diagnostic
                  assessment in Phase 2 will replace it with evidence.
                </div>
              </Panel>
            ) : null}
          </motion.div>
        </AnimatePresence>

        <div className="mt-6 flex items-center justify-between gap-3">
          <Button
            variant="ghost"
            onClick={() => setStep((current) => Math.max(0, current - 1))}
            disabled={step === 0 || submitting}
          >
            <ArrowLeft className="size-4" aria-hidden />
            Back
          </Button>

          {step < 2 ? (
            <Button onClick={next}>
              Continue
              <ArrowRight className="size-4" aria-hidden />
            </Button>
          ) : (
            <Button onClick={submit} loading={submitting}>
              <Timer className="size-4" aria-hidden />
              {submitting ? "Saving your plan…" : editMode ? "Save changes" : "Finish setup"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
