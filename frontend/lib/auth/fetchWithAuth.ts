/**
 * Authenticated fetch wrapper. Auto-injects JWT token and handles refresh.
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let _getAccessToken: (() => string | null) | null = null;
let _refreshAccessToken: (() => Promise<string | null>) | null = null;
let _logout: (() => void) | null = null;

export function configureAuthFetch(
  getAccessToken: () => string | null,
  refreshAccessToken: () => Promise<string | null>,
  logout: () => void,
) {
  _getAccessToken = getAccessToken;
  _refreshAccessToken = refreshAccessToken;
  _logout = logout;
}

export async function authFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = _getAccessToken?.();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res = await fetch(`${BACKEND_URL}${path}`, { ...options, headers });

  // If 401, try refresh
  if (res.status === 401 && _refreshAccessToken) {
    const newToken = await _refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${BACKEND_URL}${path}`, { ...options, headers });
    } else {
      _logout?.();
      throw new Error("Session expired. Please log in again.");
    }
  }

  return res;
}
