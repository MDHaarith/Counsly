const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

interface ApiOptions extends RequestInit {
  raw?: boolean;
}

export async function apiClient<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { raw, ...fetchOptions } = options;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...fetchOptions,
    // Note: credentials: "include" works for client-side fetches.
    // For server-side fetches, the caller must manually pass the Cookie header in fetchOptions.headers.
    credentials: "include",
    headers: {
      ...(raw ? {} : { "Content-Type": "application/json" }),
      ...fetchOptions.headers,
    },
  });

  if (!res.ok) {
    let errorMessage = `API error ${res.status}`;
    try {
      const body = await res.json();
      errorMessage = body.error ?? errorMessage;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  return res.json() as Promise<T>;
}

export function getConfigStatus<T>(headers?: HeadersInit) {
  return apiClient<T>("/api/config/status", { headers });
}

export function getSession<T>(headers?: HeadersInit) {
  return apiClient<T>("/api/auth/session", { headers });
}

export function getProfile<T>(headers?: HeadersInit) {
  return apiClient<T>("/api/profile", { headers });
}

export function postJson<T>(path: string, body: unknown, headers?: HeadersInit) {
  return apiClient<T>(path, { method: "POST", body: JSON.stringify(body), headers });
}
