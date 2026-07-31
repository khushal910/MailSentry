import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Wand2,
  History,
  UserCircle,
  Settings,
  LogOut,
} from "lucide-react";
import { BrandLogo } from "./BrandLogo";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";

const links: Array<{
  to: "/dashboard" | "/dashboard/classifier" | "/dashboard/history" | "/dashboard/profile" | "/dashboard/settings";
  label: string;
  icon: typeof LayoutDashboard;
  exact?: boolean;
}> = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/dashboard/classifier", label: "Email Classifier", icon: Wand2 },
  { to: "/dashboard/history", label: "History", icon: History },
  { to: "/dashboard/profile", label: "Profile", icon: UserCircle },
  { to: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function DashboardSidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (r) => r.location.pathname });
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <aside className="glass-strong sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-border/60 p-4">
      <div className="px-2 pb-6 pt-2">
        <Link to="/" onClick={onNavigate}>
          <BrandLogo />
        </Link>
      </div>
      <nav className="flex-1 space-y-1">
        {links.map((l) => {
          const active = l.exact
            ? pathname === l.to
            : pathname === l.to || pathname.startsWith(`${l.to}/`);
          return (
            <Link
              key={l.to}
              to={l.to}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-brand/15 text-foreground shadow-soft"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
              )}
            >
              <l.icon className="h-4 w-4" />
              {l.label}
            </Link>
          );
        })}
      </nav>
      <button
        onClick={() => {
          logout();
          navigate({ to: "/login" });
        }}
        className="mt-6 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
      >
        <LogOut className="h-4 w-4" />
        Logout
      </button>
    </aside>
  );
}
