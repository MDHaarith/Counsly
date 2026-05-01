interface ApiOptions extends RequestInit {
  raw?: boolean;
}

function buildRequestHeaders(input: HeadersInit | undefined, raw: boolean): Headers {
  const headers = new Headers(input);

  if (!raw && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return headers;
}

export class ApiClientError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

export async function apiClient<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { raw, ...fetchOptions } = options;
  const requestUrl = path;

  const res = await fetch(requestUrl, {
    ...fetchOptions,
    // Note: credentials: "include" works for client-side fetches.
    // For server-side fetches, the caller must manually pass the Cookie header in fetchOptions.headers.
    credentials: "include",
    headers: buildRequestHeaders(fetchOptions.headers, Boolean(raw)),
  });

  if (!res.ok) {
    let errorMessage = `API error ${res.status}`;
    let errorCode: string | undefined;
    try {
      const body = await res.json();
      errorMessage = body.error ?? errorMessage;
      errorCode = body.code;
    } catch {
      // ignore json parse error
    }
    throw new ApiClientError(errorMessage, res.status, errorCode);
  }

  return res.json() as Promise<T>;
}

export function postJson<T>(path: string, body: unknown, headers?: HeadersInit) {
  return apiClient<T>(path, { method: "POST", body: JSON.stringify(body), headers });
}

export { buildRequestHeaders };
