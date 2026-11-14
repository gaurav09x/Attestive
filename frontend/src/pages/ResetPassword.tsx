import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthLayout } from "../components/layout/AuthLayout";
import { Alert, Button, Field, Input } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("The two passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch<void>("/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
      });
      setDone(true);
      setTimeout(() => navigate("/login", { replace: true }), 1600);
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Could not reset your password.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Choose a new password"
      subtitle="Resetting your password signs out every other session."
      footer={
        <Link to="/login" className="font-medium text-electric hover:underline">
          Back to sign in
        </Link>
      }
    >
      {!token ? (
        <Alert>
          This link is missing its token. Request a new reset link from the{" "}
          <Link to="/forgot-password" className="underline">
            forgot password
          </Link>{" "}
          page.
        </Alert>
      ) : done ? (
        <Alert tone="success">Password changed. Redirecting you to sign in…</Alert>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          {error ? <Alert>{error}</Alert> : null}

          <Field
            label="New password"
            htmlFor="password"
            hint="At least 8 characters, with letters and numbers."
          >
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </Field>

          <Field label="Confirm password" htmlFor="confirm">
            <Input
              id="confirm"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
              required
            />
          </Field>

          <Button type="submit" className="w-full" loading={submitting}>
            {submitting ? "Saving…" : "Set new password"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
