"use client";

import { Clock, UserPlus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Field, Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { apiFetch, readError } from "@/lib/api";

type Member = { id: string; email: string; full_name: string; role_codes: string[]; status: string };

export default function AssistantsPage() {
  const { accessToken, currentOrg, tenantFetch, permissions } = useAuth();
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteOk, setInviteOk] = useState(false);
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [members, setMembers] = useState<Member[]>([]);

  useEffect(() => {
    if (!permissions.includes("users.manage")) return;
    void tenantFetch("/api/v1/memberships").then(async (response) => {
      if (response.ok) setMembers((await response.json()) as Member[]);
    });
  }, [permissions, tenantFetch]);

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !currentOrg) return;
    setInviteError(null);
    setInviteOk(false);
    setPending(true);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/organizations/invitations", {
      method: "POST",
      accessToken,
      organizationId: currentOrg.id,
      body: JSON.stringify({ email: String(form.get("email") || "") }),
    });
    setPending(false);
    if (!response.ok) {
      setInviteError(await readError(response));
      return;
    }
    setInviteOk(true);
    event.currentTarget.reset();
  }

  return (
    <div>
      <PageHeader
        title="Store assistants"
        description="Manage staff who help run your store"
        actions={
          <>
            <Button variant="outline">Refresh</Button>
            <Button icon={<UserPlus className="h-3.5 w-3.5" />} onClick={() => setOpen(true)}>
              Invite assistant
            </Button>
          </>
        }
      />

      {inviteError ? (
        <Alert tone="critical" title="Invitation not sent" className="mb-4">
          {inviteError}
        </Alert>
      ) : null}
      {inviteOk ? (
        <Alert tone="success" title="Invitation sent" className="mb-4">
          They can accept from the email we queued for this organisation.
        </Alert>
      ) : null}

      {open && currentOrg?.is_owner ? (
        <Card className="mb-4 p-4">
          <h2 className="text-sm font-semibold text-ink">Invite a team member</h2>
          <p className="mt-1 text-sm text-secondary">
            Inviting to {currentOrg.name}. They join with the same email address.
          </p>
          <form className="mt-4 max-w-md space-y-3" onSubmit={invite}>
            <Field label="Email">
              <Input name="email" type="email" required />
            </Field>
            <div className="flex gap-2">
              <Button type="submit" disabled={pending}>
                {pending ? "Sending…" : "Send invitation"}
              </Button>
              <Button variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      ) : null}

      <h2 className="mb-2 text-sm font-semibold text-ink">Active assistants</h2>
      {members.length ? (
        <Card className="mb-4 overflow-hidden">
          <ul className="divide-y divide-border text-sm">
            {members.map((member) => (
              <li key={member.id} className="flex items-center justify-between px-3 py-2">
                <span>
                  <span className="font-medium text-ink">{member.full_name}</span>
                  <span className="ml-2 text-secondary">{member.email}</span>
                </span>
                <span className="text-xs text-muted">{member.role_codes.join(", ")}</span>
              </li>
            ))}
          </ul>
        </Card>
      ) : (
      <EmptyState
        icon={UserPlus}
        title="No active assistants"
        description="Invite a team member to help manage day-to-day operations of your store."
        action={
          <Button icon={<UserPlus className="h-3.5 w-3.5" />} onClick={() => setOpen(true)}>
            Invite assistant
          </Button>
        }
      />
      )}

      <h2 className="mb-2 mt-6 text-sm font-semibold text-ink">Pending invitations</h2>
      <EmptyState
        icon={Clock}
        title="No pending invitations"
        description="Invitations you send will appear here until they are accepted."
      />
    </div>
  );
}
