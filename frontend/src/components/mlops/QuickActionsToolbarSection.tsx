import {
  Sparkles,
  RotateCcw,
  ExternalLink,
  Download,
  Terminal,
  RefreshCw,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuickActionsProps {
  onDeploy: () => void;
  onRollback: () => void;
  onRefresh: () => void;
}

export function QuickActionsToolbarSection({
  onDeploy,
  onRollback,
  onRefresh,
}: QuickActionsProps) {
  return (
    <div className="rounded-xl border border-border/80 bg-card p-5 shadow-xs space-y-3">
      <span className="block text-xs sm:text-sm font-extrabold text-muted-foreground uppercase tracking-wider">
        Quick Actions
      </span>

      <div className="flex flex-wrap items-center gap-2.5">
        <Button
          size="sm"
          onClick={onDeploy}
          className="h-9 px-4 text-xs sm:text-sm font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          Deploy Candidate
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={onRollback}
          className="h-9 px-4 text-xs sm:text-sm font-bold border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 rounded-lg"
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          Rollback Production
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open("http://localhost:5000", "_blank")}
          className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg"
        >
          <ExternalLink className="mr-2 h-4 w-4" />
          Open MLflow UI
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Restart Service
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => alert("Model checkpoint download started.")}
          className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg"
        >
          <Download className="mr-2 h-4 w-4" />
          Download Checkpoint (.pkl)
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => alert("Fetching live serving logs...")}
          className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg"
        >
          <Terminal className="mr-2 h-4 w-4" />
          View Serving Logs
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => alert("Viewing detailed latency telemetry...")}
          className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg"
        >
          <BarChart3 className="mr-2 h-4 w-4" />
          View Prometheus Metrics
        </Button>
      </div>
    </div>
  );
}
