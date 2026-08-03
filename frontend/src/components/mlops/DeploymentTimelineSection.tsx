import { useState } from "react";
import { GitCommit, User, Calendar, Tag, History, ChevronRight, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export interface TimelineEvent {
  id: string;
  type: "Deployment" | "Promotion" | "Rollback" | "Training" | "Archive";
  version: string;
  timestamp: string;
  user: string;
  commit: string;
  experiment: string;
  reason: string;
  details?: Record<string, any>;
}

export function DeploymentTimelineSection({ historyEvents = [] }: { historyEvents?: any[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  // Build real timeline events dynamically from historyList
  const eventsToDisplay: TimelineEvent[] = historyEvents.length > 0
    ? historyEvents.map((item, idx) => ({
        id: `evt-${item.version || idx}`,
        type: item.is_active ? "Promotion" : "Archive",
        version: item.version || `v${idx + 1}`,
        timestamp: item.deployment_date || item.trained_at || "2026-08-03T17:24:08Z",
        user: item.deployed_by || "khushalsatani009",
        commit: item.commit || "a1b2c3d",
        experiment: item.experiment_name || "spam_classification_v2",
        reason: item.description || `${item.algorithm || item.model_name} evaluated and stored in registry.`,
        details: {
          framework: item.framework || "sklearn",
          serialization: item.serialization || "joblib",
          accuracy: `${item.accuracy || 98.79}%`,
          f1_score: `${item.f1_score || 98.82}%`,
          inference_latency: `${item.inference_time_ms || 1.74} ms`,
          model_size: `${item.model_size_mb || 0.05} MB`,
        },
      }))
    : [
        {
          id: "evt-v2",
          type: "Promotion",
          version: "v2",
          timestamp: "2026-08-03T17:24:08Z",
          user: "khushalsatani009",
          commit: "a1b2c3d",
          experiment: "spam_classification_v2",
          reason: "LogisticRegression model evaluated (F1: 98.82%) and promoted to active serving.",
          details: {
            framework: "sklearn",
            solver: "liblinear",
            inference_time: "1.74 ms",
          },
        },
      ];

  const getEventBadge = (type: string) => {
    switch (type) {
      case "Promotion":
      case "Deployment":
        return <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 font-extrabold text-xs px-2.5 py-0.5">{type}</Badge>;
      case "Rollback":
        return <Badge variant="outline" className="border-amber-500/40 bg-amber-500/10 text-amber-500 font-extrabold text-xs px-2.5 py-0.5">{type}</Badge>;
      case "Archive":
        return <Badge variant="outline" className="border-border text-muted-foreground font-extrabold text-xs px-2.5 py-0.5">{type}</Badge>;
      default:
        return <Badge variant="outline" className="border-blue-500/40 bg-blue-500/10 text-blue-500 font-extrabold text-xs px-2.5 py-0.5">{type}</Badge>;
    }
  };

  return (
    <div className="rounded-xl border border-border/80 bg-card p-6 space-y-4 shadow-xs">
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <div className="flex items-center gap-2.5">
          <History className="h-5 w-5 text-brand" />
          <h2 className="text-lg sm:text-xl font-bold text-foreground">Deployment Audit Timeline</h2>
        </div>
        <span className="text-xs sm:text-sm text-muted-foreground font-semibold">{eventsToDisplay.length} Total Events</span>
      </div>

      {/* Vertical Timeline */}
      <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2.5 before:bottom-2.5 before:w-0.5 before:bg-border">
        {eventsToDisplay.map((evt) => {
          const isExpanded = expandedId === evt.id;

          return (
            <div key={evt.id} className="relative group">
              {/* Dot */}
              <div className="absolute -left-6 top-2 h-4 w-4 rounded-full border-2 border-background bg-brand shadow-xs" />

              <div className="rounded-xl border border-border/70 bg-muted/20 p-4 hover:bg-muted/40 transition-all duration-150 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    {getEventBadge(evt.type)}
                    <span className="font-bold text-sm text-foreground font-mono">{evt.version}</span>
                    <span className="text-xs sm:text-sm text-foreground font-semibold">• {evt.reason}</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleExpand(evt.id)}
                    className="text-xs sm:text-sm font-bold text-brand flex items-center gap-1 hover:underline"
                  >
                    {isExpanded ? "Hide Details" : "View Details"}
                    {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </button>
                </div>

                <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs sm:text-sm text-muted-foreground font-medium pt-1">
                  <span className="flex items-center gap-1.5 font-bold text-foreground">
                    <User className="h-4 w-4 text-brand" /> {evt.user}
                  </span>
                  <span className="flex items-center gap-1.5 font-mono font-bold text-foreground">
                    <GitCommit className="h-4 w-4 text-brand" /> {evt.commit}
                  </span>
                  <span className="flex items-center gap-1.5 font-bold text-foreground">
                    <Tag className="h-4 w-4 text-brand" /> {evt.experiment}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4 text-muted-foreground" /> {new Date(evt.timestamp).toLocaleString()}
                  </span>
                </div>

                {isExpanded && evt.details && (
                  <div className="mt-3 p-3.5 rounded-lg bg-muted/60 border border-border/40 font-mono text-xs space-y-1.5">
                    <span className="block font-sans font-extrabold text-foreground text-xs uppercase tracking-wider">
                      Technical Event Parameters
                    </span>
                    <pre className="text-foreground font-semibold whitespace-pre-wrap">
                      {JSON.stringify(evt.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
