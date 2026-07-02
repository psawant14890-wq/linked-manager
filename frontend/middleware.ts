// Gates every protected route behind a valid NextAuth session. Without
// this, an unauthenticated visit to e.g. /dashboard just renders an empty
// shell with failed/pending API calls (since apiClient has no token to
// attach) instead of sending the person to log in first.
export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/inbox/:path*",
    "/follow-ups/:path*",
    "/generate/:path*",
    "/jobs/:path*",
    "/connections/:path*",
    "/analytics/:path*",
    "/reports/:path*",
    "/import/:path*",
  ],
};
