"use client";

import { Suspense, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

import { apiFetch, readError } from "@/lib/api";
import {
  AuthShell,
  Field,
  FormError,
  PrimaryButton,
  inputClassName,
} from "@/components/AuthForm";

function ResetInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({
        token,
        password: String(form.get("password") || ""),
      }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setDone(true);
  }

  return (
    <AuthShell title="Choose a new password" subtitle="This link can be used once.">
      {done ? (
        <p className="text-sm">
          Password updated.{" "}
          <Link className="underline" href="/sign-in">
            Sign in
          </Link>
        </p>
      ) : (
        <form className="space-y-4" onSubmit={onSubmit}>
          <Field label="New password">
            <input
              className={inputClassName}
              name="password"
              type="password"
              minLength={10}
              required
            />
          </Field>
          <FormError message={error} />
          <PrimaryButton disabled={pending || !token}>
            {pending ? "Updating…" : "Update password"}
          </PrimaryButton>
        </form>
      )}
    </AuthShell>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetInner />
    </Suspense>
  );
}
