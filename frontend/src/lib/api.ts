const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface ApiOptions extends RequestInit {
  /** Skip JSON serialization (for FormData, etc.) */
  raw?: boolean;
}

export async function apiClient<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { raw, ...fetchOptions } = options;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...fetchOptions,
    headers: {
      ...(raw ? {} : { 'Content-Type': 'application/json' }),
      ...fetchOptions.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: 'Request failed', code: 'UNKNOWN' }));
    throw new Error(body.error ?? `API error ${res.status}`);
  }

  return res.json() as Promise<T>;
}
