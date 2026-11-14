// Default to the API on the same hostname the page was opened with. The refresh
// cookie is SameSite=Lax, so a page on 127.0.0.1 talking to localhost:8000 (or vice
// versa) is cross-site and the browser drops it on every reload.
const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: { field: string; message: string }[];

  constructor(message: string, code: string, status: number, details: { field: string; message: string }[] = []) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }

  fieldError(field: string): string | undefined {
    return this.details.find((detail) => detail.field === field)?.message;
  }
}

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getApiBaseUrl(): string {
  return API_URL;
}

function notifyUnauthorized(): void {
  window.dispatchEvent(new Event("sf:unauthorized"));
}

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    details?: { field: string; message: string }[];
  };
};

async function parseError(response: Response): Promise<ApiError> {
  let envelope: ErrorEnvelope = {};
  try {
    envelope = (await response.json()) as ErrorEnvelope;
  } catch {
    // Non-JSON error body (proxy, gateway) — fall through to a generic message.
  }
  const fallback =
    response.status >= 500
      ? "The server ran into a problem. Please try again."
      : "Something went wrong. Please try again.";
  return new ApiError(
    envelope.error?.message ?? fallback,
    envelope.error?.code ?? "request_failed",
    response.status,
    envelope.error?.details ?? [],
  );
}

async function rawRequest(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return fetch(`${API_URL}${path}`, { ...init, headers, credentials: "include" });
}

async function refreshAccessToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) {
      setAccessToken(null);
      return false;
    }
    const payload = (await response.json()) as { access_token: string };
    setAccessToken(payload.access_token);
    return true;
  } catch {
    setAccessToken(null);
    return false;
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  let response: Response;
  try {
    response = await rawRequest(path, init);
  } catch {
    throw new ApiError(
      "Cannot reach the Attestive API. Is the backend running?",
      "network_error",
      0,
    );
  }

  if (response.status === 401 && retry && !path.startsWith("/auth/")) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiFetch<T>(path, init, false);
    }
    notifyUnauthorized();
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const authApi = {
  refresh: refreshAccessToken,
  logoutRequest: async (): Promise<void> => {
    await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
    setAccessToken(null);
  },
};
