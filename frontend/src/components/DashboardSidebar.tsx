import { useEffect } from "react";
import { Link, useRouterState, useNavigate, useRouter } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Wand2,
  History,
  UserCircle,
  Settings,
  LogOut,
  MailSearch,
  Cpu,
} from "lucide-react";
import { BrandLogo } from "./BrandLogo";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { prefetchClassifiedEmails } from "@/hooks/usePredictiveHistory";

const links: Array<{
  to:
    | "/dashboard"
    | "/dashboard/classifier"
    | "/dashboard/auto-classifier"
    | "/dashboard/production-model"
    | "/dashboard/history"
    | "/dashboard/profile"
    | "/dashboard/settings";
  label: string;
  icon: typeof LayoutDashboard;
  exact?: boolean;
}> = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/dashboard/auto-classifier", label: "New Emails", icon: MailSearch },
  { to: "/dashboard/history", label: "Classified Emails", icon: History },
  { to: "/dashboard/classifier", label: "Manual Classifier", icon: Wand2 },
  { to: "/dashboard/production-model", label: "Production Model", icon: Cpu },
  { to: "/dashboard/profile", label: "Profile", icon: UserCircle },
  { to: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function DashboardSidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (r) => r.location.pathname });
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Proactively warm up route code for all sidebar items when idle
  useEffect(() => {
    const idlePrefetch = () => {
      links.forEach((l) => {
        router.preloadRoute({ to: l.to }).catch(() => {});
      });
    };

    if (typeof window !== "undefined" && "requestIdleCallback" in window) {
      const id = (window as unknown as { requestIdleCallback: (cb: () => void, opts?: { timeout: number }) => number }).requestIdleCallback(
        idlePrefetch,
        { timeout: 1500 }
      );
      return () => {
        if ("cancelIdleCallback" in window) {
          (window as unknown as { cancelIdleCallback: (id: number) => void }).cancelIdleCallback(id);
        }
      };
    } else {
      const t = setTimeout(idlePrefetch, 200);
      return () => clearTimeout(t);
    }
  }, [router]);

  const handleLinkPrefetch = (to: string) => {
    router.preloadRoute({ to: to as any }).catch(() => {});
    if (to === "/dashboard/history" || to === "/dashboard") {
      prefetchClassifiedEmails(queryClient);
    } else if (to === "/dashboard/production-model") {
      queryClient.prefetchQuery({
        queryKey: ["production-model"],
        queryFn: () => import("@/services/modelService").then((m) => m.modelService.getProductionModel()),
        staleTime: 1000 * 60 * 5,
      });
    } else if (to === "/dashboard/profile") {
      queryClient.prefetchQuery({
        queryKey: ["user-profile"],
        queryFn: () => import("@/services/profileApi").then((m) => m.profileApi.getProfile()),
        staleTime: 1000 * 60 * 5,
      });
    }
  };

  return (
    <aside className="glass-strong sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-border/60 p-4 transition-colors duration-300">
      <div className="px-2 pb-6 pt-2">
        <Link to="/" onClick={onNavigate}>
          <BrandLogo />
        </Link>
      </div>

      <nav className="flex-1 space-y-1.5">
        {links.map((l) => {
          const active = l.exact
            ? pathname === l.to
            : pathname === l.to || pathname.startsWith(`${l.to}/`);
          return (
            <Link
              key={l.to}
              to={l.to}
              preload="intent"
              onMouseEnter={() => handleLinkPrefetch(l.to)}
              onFocus={() => handleLinkPrefetch(l.to)}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-brand/15 text-brand shadow-soft font-semibold"
                  : "text-muted-foreground hover:bg-accent/40 hover:text-foreground",
              )}
            >
              <l.icon className={cn("h-4 w-4 shrink-0", active ? "text-brand" : "")} />
              {l.label}
            </Link>
          );
        })}
      </nav>

      {/* Sidebar Footer with Theme Toggle & User Logout */}
      <div className="border-t border-border/60 pt-4 space-y-3">
        <div className="flex items-center justify-between px-2 text-xs text-muted-foreground">
          <span className="font-medium">Theme Mode</span>
          <ThemeToggle />
        </div>

        <button
          onClick={async () => {
            await logout();
            navigate({ to: "/login" });
          }}
          className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
        >
          <LogOut className="h-4 w-4" />
          Logout ({user?.name ? user.name.split(" ")[0] : "Account"})
        </button>
      </div>
    </aside>
  );
}
