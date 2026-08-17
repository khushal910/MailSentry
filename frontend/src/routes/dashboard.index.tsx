import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ShieldCheck,
  ShieldAlert,
  Inbox,
  Target,
  Wand2,
  Mail as MailIcon,
  ArrowRight,
  AlertCircle,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { StatsCard } from "@/components/StatsCard";
import { ClassifiedEmailsTable } from "@/components/ClassifiedEmailsTable";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/utils/format";
import { PageTransition } from "@/components/PageTransition";
import { useAuth } from "@/context/AuthContext";
import { GmailStatusCard } from "@/components/GmailStatusCard";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { usePredictiveHistory, prefetchClassifiedEmails } from "@/hooks/usePredictiveHistory";
import { useQueryClient } from "@tanstack/react-query";

export const Route = createFileRoute("/dashboard/")({
  head: () => ({
    meta: [
      { title: "Dashboard — MailSentry" },
      { name: "description", content: "Overview of your inbox protection and classified emails." },
    ],
  }),
  component: DashboardHome,
});

function StatsSkeleton() {
  return (
    <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="glass rounded-xl p-5 shadow-soft animate-pulse flex items-start justify-between gap-3 h-[104px]"
        >
          <div className="space-y-2 flex-1">
            <div className="h-3 w-24 bg-muted/60 rounded" />
            <div className="h-7 w-16 bg-muted/80 rounded" />
            <div className="h-3 w-28 bg-muted/40 rounded" />
          </div>
          <div className="h-9 w-9 bg-muted/60 rounded-lg" />
        </div>
      ))}
    </div>
  );
}

function DashboardHome() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { stats, isLoading: statsLoading, isError: statsError, error: statsErrorMessage, refetch: refetchStats } = useDashboardStats();

  // Shared TanStack Query for recent emails (5-8 latest items)
  const {
    emails: recentEmails,
    isLoading: emailsLoading,
    totalCount,
    refetch: refetchEmails,
  } = usePredictiveHistory({
    page: 1,
    limit: 8,
  });

  // Helper for Total Predictions Trend
  const getTotalTrend = () => {
    if (!stats || stats.total_predictions === 0) return "No predictions yet";
    if (stats.last_week_predictions === 0) return "New";
    if (stats.growth_percentage === null || stats.growth_percentage === undefined) return "New";
    if (stats.growth_percentage > 0) return `+${stats.growth_percentage.toFixed(1)}% vs last week`;
    if (stats.growth_percentage < 0) return `${stats.growth_percentage.toFixed(1)}% vs last week`;
    return "0.0% vs last week";
  };

  return (
    <PageTransition>
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here's a snapshot of your inbox intelligence and classified emails.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            asChild
            variant="outline"
            size="sm"
            className="shadow-xs"
            onMouseEnter={() => prefetchClassifiedEmails(queryClient)}
            onFocus={() => prefetchClassifiedEmails(queryClient)}
          >
            <Link to="/dashboard/history" preload="intent">
              <MailIcon className="mr-1.5 h-4 w-4" /> Classified Emails ({totalCount})
            </Link>
          </Button>
          <Button asChild size="sm" className="bg-gradient-brand shadow-elegant">
            <Link to="/dashboard/classifier">
              Run classifier <ArrowRight className="ml-1.5 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      {/* Gmail Connection Status Card */}
      <div className="mt-6">
        <GmailStatusCard />
      </div>

      {/* Summary Statistics */}
      {statsLoading ? (
        <StatsSkeleton />
      ) : statsError ? (
        <div className="mt-6 glass rounded-xl p-5 text-center border-destructive/30">
          <div className="flex items-center justify-center gap-2 text-destructive font-medium">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load dashboard statistics</span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {statsErrorMessage || "Could not retrieve data from server."}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetchStats()} className="mt-3">
            <RefreshCw className="mr-2 h-3.5 w-3.5" /> Retry
          </Button>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            label="Total emails"
            value={formatNumber(stats?.total_predictions)}
            icon={Inbox}
            trend={getTotalTrend()}
            accent="brand"
          />
          <StatsCard
            label="Spam emails"
            value={formatNumber(stats?.spam_emails)}
            icon={ShieldAlert}
            trend={
              !stats || stats.total_predictions === 0
                ? "No predictions yet"
                : `${(stats.spam_percentage ?? 0).toFixed(1)}% of all`
            }
            accent="destructive"
          />
          <StatsCard
            label="Safe emails"
            value={formatNumber(stats?.safe_emails)}
            icon={ShieldCheck}
            trend={
              !stats || stats.total_predictions === 0
                ? "No predictions yet"
                : `${(stats.safe_percentage ?? 0).toFixed(1)}% of all`
            }
            accent="success"
          />
          <StatsCard
            label="Average Confidence"
            value={
              !stats || stats.total_predictions === 0
                ? "0.0%"
                : `${(stats.average_confidence ?? 0).toFixed(1)}%`
            }
            icon={Target}
            trend={
              !stats || stats.total_predictions === 0
                ? "No predictions yet"
                : "Average model confidence"
            }
            accent="cyan"
          />
        </div>
      )}

      {/* Main Content Grid: Recent Emails + Quick Actions */}
      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        {/* Recent Emails (2 Columns on large screens) */}
        <div className="glass rounded-2xl p-5 md:p-6 lg:col-span-2 border border-border/60 shadow-lg space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-3">
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h2 className="text-lg font-semibold tracking-tight text-foreground">
                  Recent Emails
                </h2>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-brand/20 via-purple-500/15 to-primary/20 px-3 py-1 text-xs font-semibold text-primary border border-primary/30 shadow-xs backdrop-blur-xs transition-all hover:border-primary/60 hover:shadow-soft">
                  <Sparkles className="h-3.5 w-3.5 text-brand animate-pulse" />
                  <span>Click any row for <strong className="text-foreground font-bold">AI Summary & Details</strong></span>
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Latest classified messages with real-time threat intelligence.
              </p>
            </div>
            <Link
              to="/dashboard/history"
              className="text-xs font-semibold text-primary hover:underline whitespace-nowrap"
            >
              View classified emails ({totalCount}) →
            </Link>
          </div>

          <ClassifiedEmailsTable
            emails={recentEmails}
            isLoading={emailsLoading}
            isCompact={true}
            emptyMessage="No emails classified yet"
            emptySubtitle="Run the classifier or fetch emails from Gmail to start seeing classified emails."
          />
        </div>

        {/* Quick Actions (1 Column on large screens) */}
        <div className="space-y-6">
          <div className="glass rounded-2xl p-5 md:p-6 border border-border/60 shadow-lg space-y-4">
            <div>
              <h2 className="text-base font-semibold text-foreground">Quick actions</h2>
              <p className="mt-1 text-xs text-muted-foreground">Jump into the tools you use most.</p>
            </div>
            <div className="space-y-2.5">
              <Button asChild variant="outline" className="w-full justify-start text-sm">
                <Link to="/dashboard/auto-classifier">
                  <Inbox className="mr-2.5 h-4 w-4 text-primary" /> New Emails Queue
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full justify-start text-sm">
                <Link to="/dashboard/history">
                  <MailIcon className="mr-2.5 h-4 w-4 text-primary" /> View Classified Emails
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full justify-start text-sm">
                <Link to="/dashboard/classifier">
                  <Wand2 className="mr-2.5 h-4 w-4 text-primary" /> Manual Classifier
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full justify-start text-sm">
                <Link to="/dashboard/settings">
                  <Target className="mr-2.5 h-4 w-4 text-primary" /> Tune Thresholds & Settings
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}

