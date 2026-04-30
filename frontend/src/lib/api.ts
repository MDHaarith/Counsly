const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

interface ApiOptions extends RequestInit {
  raw?: boolean;
}

export async function apiClient<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { raw, ...fetchOptions } = options;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...fetchOptions,
    credentials: "include",
    headers: {
      ...(raw ? {} : { "Content-Type": "application/json" }),
      ...fetchOptions.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Request failed", code: "UNKNOWN" }));
    throw new Error(body.error ?? `API error ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export function getConfigStatus<T>() {
  return apiClient<T>("/api/config/status");
}

export function getSession<T>() {
  return apiClient<T>("/api/auth/session");
}

export function postJson<T>(path: string, body: unknown) {
  return apiClient<T>(path, { method: "POST", body: JSON.stringify(body) });
}
