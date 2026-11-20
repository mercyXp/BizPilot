"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { apiFetch, readError, type AuthResponse } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import {
  AuthShell,
  Field,
  FormError,
  PrimaryButton,
  inputClassName,
} from "@/components/AuthForm";

export default function SignInPage() {
  const router = useRouter();
  const { setSession } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: String(form.get("email") || ""),
        password: String(form.get("password") || ""),
      }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const payload = (await response.json()) as AuthResponse;
    await setSession(payload);
    router.push("/app");
  }

  return (
    <AuthShell title="Sign in" subtitle="Use your BizPilot account to open your organizations.">
      <form className="space-y-4" onSubmit={onSubmit}>
        <Field label="Email">
          <input className={inputClassName} name="email" type="email" required />
        </Field>
        <Field label="Password">
          <input className={inputClassName} name="password" type="password" required />
        </Field>
        <FormError message={error} />
        <PrimaryButton disabled={pending}>{pending ? "Signing in…" : "Sign in"}</PrimaryButton>
      </form>
      <p className="mt-4 text-center text-sm text-secondary">
        <Link className="text-brand-deep underline-offset-2 hover:underline" href="/forgot-password">
          Forgot password
        </Link>
        {" · "}
        <Link className="text-brand-deep underline-offset-2 hover:underline" href="/sign-up">
          Create account
        </Link>
      </p>
    </AuthShell>
  );
}
