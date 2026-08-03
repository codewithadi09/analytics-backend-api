import { useState, type FormEvent } from "react";
import { createMember, listUsers, resetMemberPassword } from "@/api/admin";
import { useApiData } from "@/hooks/useApiData";
import { useToast } from "@/context/ToastContext";
import { ApiError } from "@/api/client";
import { DataTable, ErrorState, BooleanBadge, SectionHeading } from "@/components/ui/DataDisplay";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { Modal, ConfirmModal } from "@/components/ui/Modal";
import type { UserSummary } from "@/types/api";

export function AdminPage() {
  const { data, isLoading, error, refetch } = useApiData(() => listUsers(), []);

  const [addOpen, setAddOpen] = useState(false);
  const [resetTarget, setResetTarget] = useState<UserSummary | null>(null);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Admin Panel</h1>
        <button className="btn-primary" onClick={() => setAddOpen(true)}>
          Add member
        </button>
      </div>

      <SectionHeading>All users</SectionHeading>

      {error && <ErrorState message={error} onRetry={refetch} />}
      {!error && isLoading && <SkeletonTable rows={5} />}
      {!error && !isLoading && data && (
        <DataTable<UserSummary>
          rowKey={(r) => String(r.id)}
          emptyMessage="No users found."
          columns={[
            { key: "username", header: "Username", accessor: (r) => r.username },
            {
              key: "role",
              header: "Role",
              accessor: (r) => <BooleanBadge value={r.is_superadmin} trueLabel="Superadmin" falseLabel="Member" />,
            },
            {
              key: "active",
              header: "Active",
              accessor: (r) => <BooleanBadge value={r.is_active} />,
            },
            {
              key: "created",
              header: "Created",
              accessor: (r) => new Date(r.created_at).toLocaleDateString(),
            },
            {
              key: "actions",
              header: "",
              accessor: (r) =>
                r.is_superadmin ? null : (
                  <button className="btn-text" onClick={() => setResetTarget(r)}>
                    Reset password
                  </button>
                ),
            },
          ]}
          rows={data.users}
        />
      )}

      <AddMemberModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={() => {
          setAddOpen(false);
          refetch();
        }}
      />

      <ResetPasswordModal target={resetTarget} onClose={() => setResetTarget(null)} />
    </div>
  );
}

function AddMemberModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const { showToast } = useToast();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await createMember(username, password);
      showToast(`Member "${username}" created.`);
      setUsername("");
      setPassword("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add member">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="field-label" htmlFor="new_username">
            Username
          </label>
          <input
            id="new_username"
            className="input"
            minLength={3}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="mb-5">
          <label className="field-label" htmlFor="new_member_password">
            Password
          </label>
          <input
            id="new_member_password"
            type="password"
            className="input"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-3">
          <button type="button" className="btn-text" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? "Creating…" : "Create member"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ResetPasswordModal({ target, onClose }: { target: UserSummary | null; onClose: () => void }) {
  const { showToast } = useToast();
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(false);

  function handleClose() {
    setNewPassword("");
    setError(null);
    setConfirming(false);
    onClose();
  }

  async function handleReset() {
    if (!target) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await resetMemberPassword(target.username, newPassword);
      showToast(`Password reset for "${target.username}".`);
      handleClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setConfirming(false);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!target) return null;

  if (confirming) {
    return (
      <ConfirmModal
        open
        title="Reset password?"
        message={`This immediately invalidates "${target.username}"'s current session. They'll need the new password to sign in again.`}
        confirmLabel="Reset password"
        onConfirm={handleReset}
        onCancel={() => setConfirming(false)}
        isLoading={isSubmitting}
      />
    );
  }

  return (
    <Modal open onClose={handleClose} title={`Reset password for "${target.username}"`}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setConfirming(true);
        }}
      >
        <div className="mb-5">
          <label className="field-label" htmlFor="reset_password">
            New password
          </label>
          <input
            id="reset_password"
            type="password"
            className="input"
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoFocus
          />
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-3">
          <button type="button" className="btn-text" onClick={handleClose}>
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            Continue
          </button>
        </div>
      </form>
    </Modal>
  );
}
