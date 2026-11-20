"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { apiFetch, readError, type OrganizationPublic } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { Field, FormError, PrimaryButton, inputClassName } from "@/components/AuthForm";

export default function AppHomePage() {
  const router = useRouter();
  const {
    user,
    loading,
    accessToken,
    organizations,
    currentOrg,
    selectOrg,
    logout,
    reloadMemberships,
  } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/sign-in");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16 text-sm text-slate-600">Loading…</main>
    );
  }

  async function createOrg(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setPending(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/organizations", {
      method: "POST",
      accessToken,
      body: JSON.stringify({ name: String(form.get("name") || "") }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const org = (await response.json()) as OrganizationPublic;
    await reloadMemberships();
    selectOrg(org);
    event.currentTarget.reset();
  }

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !currentOrg) return;
    setInviteError(null);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/organizations/invitations", {
      method: "POST",
      accessToken,
      organizationId: currentOrg.id,
      body: JSON.stringify({ email: String(form.get("email") || "") }),
    });
    if (!response.ok) {
      setInviteError(await readError(response));
      return;
    }
    event.currentTarget.reset();
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-12">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-slate-500">BizPilot</p>
          <h1 className="text-2xl font-semibold text-slate-900">Organizations</h1>
          <p className="mt-1 text-sm text-slate-600">
            Signed in as {user.email}
            {user.email_verified ? "" : " · email not verified"}
          </p>
        </div>
        <button
          type="button"
          className="text-sm underline"
          onClick={() => {
            void logout().then(() => router.push("/sign-in"));
          }}
        >
          Sign out
        </button>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-sm font-semibold">Switch organization</h2>
        {organizations.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">You do not belong to an organization yet.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {organizations.map((org) => (
              <li key={org.id}>
                <button
                  type="button"
                  onClick={() => selectOrg(org)}
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                    currentOrg?.id === org.id
                      ? "border-slate-900 bg-slate-50"
                      : "border-slate-200"
                  }`}
                >
                  <span className="font-medium">{org.name}</span>
                  <span className="ml-2 text-slate-500">
                    {org.base_currency_code}
                    {org.is_owner ? " · owner" : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-sm font-semibold">Create organization</h2>
        <p className="mt-1 text-sm text-slate-500">
          Requires a verified email. Default currency is ZMW.
        </p>
        <form className="mt-4 space-y-3" onSubmit={createOrg}>
          <Field label="Organization name">
            <input className={inputClassName} name="name" required minLength={2} />
          </Field>
          <FormError message={error} />
          <PrimaryButton disabled={pending}>
            {pending ? "Creating…" : "Create organization"}
          </PrimaryButton>
        </form>
      </section>

      {currentOrg?.is_owner ? (
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-sm font-semibold">Invite a member</h2>
          <p className="mt-1 text-sm text-slate-500">
            Inviting to {currentOrg.name}. They join with the same email address.
          </p>
          <form className="mt-4 space-y-3" onSubmit={invite}>
            <Field label="Email">
              <input className={inputClassName} name="email" type="email" required />
            </Field>
            <FormError message={inviteError} />
            <PrimaryButton>Send invitation</PrimaryButton>
          </form>
        </section>
      ) : null}
    </main>
  );
}
