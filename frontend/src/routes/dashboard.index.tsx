import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ShieldCheck,
  ShieldAlert,
  Inbox,
  Target,
  Wand2,
  History as HistoryIcon,
  ArrowRight,
} from "lucide-react";
import { StatsCard } from "@/components/StatsCard";
import { PredictionBadge } from "@/components/PredictionBadge";
import { Button } from "@/components/ui/button";
import { formatConfidence, formatDate, truncate } from "@/utils/format";
import { PageTransition } from "@/components/PageTransition";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/dashboard/")({
  head: () => ({
    meta: [
      { title: "Dashboard — MailSentry" },
      { name: "description", content: "Overview of your inbox protection." },
    ],
  }),
  component: DashboardHome,
});

const recent = [
  {
    id: "1",
    date: new Date(Date.now() - 3600e3).toISOString(),
    subject: "Reset your Netflix password immediately",
    prediction: "Spam" as const,
    confidence: 98.34,
  },
  {
    id: "2",
    date: new Date(Date.now() - 7200e3).toISOString(),
    subject: "Q3 board deck — draft for review",
    prediction: "Ham" as const,
    confidence: 96.1,
  },
  {
    id: "3",
    date: new Date(Date.now() - 86400e3).toISOString(),
    subject: "You WON a $500 Amazon gift card!!!",
    prediction: "Spam" as const,
    confidence: 99.7,
  },
  {
    id: "4",
    date: new Date(Date.now() - 172800e3).toISOString(),
    subject: "Design review notes — Wed 3pm",
    prediction: "Ham" as const,
    confidence: 92.4,
  },
];

function DashboardHome() {
  const { user } = useAuth();
  return (
    <PageTransition>
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome{user?.name ? `, ${user.name.split(" ")[0]}` : ""} 👋
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

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard label="Total predictions" value="1,284" icon={Inbox} trend="+12.4% vs last week" accent="brand" />
        <StatsCard label="Spam emails" value="317" icon={ShieldAlert} trend="24.7% of all" accent="destructive" />
        <StatsCard label="Safe emails" value="967" icon={ShieldCheck} trend="75.3% of all" accent="success" />
        <StatsCard label="Accuracy" value="98.4%" icon={Target} trend="↑ 0.2% this week" accent="cyan" />
      </div>

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
                {recent.map((r) => (
                  <tr key={r.id} className="border-b border-border/40 last:border-0">
                    <td className="py-3 text-muted-foreground">{formatDate(r.date)}</td>
                    <td className="py-3">{truncate(r.subject, 45)}</td>
                    <td className="py-3">
                      <PredictionBadge prediction={r.prediction} />
                    </td>
                    <td className="py-3 text-right font-medium">
                      {formatConfidence(r.confidence)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass rounded-xl p-5">
          <h2 className="text-base font-semibold">Quick actions</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Jump into the tools you use most.
          </p>
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
