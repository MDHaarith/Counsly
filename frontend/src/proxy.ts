import { NextResponse, type NextRequest } from "next/server";

const AUTH_ROUTES = [
  "/dashboard",
  "/recommendations",
  "/choices",
  "/explore",
  "/profile",
  "/onboarding",
];

function isAuthRoute(pathname: string) {
  return AUTH_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export function proxy(request: NextRequest) {
  const maintenanceEnabled = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === "true";
  const { pathname } = request.nextUrl;

  if (maintenanceEnabled && pathname !== "/maintenance" && !pathname.startsWith("/_next")) {
    const url = request.nextUrl.clone();
    url.pathname = "/maintenance";
    return NextResponse.rewrite(url);
  }

  if (isAuthRoute(pathname) && !request.cookies.get("counsly_session")) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (pathname === "/login" && request.cookies.get("counsly_session")) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|favicon.ico).*)"],
};
