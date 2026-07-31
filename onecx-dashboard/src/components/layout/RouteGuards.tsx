import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return null; // brief flash guard while token is decoded on first paint
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;

  return <>{children}</>;
}

/**
 * Superadmin-only routes. A member navigating here directly (e.g. a
 * stale bookmark) is bounced to the dashboard root, not shown a 403
 * page — per the doc, a member should never be routed through admin
 * territory at all.
 */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.is_superadmin) return <Navigate to="/" replace />;

  return <>{children}</>;
}
