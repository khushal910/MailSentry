import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient from "@/services/apiClient";
import { useAuth } from "@/context/AuthContext";
import { prefetchUnclassifiedEmails } from "@/hooks/useUnclassifiedQueue";
import { prefetchClassifiedEmails } from "@/hooks/usePredictiveHistory";

/**
 * /auth/callback
 *
 * This page is the landing target for the Google OAuth 2.0 redirect.
 * The backend sends the browser here with ?token=<JWT> after a successful
 * OAuth exchange. This page:
 *   1. Reads the token from the URL.
 *   2. Removes the token from the URL bar immediately (security hygiene).
 *   3. POSTs the token to /auth/google/set-token which sets an HttpOnly cookie.
 *   4. Calls refresh() to populate AuthContext with the logged-in user.
 *   5. Navigates to /dashboard.
 *
 * If anything fails (token expired, network error, etc.) it redirects to /login
 * with a toast error.
 */

export const Route = createFileRoute("/auth/callback")({
  head: () => ({
    meta: [{ title: "Signing in… — MailSentry" }, { name: "robots", content: "noindex" }],
  }),
  component: OAuthCallbackPage,
});

function OAuthCallbackPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { refresh } = useAuth();
  const handled = useRef(false);

  useEffect(() => {
    // Guard against React StrictMode double-invocation
    if (handled.current) return;
    handled.current = true;

    const run = async () => {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token");
      const oauthError = params.get("oauth_error");

      // Remove the token from the URL bar IMMEDIATELY so it is never in browser history
      window.history.replaceState({}, document.title, window.location.pathname);

      if (oauthError) {
        toast.error(`Google sign-in failed: ${oauthError.replace(/_/g, " ")}`);
        navigate({ to: "/login" });
        return;
      }

      if (!token) {
        toast.error("OAuth handoff failed: no token received.");
        navigate({ to: "/login" });
        return;
      }

      try {
        // Step 1: Store token in localStorage as fallback & exchange for HttpOnly cookie
        localStorage.setItem("token", token);
        const { data } = await apiClient.post("/auth/google/set-token", { token });

        if (!data?.success) {
          throw new Error(data?.message || "Failed to set authentication token.");
        }

        // Step 2: Re-fetch the user so AuthContext is populated with the logged-in user.
        await refresh();

        // Silent background prefetching — does not block navigation or UI
        void prefetchUnclassifiedEmails(queryClient);
        void prefetchClassifiedEmails(queryClient);

        // Step 3: Navigate to dashboard smoothly using SPA router replace
        navigate({ to: "/dashboard", replace: true });
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Something went wrong during Google sign-in.";
        console.error("[OAuthCallback] error:", err);
        toast.error(message);
        navigate({ to: "/login" });
      }
    };

    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4 text-center">
        {/* Animated spinner */}
        <div className="relative h-12 w-12">
          <div className="absolute inset-0 rounded-full border-4 border-muted" />
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-brand" />
        </div>
        <p className="text-sm font-medium text-muted-foreground">Completing Google sign-in…</p>
      </div>
    </div>
  );
}
