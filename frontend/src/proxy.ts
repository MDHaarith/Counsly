import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const maintenanceEnabled = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === "true";
  const { pathname } = request.nextUrl;

  if (!maintenanceEnabled || pathname === "/maintenance" || pathname.startsWith("/_next")) {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = "/maintenance";
  return NextResponse.rewrite(url);
}

export const config = {
  matcher: ["/((?!api|favicon.ico).*)"],
};
