import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/register", "/_next", "/favicon.ico"];
const API_PATHS = ["/api/"]; // API routes handle their own auth

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths and API routes through
  if (
    PUBLIC_PATHS.some((p) => pathname.startsWith(p)) ||
    API_PATHS.some((p) => pathname.startsWith(p)) ||
    pathname === "/"
  ) {
    // Check for auth cookie to decide redirect on "/"
    // Actually, we let the client-side AuthContext handle this.
    // The page component itself redirects if unauthenticated.
    return NextResponse.next();
  }

  // All other paths pass through — client handles auth
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
