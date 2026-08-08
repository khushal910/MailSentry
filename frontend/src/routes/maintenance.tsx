import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Wrench,
  Clock,
  RefreshCw,
  Mail,
  ShieldAlert,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { useMaintenance } from "../context/MaintenanceContext";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/maintenance")({
  head: () => ({
    meta: [
      { title: "Scheduled Maintenance — MailSentry" },
      {
        name: "description",
        content: "MailSentry is currently undergoing scheduled maintenance.",
      },
    ],
  }),
  component: MaintenancePage,
});

function formatCountdown(targetDateStr: string | null): string | null {
  if (!targetDateStr) return null;
  const target = new Date(targetDateStr).getTime();
  if (isNaN(target)) return null;

  const now = new Date().getTime();
  const diff = target - now;

  if (diff <= 0) return "Maintenance complete — checking status…";

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);

  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0 || hours > 0) parts.push(`${minutes}m`);
  parts.push(`${seconds}s`);

  return parts.join(" ");
}

function MaintenancePage() {
  const { isMaintenance, maintenanceEnd, checkStatus } = useMaintenance();
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!maintenanceEnd) {
      setCountdown(null);
      return;
    }

    const timer = setInterval(() => {
      setCountdown(formatCountdown(maintenanceEnd));
    }, 1000);

    setCountdown(formatCountdown(maintenanceEnd));

    return () => clearInterval(timer);
  }, [maintenanceEnd]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await checkStatus();
    setTimeout(() => {
      setIsRefreshing(false);
    }, 600);
  };

  useEffect(() => {
    if (!isMaintenance) {
      // If maintenance mode turns off, automatically redirect user home
      navigate({ to: "/", replace: true });
    }
  }, [isMaintenance, navigate]);

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-between bg-gradient-hero px-4 py-8 text-foreground selection:bg-brand selection:text-white">
      {/* Background ambient lighting effects */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-brand/10 blur-[120px] dark:bg-brand/20" />
      <div className="pointer-events-none absolute -bottom-40 right-1/4 -z-10 h-[400px] w-[400px] rounded-full bg-amber-500/10 blur-[100px]" />

      {/* Header with MailSentry Logo */}
      <header className="flex w-full max-w-5xl items-center justify-between py-4">
        <Link to="/" className="flex items-center gap-2.5 transition-transform hover:scale-[1.02]">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-brand shadow-elegant">
            <ShieldAlert className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight gradient-text">
            MailSentry
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400">
            <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping" />
            Under Maintenance
          </span>
        </div>
      </header>

      {/* Main Content Card */}
      <main className="my-auto w-full max-w-2xl text-center">
        <div className="relative overflow-hidden rounded-3xl border border-border/60 bg-card/75 p-8 sm:p-12 shadow-2xl backdrop-blur-xl transition-all">
          {/* Animated Graphic Icon */}
          <div className="mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-amber-500/20 via-brand/20 to-purple-500/20 p-0.5 shadow-inner">
            <div className="flex h-full w-full items-center justify-center rounded-[22px] bg-background/90 shadow-sm">
              <Wrench className="h-10 w-10 text-brand animate-bounce" />
            </div>
          </div>

          {/* Heading */}
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl gradient-text">
            We'll be back soon!
          </h1>

          {/* Subtext */}
          <p className="mx-auto mt-4 max-w-lg text-base text-muted-foreground sm:text-lg">
            We're performing scheduled maintenance to improve your experience and upgrade backend security. Thank you for your patience.
          </p>

          {/* Countdown timer badge if configured */}
          {countdown && (
            <div className="mt-8 inline-flex flex-col items-center justify-center rounded-2xl border border-border/80 bg-accent/40 px-6 py-3 shadow-inner">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Clock className="h-4 w-4 text-brand" />
                <span>Estimated Completion</span>
              </div>
              <p className="mt-1 font-mono text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                {countdown}
              </p>
            </div>
          )}

          {/* Status checklist */}
          <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2 text-left">
            <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-background/60 p-3 shadow-sm">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
              <span className="text-xs font-medium text-muted-foreground">
                Data & Account Security Active
              </span>
            </div>
            <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-background/60 p-3 shadow-sm">
              <Sparkles className="h-5 w-5 shrink-0 text-brand" />
              <span className="text-xs font-medium text-muted-foreground">
                Upgrading Spam Classifier Models
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="bg-gradient-brand shadow-elegant transition-transform hover:scale-[1.02]"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              {isRefreshing ? "Checking Status…" : "Check System Status"}
            </Button>

            <a
              href="mailto:support@mailsentry.app?subject=Maintenance%20Query"
              className="inline-flex items-center justify-center rounded-lg border border-input bg-background/80 px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <Mail className="mr-2 h-4 w-4 text-muted-foreground" />
              Contact Support
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full max-w-5xl py-6 text-center text-xs text-muted-foreground">
        <p>© {new Date().getFullYear()} MailSentry Inc. All systems operational once maintenance concludes.</p>
      </footer>
    </div>
  );
}
