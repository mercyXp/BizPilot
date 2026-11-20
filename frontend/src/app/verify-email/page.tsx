"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";

import { apiFetch, readError } from "@/lib/api";
import { AuthShell } from "@/components/AuthForm";

function VerifyInner() {
  const params = useSearchParams();
  const token = params.get("token");
  const [status, setStatus] = useState(token ? "Verifying…" : "Check your inbox");
  const [ok, setOk] = useState(false);

  useEffect(() => {
    if (!token) return;
    void (async () => {
      const response = await apiFetch("/api/v1/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      if (response.ok) {
        setOk(true);
        setStatus("Email verified. You can sign in and create an organization.");
      } else {
        setStatus(await readError(response));
      }
    })();
  }, [token]);

  return (
    <AuthShell title="Verify email" subtitle="We send a link after you create an account.">
      <p className="text-sm text-ink">{status}</p>
      {!token ? (
        <p className="mt-3 text-sm text-secondary">
          Open the verification link from your email. In development the API logs the URL
          and stores it in outbound_emails.
        </p>
      ) : null}
      {ok ? (
        <p className="mt-4 text-sm">
          <Link className="underline" href="/sign-in">
            Continue to sign in
          </Link>
        </p>
      ) : null}
    </AuthShell>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyInner />
    </Suspense>
  );
}
