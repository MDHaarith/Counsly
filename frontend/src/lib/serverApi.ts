import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { ApiClientError, apiClient } from "@/lib/api";

const SESSION_COOKIE_NAME = process.env.NEXT_PUBLIC_SESSION_COOKIE_NAME ?? "counsly_session";

function forwardedValue(value: string | null): string | null {
  return value?.split(",")[0].trim() || null;
}

export async function getRequestOrigin(): Promise<string> {
  const headerStore = await headers();
  const forwardedProto = forwardedValue(headerStore.get("x-forwarded-proto"));
  const forwardedHost = forwardedValue(headerStore.get("x-forwarded-host"));
  const host = forwardedHost ?? headerStore.get("host") ?? "127.0.0.1:3000";
  const protocol = forwardedProto ?? (process.env.NODE_ENV === "development" ? "http" : "https");
  return `${protocol}://${host}`;
}

export async function getServerApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const origin = await getRequestOrigin();
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);
  const requestHeaders = new Headers(init.headers);

  if (sessionCookie && !requestHeaders.has("cookie")) {
    requestHeaders.set("cookie", `${SESSION_COOKIE_NAME}=${sessionCookie.value}`);
  }

  return apiClient<T>(`${origin}${path}`, {
    ...init,
    headers: requestHeaders,
  });
}

export function redirectToLoginOnUnauthorized(error: unknown, nextPath: string): never | void {
  if (error instanceof ApiClientError && error.status === 401) {
    redirect(`/login?next=${encodeURIComponent(nextPath)}`);
  }
}
