import { useEffect, useState, useCallback } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ShieldCheck,
  ShieldAlert,
  Inbox,
  Target,
  Wand2,
  History as HistoryIcon,
  ArrowRight,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { StatsCard } from "@/components/StatsCard";
import { PredictionBadge } from "@/components/PredictionBadge";
import { Button } from "@/components/ui/button";
import { formatConfidence, formatDate, formatNumber, truncate } from "@/utils/format";
import { PageTransition } from "@/components/PageTransition";
import { useAuth } from "@/context/AuthContext";
import { GmailStatusCard } from "@/components/GmailStatusCard";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { emailsApi, type ClassifiedEmail } from "@/services/emailsApi";

export const Route = createFileRoute("/dashboard/")({
  head: () => ({
    meta: [
      { title: "Dashboard — MailSentry" },
      { name: "description", content: "Overview of your inbox protection." },
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
  const { stats, isLoading, isError, error, refetch } = useDashboardStats();

  const [recentEmails, setRecentEmails] = useState<ClassifiedEmail[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);

  const fetchRecent = useCallback(async () => {
    setLoadingRecent(true);
    try {
      const res = await emailsApi.getEmails({ page: 1, limit: 5 });
      setRecentEmails(res.emails || []);
    } catch {
      setRecentEmails([]);
    } finally {
      setLoadingRecent(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (active) void fetchRecent();
    });
    return () => {
      active = false;
    };
  }, [fetchRecent]);

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
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here's a snapshot of your inbox intelligence.
          </p>
        </div>
        <Button asChild className="hidden bg-gradient-brand shadow-elegant sm:inline-flex">
          <Link to="/dashboard/classifier">
            Run classifier <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>

      <div className="mt-6">
        <GmailStatusCard />
      </div>

      {isLoading ? (
        <StatsSkeleton />
      ) : isError ? (
        <div className="mt-6 glass rounded-xl p-5 text-center border-destructive/30">
          <div className="flex items-center justify-center gap-2 text-destructive font-medium">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load dashboard statistics</span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {error || "Could not retrieve data from server."}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-3">
            <RefreshCw className="mr-2 h-3.5 w-3.5" /> Retry
          </Button>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            label="Total predictions"
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

      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        <div className="glass rounded-xl p-5 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">Recent predictions</h2>
            <Link
              to="/dashboard/history"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              View all
            </Link>
          </div>
          <div className="mt-4 overflow-x-auto">
            {loadingRecent ? (
              <div className="py-8 text-center text-xs text-muted-foreground animate-pulse">
                Loading recent predictions…
              </div>
            ) : recentEmails.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                No predictions recorded yet. Run the classifier or sync Gmail to get started!
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-3 text-left font-medium">Date</th>
                    <th className="pb-3 text-left font-medium">Subject</th>
                    <th className="pb-3 text-left font-medium">Prediction</th>
                    <th className="pb-3 text-right font-medium">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {recentEmails.map((r) => (
                    <tr key={r.message_id} className="border-b border-border/40 last:border-0">
                      <td className="py-3 text-muted-foreground">
                        {formatDate(r.classified_at || r.fetch_time || new Date().toISOString())}
                      </td>
                      <td className="py-3">{truncate(r.subject || "(No Subject)", 45)}</td>
                      <td className="py-3">
                        <PredictionBadge
                          prediction={r.predicted_label === "spam" ? "Spam" : "Ham"}
                        />
                      </td>
                      <td className="py-3 text-right font-medium">
                        {r.predicted_score !== undefined && r.predicted_score !== null
                          ? formatConfidence(r.predicted_score)
                          : "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="glass rounded-xl p-5">
          <h2 className="text-base font-semibold">Quick actions</h2>
          <p className="mt-1 text-xs text-muted-foreground">Jump into the tools you use most.</p>
          <div className="mt-4 space-y-2">
            <Button asChild variant="outline" className="w-full justify-start">
              <Link to="/dashboard/classifier">
                <Wand2 className="mr-2 h-4 w-4" /> New prediction
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start">
              <Link to="/dashboard/history">
                <HistoryIcon className="mr-2 h-4 w-4" /> View history
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start">
              <Link to="/dashboard/settings">
                <Target className="mr-2 h-4 w-4" /> Tune thresholds
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
