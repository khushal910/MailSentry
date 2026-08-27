import { useState } from "react";
import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { Bell, Menu, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { BrandLogo } from "./BrandLogo";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./ThemeToggle";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "Home" },
  { to: "/features", label: "Features" },
  { to: "/pricing", label: "Pricing" },
  { to: "/about", label: "About" },
  { to: "/contact", label: "Contact" },
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (r) => r.location.pathname });
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const initials =
    user?.name
      ?.split(" ")
      .map((s) => s[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "MS";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/60 backdrop-blur-2xl backdrop-saturate-150 transition-colors duration-300 shadow-soft">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
        <Link to="/" className="flex items-center">
          <BrandLogo />
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {links.map((l) => {
            const active = pathname === l.to;
            return (
              <Link
                key={l.to}
                to={l.to}
                preload="intent"
                className={cn(
                  "rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors relative",
                  active
                    ? "text-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/40",
                )}
              >
                {l.label}
                {active && (
                  <motion.div
                    layoutId="activeNavTab"
                    className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-gradient-brand"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle />

          {isAuthenticated ? (
            <>
              <button
                onClick={() => navigate({ to: "/dashboard" })}
                className="relative rounded-lg p-2 text-muted-foreground hover:bg-accent/40 hover:text-foreground transition-colors"
                aria-label="Notifications"
                title="Notifications"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-brand" />
              </button>

              <DropdownMenu>
                <DropdownMenuTrigger className="focus-visible:outline-none rounded-full">
                  <Avatar className="h-8 w-8 border border-border/60 hover:ring-2 hover:ring-brand/40 transition-all cursor-pointer">
                    <AvatarImage src={user?.avatarUrl} />
                    <AvatarFallback className="bg-brand/20 text-xs font-semibold text-foreground">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="text-xs">
                    <div className="font-medium">{user?.name ?? "Guest"}</div>
                    <div className="text-muted-foreground truncate">{user?.email ?? "Not signed in"}</div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard">Dashboard</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard/profile">Profile</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard/settings">Settings</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={async () => {
                      await logout();
                      navigate({ to: "/login" });
                    }}
                    className="text-destructive cursor-pointer"
                  >
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm" className="hover:bg-accent/50">
                <Link to="/login" preload="intent">Login</Link>
              </Button>
              <Button
                asChild
                size="sm"
                className="bg-gradient-brand shadow-elegant btn-gradient-glow font-semibold"
              >
                <Link to="/signup" preload="intent">Sign up</Link>
              </Button>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          {isAuthenticated && (
            <Avatar className="h-7 w-7 border border-border/60">
              <AvatarImage src={user?.avatarUrl} />
              <AvatarFallback className="bg-brand/20 text-[10px] font-semibold text-foreground">
                {initials}
              </AvatarFallback>
            </Avatar>
          )}
          <button
            onClick={() => setOpen((v) => !v)}
            className="rounded-lg p-2 text-foreground hover:bg-accent/50"
            aria-label="Toggle menu"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-border/60 bg-background/90 backdrop-blur-2xl md:hidden"
          >
            <div className="mx-auto max-w-7xl space-y-1 px-4 py-3">
              {links.map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  onClick={() => setOpen(false)}
                  className="block rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                >
                  {l.label}
                </Link>
              ))}
              <div className="mt-2 flex flex-col gap-2 border-t border-border/60 pt-3">
                {isAuthenticated ? (
                  <>
                    <div className="flex items-center gap-3 px-2 py-2">
                      <Avatar className="h-8 w-8 border border-border/60">
                        <AvatarImage src={user?.avatarUrl} />
                        <AvatarFallback className="bg-brand/20 text-xs font-semibold text-foreground">
                          {initials}
                        </AvatarFallback>
                      </Avatar>
                      <div className="text-xs">
                        <div className="font-medium text-foreground">{user?.name ?? "User"}</div>
                        <div className="text-muted-foreground truncate max-w-[200px]">{user?.email ?? ""}</div>
                      </div>
                    </div>
                    <Button asChild size="sm" className="w-full bg-gradient-brand btn-gradient-glow">
                      <Link to="/dashboard" onClick={() => setOpen(false)}>
                        Dashboard
                      </Link>
                    </Button>
                    <div className="grid grid-cols-2 gap-2">
                      <Button asChild variant="outline" size="sm">
                        <Link to="/dashboard/profile" onClick={() => setOpen(false)}>
                          Profile
                        </Link>
                      </Button>
                      <Button asChild variant="outline" size="sm">
                        <Link to="/dashboard/settings" onClick={() => setOpen(false)}>
                          Settings
                        </Link>
                      </Button>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:bg-destructive/10 justify-start px-2"
                      onClick={async () => {
                        setOpen(false);
                        await logout();
                        navigate({ to: "/login" });
                      }}
                    >
                      Log out
                    </Button>
                  </>
                ) : (
                  <div className="flex gap-2">
                    <Button asChild variant="outline" size="sm" className="flex-1">
                      <Link to="/login" onClick={() => setOpen(false)}>
                        Login
                      </Link>
                    </Button>
                    <Button
                      asChild
                      size="sm"
                      className="flex-1 bg-gradient-brand btn-gradient-glow"
                    >
                      <Link to="/signup" onClick={() => setOpen(false)}>
                        Sign up
                      </Link>
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
