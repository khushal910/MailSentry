import { Link, useLocation } from "@tanstack/react-router";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { useMaintenance } from "../context/MaintenanceContext";

export function MaintenanceBanner() {
  const { isMaintenance } = useMaintenance();
  const location = useLocation();

  // Do not render banner on the dedicated maintenance page itself
  if (!isMaintenance || location.pathname === "/maintenance") {
    return null;
  }

  return (
    <div className="relative z-50 bg-amber-500/90 text-amber-950 dark:bg-amber-600/90 dark:text-amber-50 px-4 py-2.5 shadow-md backdrop-blur-sm transition-all duration-300">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 text-xs font-medium sm:text-sm">
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-950 dark:text-amber-200 animate-pulse" />
          <span>
            <strong className="font-bold">Scheduled Maintenance:</strong> MailSentry is currently undergoing system maintenance.
          </span>
        </div>
        <Link
          to="/maintenance"
          className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-950/10 dark:bg-amber-900/40 px-3 py-1 text-xs font-bold text-amber-950 dark:text-amber-100 transition-all hover:bg-amber-950/20 dark:hover:bg-amber-900/60"
        >
          <span>View Details</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
