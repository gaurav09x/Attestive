import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AuthLayout } from "../components/layout/AuthLayout";
import { Alert, Spinner } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [state, setState] = useState<"pending" | "verified" | "failed">("pending");
  const [error, setError] = useState<string | null>(null);
  const sent = useRef(false);

  useEffect(() => {
    if (sent.current || !token) return;
    sent.current = true;
    apiFetch<{ verified: boolean }>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then(() => setState("verified"))
      .catch((caught) => {
        setState("failed");
        setError(
          caught instanceof ApiError ? caught.message : "Could not verify this address.",
        );
      });
  }, [token]);

  return (
    <AuthLayout
      title="Email verification"
      subtitle="Confirming the address on your Attestive account."
      footer={
        <Link to="/dashboard" className="font-medium text-electric hover:underline">
          Go to your dashboard
        </Link>
      }
    >
      {!token ? (
        <Alert>
          This link is missing its token. Sign in and request a new verification email from your
          profile.
        </Alert>
      ) : state === "pending" ? (
        <Spinner label="Verifying your email…" />
      ) : state === "verified" ? (
        <Alert tone="success">
          Your email address is verified. You can close this page — your account now shows as
          verified.
        </Alert>
      ) : (
        <Alert>{error ?? "This verification link is invalid or has already been used."}</Alert>
      )}
    </AuthLayout>
  );
}
