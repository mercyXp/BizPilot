"use client";

import Link from "next/link";
import type { FormEvent, ReactNode } from "react";

import { Logo } from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { Field as UiField, inputClassName } from "@/components/ui/input";

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-12">
      <Link href="/" className="w-fit" aria-label="BizPilot home">
        <Logo height={40} priority />
      </Link>
      <h1 className="mt-6 text-2xl font-semibold tracking-tight text-ink">{title}</h1>
      <p className="mt-2 text-sm text-secondary">{subtitle}</p>
      <div className="mt-8 rounded-xl border border-border bg-surface p-6 shadow-card">{children}</div>
    </main>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return <UiField label={label}>{children}</UiField>;
}

export { inputClassName };

export function PrimaryButton({
  children,
  disabled,
}: {
  children: ReactNode;
  disabled?: boolean;
}) {
  return (
    <Button type="submit" disabled={disabled} className="w-full">
      {children}
    </Button>
  );
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <Alert tone="critical">{message}</Alert>
  );
}

export function AuthLinks() {
  return (
    <p className="mt-4 text-center text-sm text-secondary">
      <Link className="text-brand-deep underline-offset-2 hover:underline" href="/sign-in">
        Sign in
      </Link>
      {" · "}
      <Link className="text-brand-deep underline-offset-2 hover:underline" href="/sign-up">
        Create account
      </Link>
    </p>
  );
}

export type SubmitHandler = (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
