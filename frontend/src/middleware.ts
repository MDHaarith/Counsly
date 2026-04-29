import { NextResponse, type NextRequest } from "next/server";

import { getRouteGuardAction } from "@/lib/routeGuard";

const SESSION_COOKIE_NAME = process.env.NEXT_PUBLIC_SESSION_COOKIE_NAME ?? "counsly_session";

export function middleware(request: NextRequest) {
  const maintenanceEnabled = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === "true";
  const { pathname } = request.nextUrl;
  const action = getRouteGuardAction(pathname, Boolean(request.cookies.get(SESSION_COOKIE_NAME)), maintenanceEnabled);

  if (action.kind === "rewrite") {
    const url = request.nextUrl.clone();
    url.pathname = action.pathname;
    return NextResponse.rewrite(url);
  }

  if (action.kind === "redirect") {
    const url = request.nextUrl.clone();
    url.pathname = action.pathname;
    url.search = "";
    if (action.next) {
      url.searchParams.set("next", action.next);
    }
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|favicon.ico).*)"],
};
