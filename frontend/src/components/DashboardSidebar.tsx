import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Wand2,
  History,
  UserCircle,
  Settings,
  LogOut,
  MailSearch,
} from "lucide-react";
import { BrandLogo } from "./BrandLogo";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";

const links: Array<{
  to: "/dashboard" | "/dashboard/classifier" | "/dashboard/auto-classifier" | "/dashboard/history" | "/dashboard/profile" | "/dashboard/settings";
  label: string;
  icon: typeof LayoutDashboard;
  exact?: boolean;
}> = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/dashboard/classifier", label: "Email Classifier", icon: Wand2 },
  { to: "/dashboard/auto-classifier", label: "Auto Classifier", icon: MailSearch },
  { to: "/dashboard/history", label: "History", icon: History },
  { to: "/dashboard/profile", label: "Profile", icon: UserCircle },
  { to: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function DashboardSidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (r) => r.location.pathname });
  const { logout, user } = useAuth();
  const navigate = useNavigate();

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
              onClick={onNavigate}
              className={cn(
                "relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-brand/15 text-brand shadow-soft font-semibold"
                  : "text-muted-foreground hover:bg-accent/40 hover:text-foreground"
              )}
            >
              {active && (
                <motion.div
                  layoutId="activeSidebarTab"
                  className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-brand"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
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
