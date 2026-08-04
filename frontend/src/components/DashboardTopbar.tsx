import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Bell, Menu, Search } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { DashboardSidebar } from "./DashboardSidebar";
import { ThemeToggle } from "./ThemeToggle";
import { useAuth } from "@/context/AuthContext";
import { useGlobalSearch } from "@/hooks/useGlobalSearch";
import { GlobalSearchModal } from "@/components/search/GlobalSearchModal";

export function DashboardTopbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const searchState = useGlobalSearch();

  const initials =
    user?.name
      ?.split(" ")
      .map((s) => s[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "MS";

  return (
    <header className="glass sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border/60 px-4 md:px-6 transition-colors duration-300">
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger asChild>
          <button className="rounded-lg p-2 hover:bg-accent/40 md:hidden" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <DashboardSidebar onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Global Command Palette Trigger — Desktop */}
      <button
        onClick={searchState.openSearch}
        className="relative hidden max-w-md flex-1 md:flex items-center h-9 w-full rounded-xl border border-border/60 bg-background/50 px-3 py-1.5 text-xs text-muted-foreground transition-all hover:bg-accent/40 hover:border-brand/40 focus-visible:outline-none"
        aria-label="Global Command Palette Search"
      >
        <Search className="mr-2.5 h-4 w-4 text-muted-foreground shrink-0" />
        <span className="flex-1 text-left font-medium">Search emails, commands, settings...</span>
        <kbd className="inline-flex items-center gap-0.5 rounded-lg border border-border/60 bg-muted/60 px-2 py-0.5 text-[10px] font-semibold text-muted-foreground">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      {/* Mobile Search Button */}
      <button
        onClick={searchState.openSearch}
        className="rounded-lg p-2 text-muted-foreground hover:bg-accent/40 hover:text-foreground md:hidden"
        aria-label="Open Global Search"
      >
        <Search className="h-5 w-5" />
      </button>

      <div className="flex-1 md:hidden" />

      <ThemeToggle />

      <button className="relative rounded-lg p-2 text-muted-foreground hover:bg-accent/40 hover:text-foreground transition-colors">
        <Bell className="h-4 w-4" />
        <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-brand" />
      </button>

      <DropdownMenu>
        <DropdownMenuTrigger className="focus-visible:outline-none">
          <Avatar className="h-8 w-8 border border-border/60 hover:ring-2 hover:ring-brand/40 transition-all">
            <AvatarImage src={user?.avatarUrl} />
            <AvatarFallback className="bg-brand/20 text-xs font-semibold text-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="text-xs">
            <div className="font-medium">{user?.name ?? "Guest"}</div>
            <div className="text-muted-foreground">{user?.email ?? "Not signed in"}</div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
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
            className="text-destructive"
          >
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Global Command Palette Search Modal */}
      <GlobalSearchModal {...searchState} />
    </header>
  );
}
