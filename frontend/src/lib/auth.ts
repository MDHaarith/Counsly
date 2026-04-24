export function getSession() {
  // TODO: read from httpOnly cookie via /api/auth/session
  return null;
}

export function isLoggedIn(): boolean {
  return getSession() !== null;
}
