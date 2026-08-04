import {
  Download,
  ExternalLink,
  RefreshCw,
  Terminal,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { downloadPklFile } from "@/utils/downloadHelper";
import { toast } from "sonner";

interface QuickActionsProps {
  onRefresh: () => void;
}

export function QuickActionsToolbarSection({
  onRefresh,
}: QuickActionsProps) {
  return (
    <div className="rounded-xl border border-border/80 bg-card p-5 shadow-xs space-y-3">
      <span className="block text-xs sm:text-sm font-extrabold text-muted-foreground uppercase tracking-wider">
        Artifact Downloads & System Actions
      </span>

      <div className="flex flex-wrap items-center gap-2.5">
        <Button
          size="sm"
          onClick={() => {
            downloadPklFile("model.pkl", "MailSentry Production Classifier Model", 0.05);
            toast.success("Downloading Model (.pkl) artifact (0.05 MB)...");
          }}
          className="h-9 px-4 text-xs sm:text-sm font-bold bg-brand text-brand-foreground hover:bg-brand/90 rounded-lg"
        >
          <Download className="mr-2 h-4 w-4" />
          Model File (.pkl) (0.05 MB)
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            downloadPklFile("preprocessing.pkl", "TF-IDF & Text Preprocessing Pipeline", 0.02);
            toast.success("Downloading Preprocessing (.pkl) artifact (0.02 MB)...");
          }}
          className="h-9 px-4 text-xs sm:text-sm font-bold border-emerald-500/40 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 rounded-lg"
        >
          <Download className="mr-2 h-4 w-4" />
          Preprocessing File (.pkl) (0.02 MB)
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            downloadPklFile("embedding.pkl", "Label Encoder & Embedding Dictionary", 0.01);
            toast.success("Downloading Label Encoder & Embedding (.pkl) artifact (0.01 MB)...");
          }}
          className="h-9 px-4 text-xs sm:text-sm font-bold border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 rounded-lg"
        >
          <Download className="mr-2 h-4 w-4" />
          Embedding / Label Encoder (.pkl) (0.01 MB)
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
          Refresh Telemetry
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
