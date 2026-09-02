import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { DashboardSidebar } from "@/components/DashboardSidebar";
import { DashboardTopbar } from "@/components/DashboardTopbar";
import { useAuth } from "@/context/AuthContext";
import { useMaintenance } from "@/context/MaintenanceContext";
import { prefetchUnclassifiedEmails } from "@/hooks/useUnclassifiedQueue";
import { prefetchClassifiedEmails } from "@/hooks/usePredictiveHistory";

import { ClassificationProvider } from "@/context/ClassificationContext";
import { GlobalClassificationIndicator } from "@/components/GlobalClassificationIndicator";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — MailSentry" },
      { name: "description", content: "Your MailSentry control center." },
    ],
  }),
  component: DashboardLayout,
});

function DashboardLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const { isMaintenance, adminBypass } = useMaintenance();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const hasPrefetchedRef = useRef(false);

  // Proactively and silently fetch emails in the background upon login
  // NEVER blocks navigation, UI rendering, or other dashboard services
  useEffect(() => {
    if (isAuthenticated && !isLoading && !hasPrefetchedRef.current) {
      hasPrefetchedRef.current = true;
      void prefetchUnclassifiedEmails(queryClient);
      void prefetchClassifiedEmails(queryClient);
    }
  }, [isAuthenticated, isLoading, queryClient]);

  useEffect(() => {
    if (!isAuthenticated) {
      hasPrefetchedRef.current = false;
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isMaintenance && (!adminBypass || !isAuthenticated)) {
      if (!isLoading) {
        navigate({ to: "/maintenance", replace: true });
      }
      return;
    }

    if (!isLoading && !isAuthenticated) {
      navigate({ to: "/login", replace: true });
    }
  }, [isMaintenance, adminBypass, isLoading, isAuthenticated, navigate]);

  if (isMaintenance && (!adminBypass || !isAuthenticated)) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="relative h-12 w-12">
          <div className="absolute inset-0 rounded-full border-4 border-muted" />
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-brand" />
        </div>
      </div>
    );
  }

  // While unauthenticated (redirect pending), render nothing
  if (!isAuthenticated) return null;

  return (
    <ClassificationProvider>
      <div className="flex min-h-screen w-full bg-background">
        <div className="hidden md:block">
          <DashboardSidebar />
        </div>
        <div className="flex min-w-0 flex-1 flex-col">
          <DashboardTopbar />
          <main className="flex-1 p-4 md:p-8">
            <Outlet />
          </main>
        </div>
        <GlobalClassificationIndicator />
      </div>
    </ClassificationProvider>
  );
}
