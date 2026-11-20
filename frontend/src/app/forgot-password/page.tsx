"use client";

import { useState, type FormEvent } from "react";

import { apiFetch, readError } from "@/lib/api";
import {
  AuthLinks,
  AuthShell,
  Field,
  FormError,
  PrimaryButton,
  inputClassName,
} from "@/components/AuthForm";

export default function ForgotPasswordPage() {
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email: String(form.get("email") || "") }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setDone(true);
  }

  return (
    <AuthShell title="Reset password" subtitle="If the account exists, we send a reset link.">
      {done ? (
        <p className="text-sm text-ink">Check your email for the reset link.</p>
      ) : (
        <form className="space-y-4" onSubmit={onSubmit}>
          <Field label="Email">
            <input className={inputClassName} name="email" type="email" required />
          </Field>
          <FormError message={error} />
          <PrimaryButton disabled={pending}>{pending ? "Sending…" : "Send reset link"}</PrimaryButton>
        </form>
      )}
      <AuthLinks />
    </AuthShell>
  );
}
