"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

import { apiFetch, readError } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { AuthShell, FormError, PrimaryButton } from "@/components/AuthForm";

function AcceptInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const router = useRouter();
  const { user, accessToken, loading, reloadMemberships } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/sign-in`);
    }
  }, [loading, user, router]);

  async function accept() {
    if (!accessToken) return;
    setPending(true);
    const response = await apiFetch("/api/v1/invitations/accept", {
      method: "POST",
      accessToken,
      body: JSON.stringify({ token }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    await reloadMemberships();
    router.push("/app");
  }

  return (
    <AuthShell title="Join organization" subtitle="Accept the invitation with the account that matches the invited email.">
      <FormError message={error} />
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          void accept();
        }}
      >
        <PrimaryButton disabled={pending || !token || !accessToken}>
          {pending ? "Joining…" : "Accept invitation"}
        </PrimaryButton>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Wrong account?{" "}
        <Link className="underline" href="/sign-in">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense>
      <AcceptInner />
    </Suspense>
  );
}
