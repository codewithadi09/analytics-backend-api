import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { onSessionExpired } from "@/api/client";
import { login as loginRequest } from "@/api/auth";
import { tokenStorage } from "@/lib/tokenStorage";
import type { CurrentUser } from "@/types/api";

/**
 * The backend embeds user_id/is_superadmin directly in the JWT so
 * protected routes never need a DB lookup (see auth/jwt.py). The
 * frontend piggybacks on that same design: decode the access token's
 * payload client-side rather than maintaining a parallel /me endpoint
 * that doesn't exist in the API.
 */
function decodeUserFromToken(accessToken: string): CurrentUser | null {
  try {
    const payloadB64 = accessToken.split(".")[1];
    const payload = JSON.parse(atob(payloadB64.replace(/-/g, "+").replace(/_/g, "/")));
    if (typeof payload.user_id !== "number" || typeof payload.sub !== "string") return null;
    return {
      username: payload.sub,
      user_id: payload.user_id,
      is_superadmin: Boolean(payload.is_superadmin),
    };
  } catch {
    return null;
  }
}

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const existingToken = tokenStorage.getAccessToken();
    if (existingToken) setUser(decodeUserFromToken(existingToken));
    setIsLoading(false);
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  useEffect(() => onSessionExpired(logout), [logout]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await loginRequest(username, password);
    tokenStorage.setTokens(res.access_token, res.refresh_token);
    setUser(decodeUserFromToken(res.access_token));
  }, []);

  const value = useMemo(() => ({ user, isLoading, login, logout }), [user, isLoading, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
