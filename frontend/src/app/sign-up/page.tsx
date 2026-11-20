"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, readError } from "@/lib/api";
import {
  AuthShell,
  Field,
  FormError,
  PrimaryButton,
  inputClassName,
} from "@/components/AuthForm";
import Link from "next/link";

export default function SignUpPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: String(form.get("full_name") || ""),
        email: String(form.get("email") || ""),
        password: String(form.get("password") || ""),
      }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    router.push("/verify-email");
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Verify your email before creating an organization."
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <Field label="Full name">
          <input className={inputClassName} name="full_name" required />
        </Field>
        <Field label="Email">
          <input className={inputClassName} name="email" type="email" required />
        </Field>
        <Field label="Password">
          <input
            className={inputClassName}
            name="password"
            type="password"
            minLength={10}
            required
          />
        </Field>
        <FormError message={error} />
        <PrimaryButton disabled={pending}>{pending ? "Creating…" : "Create account"}</PrimaryButton>
      </form>
      <p className="mt-4 text-center text-sm text-secondary">
        Already have an account?{" "}
        <Link className="text-brand-deep underline-offset-2 hover:underline" href="/sign-in">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
