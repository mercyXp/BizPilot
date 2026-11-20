"use client";

import Link from "next/link";
import type { FormEvent, ReactNode } from "react";

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
      <p className="text-sm font-medium uppercase tracking-wide text-slate-500">BizPilot</p>
      <h1 className="mt-2 text-2xl font-semibold text-slate-900">{title}</h1>
      <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
      <div className="mt-8 rounded-lg border border-slate-200 bg-white p-6">{children}</div>
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
  return (
    <label className="block space-y-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {children}
    </label>
  );
}

export const inputClassName =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900";

export function PrimaryButton({
  children,
  disabled,
}: {
  children: ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
    >
      {children}
    </button>
  );
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return <p className="text-sm text-red-700">{message}</p>;
}

export function AuthLinks() {
  return (
    <p className="mt-4 text-center text-sm text-slate-600">
      <Link className="underline" href="/sign-in">
        Sign in
      </Link>
      {" · "}
      <Link className="underline" href="/sign-up">
        Create account
      </Link>
    </p>
  );
}

export type SubmitHandler = (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
