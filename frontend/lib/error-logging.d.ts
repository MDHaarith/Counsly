export function hashUserId(userId?: string): Promise<string>;

export function shouldLogApiError(status: number): boolean;

export function readStoredUser(win?: Window): { id?: string } | null;

export function buildApiErrorLog(input?: {
  endpoint?: string;
  errorType?: string;
  message?: string;
  status?: number;
  timestamp?: string;
  userId?: string;
}): Promise<Record<string, unknown>>;

export function buildClientErrorLog(input?: {
  error?: Error;
  message?: string;
  route?: string;
  timestamp?: string;
  userId?: string;
}): Promise<Record<string, unknown>>;

export function submitErrorLog(payload: Record<string, unknown>, fetcher?: typeof fetch, baseUrl?: string): Promise<void>;

export function logApiError(input: Record<string, unknown>, options?: { baseUrl?: string; fetcher?: typeof fetch }): Promise<Record<string, unknown>>;

export function logClientError(input: Record<string, unknown>, options?: { baseUrl?: string; fetcher?: typeof fetch }): Promise<Record<string, unknown>>;

export function installClientErrorHandlers(options?: { baseUrl?: string; userId?: string; win?: Window }): void;
