import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Bell, Menu, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
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
import { useAuth } from "@/context/AuthContext";

export function DashboardTopbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const initials =
    user?.name
      ?.split(" ")
      .map((s) => s[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "MS";

  return (
    <header className="glass sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border/60 px-4 md:px-6">
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger asChild>
          <button className="rounded-md p-2 md:hidden" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <DashboardSidebar onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="relative hidden max-w-md flex-1 md:block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search…"
          className="h-9 pl-9"
          aria-label="Search"
        />
      </div>
      <div className="flex-1 md:hidden" />

      <button className="relative rounded-md p-2 text-muted-foreground hover:text-foreground">
        <Bell className="h-4 w-4" />
        <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-brand" />
      </button>

      <DropdownMenu>
        <DropdownMenuTrigger className="focus-visible:outline-none">
          <Avatar className="h-8 w-8 border border-border/60">
            <AvatarImage src={user?.avatarUrl} />
            <AvatarFallback className="bg-brand/20 text-xs text-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="text-xs">
            <div className="font-medium">{user?.name ?? "Guest"}</div>
            <div className="text-muted-foreground">
              {user?.email ?? "Not signed in"}
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link to="/dashboard/profile">Profile</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link to="/dashboard/settings">Settings</Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={async () => { await logout(); navigate({ to: "/login" }); }} className="text-destructive">
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
