import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { changeOwnPassword } from "@/api/auth";
import { ApiError } from "@/api/client";

export function AccountPage() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await changeOwnPassword(currentPassword, newPassword);
      showToast("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Account</h1>
      </div>

      <div className="mb-6 card-compact">
        <div className="text-xs text-zinc-500">Signed in as</div>
        <div className="mt-0.5 text-sm font-medium text-zinc-900">
          {user?.username}
          {user?.is_superadmin && <span className="badge-positive ml-2">Superadmin</span>}
        </div>
      </div>

      <div className="mb-6 card">
        <h2 className="mb-4 text-sm font-medium text-zinc-900">Change password</h2>
        <form onSubmit={handleChangePassword}>
          <div className="mb-4">
            <label className="field-label" htmlFor="current_password">
              Current password
            </label>
            <input
              id="current_password"
              type="password"
              className="input"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div className="mb-5">
            <label className="field-label" htmlFor="new_password">
              New password
            </label>
            <input
              id="new_password"
              type="password"
              className="input"
              autoComplete="new-password"
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>

          {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? "Saving…" : "Change password"}
          </button>
        </form>
      </div>

      <button className="btn-secondary" onClick={handleLogout}>
        Log out
      </button>
    </div>
  );
}
