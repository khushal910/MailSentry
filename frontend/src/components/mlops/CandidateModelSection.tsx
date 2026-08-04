import { Sparkles, Scale, ArrowUpRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface CandidateModelProps {
  candidate?: {
    version: string;
    model_name: string;
    algorithm?: string;
    accuracy_improvement: string;
    training_date: string;
    experiment_name: string;
    mlflow_run_id: string;
    dataset_version: string;
  } | null;
  onCompare: (version: string) => void;
  onDeploy: (version: string) => void;
}

export function CandidateModelSection({
  candidate,
  onCompare,
  onDeploy,
}: CandidateModelProps) {
  if (!candidate) {
    return (
      <div className="rounded-xl border border-border/80 bg-card p-5 text-sm font-semibold text-muted-foreground flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-2.5">
          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          <span>No candidate model available. Current production model is serving optimal traffic.</span>
        </div>
        <span className="text-xs font-mono text-muted-foreground">Status: Optimal</span>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/5 p-5 space-y-4 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-500/20 pb-3">
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 font-extrabold text-sm px-3 py-1 rounded-md">
            Candidate Available
          </Badge>
          <span className="text-base font-extrabold text-foreground">
            {candidate.model_name} ({candidate.version})
          </span>
          <span className="text-sm font-mono font-extrabold text-emerald-500 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/30">
            {candidate.accuracy_improvement} Accuracy
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCompare(candidate.version)}
            className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg border-border/80"
          >
            <Scale className="mr-2 h-4 w-4" />
            Compare Candidate
          </Button>

          <Button
            size="sm"
            onClick={() => onDeploy(candidate.version)}
            className="h-9 px-4 text-xs sm:text-sm font-bold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            Promote & Deploy Candidate
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs sm:text-sm">
        <div>
          <span className="block text-xs text-muted-foreground font-medium">Experiment</span>
          <span className="font-medium text-foreground/80">{candidate.experiment_name}</span>
        </div>
        <div>
          <span className="block text-xs text-muted-foreground font-medium">Dataset Version</span>
          <span className="font-mono font-medium text-foreground/80">{candidate.dataset_version}</span>
        </div>
        <div>
          <span className="block text-xs text-muted-foreground font-medium">MLflow Run ID</span>
          <span className="font-mono text-xs font-medium text-brand/90 truncate block">{candidate.mlflow_run_id}</span>
        </div>
        <div>
          <span className="block text-xs text-muted-foreground font-medium">Trained At</span>
          <span className="font-medium text-foreground/80">{candidate.training_date}</span>
        </div>
      </div>
    </div>
  );
}
