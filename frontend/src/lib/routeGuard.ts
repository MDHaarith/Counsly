export type RouteGuardAction =
  | { kind: "next" }
  | { kind: "redirect"; pathname: string; next?: string }
  | { kind: "rewrite"; pathname: string };

const AUTH_ROUTES = [
  "/dashboard",
  "/recommendations",
  "/choices",
  "/explore",
  "/profile",
  "/onboarding",
];

const STATIC_PREFIXES = ["/_next", "/api"];
const STATIC_PATHS = ["/favicon.ico", "/robots.txt", "/sitemap.xml", "/health"];

export function isAuthRoute(pathname: string) {
  return AUTH_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export function isPassThroughRoute(pathname: string) {
  return STATIC_PATHS.includes(pathname) || STATIC_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function getRouteGuardAction(pathname: string, hasSession: boolean, maintenanceEnabled: boolean): RouteGuardAction {
  if (isPassThroughRoute(pathname)) {
    return { kind: "next" };
  }

  if (maintenanceEnabled && pathname !== "/maintenance") {
    return { kind: "rewrite", pathname: "/maintenance" };
  }

  if (isAuthRoute(pathname) && !hasSession) {
    return { kind: "redirect", pathname: "/login", next: pathname };
  }

  if (pathname === "/login" && hasSession) {
    return { kind: "redirect", pathname: "/dashboard" };
  }

  return { kind: "next" };
}
