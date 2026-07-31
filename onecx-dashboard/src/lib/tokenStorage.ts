/**
 * Centralized token storage. localStorage is fine here — this is an
 * internal tool with no XSS-exposed third-party content, and the
 * backend already treats a valid access token as sufficient for any
 * read, with refresh rotation limiting the blast radius of a leaked
 * refresh token to a single active session per user.
 */

const ACCESS_TOKEN_KEY = "onecx_access_token";
const REFRESH_TOKEN_KEY = "onecx_refresh_token";

export const tokenStorage = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};
