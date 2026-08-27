import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { DashboardSidebar } from "@/components/DashboardSidebar";
import { DashboardTopbar } from "@/components/DashboardTopbar";
import { useAuth } from "@/context/AuthContext";
import { useMaintenance } from "@/context/MaintenanceContext";

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
    </div>
  );
}
