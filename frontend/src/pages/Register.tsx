import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Check, Eye, EyeOff } from "lucide-react";
import { AuthLayout } from "../components/layout/AuthLayout";
import { Alert, Button, Field, Input } from "../components/ui";
import { ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function Register() {
  const { register, status, user } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated" && user) {
    return <Navigate to={user.onboarding_completed ? "/dashboard" : "/onboarding"} replace />;
  }

  const passwordChecks = [
    { label: "At least 8 characters", met: password.length >= 8 },
    { label: "A letter and a number", met: /[A-Za-z]/.test(password) && /\d/.test(password) },
  ];

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldErrors({});

    const errors: Record<string, string> = {};
    if (fullName.trim().length < 2) errors.full_name = "Enter your name.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.email = "Enter a valid email address.";
    if (!passwordChecks.every((check) => check.met)) {
      errors.password = "Choose a password that meets both requirements.";
    }
    if (password !== confirmPassword) errors.confirm_password = "Passwords do not match.";
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      await register(fullName.trim(), email.trim(), password);
      navigate("/onboarding", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
        const mapped: Record<string, string> = {};
        caught.details.forEach((detail) => {
          mapped[detail.field] = detail.message;
        });
        setFieldErrors(mapped);
      } else {
        setError("Could not create your account. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Three short onboarding steps and you'll have a real baseline — not a generic course list."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-electric hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {error ? <Alert>{error}</Alert> : null}

        <Field label="Full name" htmlFor="full_name" error={fieldErrors.full_name}>
          <Input
            id="full_name"
            name="full_name"
            autoComplete="name"
            placeholder="Ada Lovelace"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            invalid={Boolean(fieldErrors.full_name)}
            required
          />
        </Field>

        <Field label="Email" htmlFor="email" error={fieldErrors.email}>
          <Input
            id="email"
            type="email"
            name="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            invalid={Boolean(fieldErrors.email)}
            required
          />
        </Field>

        <Field label="Password" htmlFor="password" error={fieldErrors.password}>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              name="password"
              autoComplete="new-password"
              placeholder="Create a password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              invalid={Boolean(fieldErrors.password)}
              className="pr-11"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-lg text-fog-500 hover:text-fog-200"
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
            {passwordChecks.map((check) => (
              <li
                key={check.label}
                className={check.met ? "flex items-center gap-1 text-xs text-emerald" : "flex items-center gap-1 text-xs text-fog-500"}
              >
                <Check className="size-3" aria-hidden />
                {check.label}
              </li>
            ))}
          </ul>
        </Field>

        <Field
          label="Confirm password"
          htmlFor="confirm_password"
          error={fieldErrors.confirm_password}
        >
          <Input
            id="confirm_password"
            type={showPassword ? "text" : "password"}
            name="confirm_password"
            autoComplete="new-password"
            placeholder="Repeat your password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            invalid={Boolean(fieldErrors.confirm_password)}
            required
          />
        </Field>

        <Button type="submit" className="w-full" loading={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </Button>

        <p className="text-xs leading-relaxed text-fog-500">
          You'll be asked about your education, current experience and the skills you want next.
          Nothing is shared with third parties.
        </p>
      </form>
    </AuthLayout>
  );
}
