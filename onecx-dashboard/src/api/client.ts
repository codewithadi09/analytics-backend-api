import { tokenStorage } from "@/lib/tokenStorage";
import type { ApiErrorBody, RefreshResponse } from "@/types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

/**
 * Fired when the session can no longer be salvaged (refresh failed or
 * there was never a token to begin with). AuthContext listens for this
 * so a 401 deep in some page's data fetch still routes back to /login,
 * without every call site needing to know about routing.
 */
const SESSION_EXPIRED_EVENT = "onecx:session-expired";

function announceSessionExpired(): void {
  tokenStorage.clear();
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

export function onSessionExpired(callback: () => void): () => void {
  window.addEventListener(SESSION_EXPIRED_EVENT, callback);
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, callback);
}

// Single-flight refresh lock — if five components hit a 401 at once
// (e.g. dashboard shell loading several widgets in parallel), they
// should all await the same in-flight refresh call, not each fire
// their own and race to rotate the refresh token out from under
// each other (remember: rotation invalidates the previous token).
let refreshPromise: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;

    const data: RefreshResponse = await res.json();
    tokenStorage.setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}

function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  /** Query params — undefined/null values are omitted, not sent as "undefined". */
  params?: { [key: string]: string | number | undefined | null };
  /** Public routes (login) skip attaching a bearer token and skip refresh-on-401. */
  skipAuth?: boolean;
}

function buildUrl(path: string, params?: RequestOptions["params"]): string {
  const url = new URL(`${BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function parseErrorBody(res: Response): Promise<ApiErrorBody["detail"]> {
  try {
    const data: ApiErrorBody = await res.json();
    if (data?.detail?.message) return data.detail;
  } catch {
    // fall through to generic message below
  }
  return { message: `Request failed with status ${res.status}`, code: "UNKNOWN_ERROR" };
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, params, skipAuth = false } = options;

  const doFetch = async (): Promise<Response> => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (!skipAuth) {
      const token = tokenStorage.getAccessToken();
      if (token) headers.Authorization = `Bearer ${token}`;
    }
    return fetch(buildUrl(path, params), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let res = await doFetch();

  // One retry after a silent refresh — never loop, never retry twice.
  if (res.status === 401 && !skipAuth) {
    const newToken = await refreshAccessToken();
    if (!newToken) {
      announceSessionExpired();
      const errBody = await parseErrorBody(res);
      throw new ApiError(errBody.message, errBody.code, res.status);
    }
    res = await doFetch();
  }

  if (!res.ok) {
    const errBody = await parseErrorBody(res);
    if (res.status === 401 && !skipAuth) {
      // Retried request still failed auth — session is unsalvageable.
      announceSessionExpired();
    }
    throw new ApiError(errBody.message, errBody.code, res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
