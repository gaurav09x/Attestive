import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthLayout } from "../components/layout/AuthLayout";
import { Alert, Button, Field, Input } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    if (!email.trim()) {
      setError("Enter the email address on your account.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await apiFetch<{ message: string }>("/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });
      setMessage(response.message);
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Could not request a password reset.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We will create a single-use reset link for the address on your account."
      footer={
        <>
          Remembered it?{" "}
          <Link to="/login" className="font-medium text-electric hover:underline">
            Back to sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {error ? <Alert>{error}</Alert> : null}
        {message ? (
          <Alert tone="success">
            {message}
            <span className="mt-2 block text-xs text-fog-400">
              Email delivery is not configured on this deployment. In development the link is
              written to the API log.
            </span>
          </Alert>
        ) : null}

        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </Field>

        <Button type="submit" className="w-full" loading={submitting}>
          {submitting ? "Creating link…" : "Send reset link"}
        </Button>
      </form>
    </AuthLayout>
  );
}
