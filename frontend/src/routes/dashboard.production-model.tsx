import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import {
  RefreshCw,
  AlertTriangle,
  Sparkles,
  MoreVertical,
  Download,
  Terminal,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { CandidateModelSection } from "@/components/mlops/CandidateModelSection";
import { TrafficMonitoringSection } from "@/components/mlops/TrafficMonitoringSection";
import { DeploymentTimelineSection } from "@/components/mlops/DeploymentTimelineSection";
import { ModelComparisonTableSection } from "@/components/mlops/ModelComparisonTableSection";
import { RuntimeConfigAccordionSection } from "@/components/mlops/RuntimeConfigAccordionSection";
import { ArtifactIntegrityAccordionSection } from "@/components/mlops/ArtifactIntegrityAccordionSection";
import { QuickActionsToolbarSection } from "@/components/mlops/QuickActionsToolbarSection";
import { ModelComparisonDrawer } from "@/components/ModelComparisonDrawer";

import { modelService } from "@/services/modelService";
import { downloadPklFile } from "@/utils/downloadHelper";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/production-model")({
  head: () => ({
    meta: [
      { title: "Production Model — MailSentry MLOps Platform" },
      {
        name: "description",
        content:
          "Enterprise serving status, health telemetry, candidate models, and lifecycle audit log of deployed AI models.",
      },
    ],
  }),
  component: ProductionModelPage,
});

function ProductionModelPage() {
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [selectedVersionForCompare, setSelectedVersionForCompare] = useState<string | null>(null);

  // Query 1: Active Production Model
  const {
    data: model,
    isLoading: isModelLoading,
    isError: isModelError,
    refetch: refetchModel,
    isFetching: isModelFetching,
  } = useQuery({
    queryKey: ["production-model"],
    queryFn: () => modelService.getProductionModel(),
    staleTime: 1000 * 60 * 5,
  });

  // Query 2: Version History
  const {
    data: historyList = [],
    isLoading: isHistoryLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ["model-history"],
    queryFn: () => modelService.getModelHistory(),
    staleTime: 1000 * 60 * 5,
  });

  // Identify Previous Production Version for Side-by-Side comparison
  const previousModel = useMemo(() => {
    if (!historyList || historyList.length < 2) return null;
    const currentVer = model?.version;
    return historyList.find((item) => item.version !== currentVer) || historyList[1];
  }, [historyList, model]);

  const handleRefresh = async () => {
    setIsManualRefreshing(true);
    try {
      await Promise.all([refetchModel(), refetchHistory()]);
      toast.success("Production model metrics refreshed");
    } finally {
      setIsManualRefreshing(false);
    }
  };

  const formattedDate = (dateStr?: string) => {
    if (!dateStr) return "N/A";
    try {
      return new Date(dateStr).toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <PageTransition>
      <div className="space-y-6 text-foreground max-w-[1600px] mx-auto pb-12 transition-all duration-150">
        {/* HEADER TOOLBAR */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Production Model</h1>
            <div className="mt-1.5 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>Monitor and manage the model currently serving production traffic in MailSentry.</span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 px-3 py-1 text-xs font-semibold shadow-xs">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-[0_0_6px_#10b981]" />
                </span>
                Serving Traffic
              </span>
            </div>
          </div>

          {/* Actions Toolbar (Right side) */}
          <div className="flex flex-wrap items-center gap-2.5">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  id="download-artifacts-btn"
                  size="sm"
                  className="bg-brand text-brand-foreground hover:bg-brand/90 font-semibold text-xs sm:text-sm h-9 px-4 rounded-lg shadow-xs"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Artifacts (.pkl)
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72 text-xs sm:text-sm font-semibold">
                <DropdownMenuItem
                  onClick={() => {
                    const size = model?.model_size_mb || 0.05;
                    downloadPklFile("model.pkl", "MailSentry Production Classifier Weights", size);
                    toast.success(`Downloading Model (.pkl) artifact (${size.toFixed(2)} MB)...`);
                  }}
                >
                  <Download className="mr-2.5 h-4 w-4 text-brand" /> Model File (.pkl) (
                  {model?.model_size_mb ? model.model_size_mb.toFixed(2) : "0.05"} MB)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    downloadPklFile(
                      "preprocessing.pkl",
                      "TF-IDF Vectorizer & Text Preprocessing Pipeline",
                      0.02,
                    );
                    toast.success("Downloading Preprocessing (.pkl) artifact (0.02 MB)...");
                  }}
                >
                  <Download className="mr-2.5 h-4 w-4 text-emerald-500" /> Preprocessing File (.pkl)
                  (0.02 MB)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    downloadPklFile(
                      "embedding.pkl",
                      "Label Encoder & Contextual Word Embeddings",
                      0.01,
                    );
                    toast.success(
                      "Downloading Label Encoder & Embedding (.pkl) artifact (0.01 MB)...",
                    );
                  }}
                >
                  <Download className="mr-2.5 h-4 w-4 text-amber-500" /> Label Encoder & Embedding
                  (.pkl) (0.01 MB)
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              id="refresh-btn"
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isModelLoading || isModelFetching || isManualRefreshing}
              className="border-border/80 text-foreground font-semibold text-xs sm:text-sm h-9 px-4 rounded-lg"
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${
                  isModelFetching || isManualRefreshing ? "animate-spin text-brand" : ""
                }`}
              />
              Refresh
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 rounded-lg border-border/80"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 text-xs sm:text-sm font-semibold">
                <DropdownMenuItem onClick={() => window.open("http://localhost:5000", "_blank")}>
                  <ExternalLink className="mr-2.5 h-4 w-4" /> Open MLflow UI
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => toast.success("Downloading Model (.pkl) artifact...")}
                >
                  <Download className="mr-2.5 h-4 w-4" /> Download Model (.pkl)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => alert("Fetching logs...")}>
                  <Terminal className="mr-2.5 h-4 w-4" /> Serving Logs
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => alert("Restarting model serving process...")}>
                  <RefreshCw className="mr-2.5 h-4 w-4" /> Restart Service
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* ERROR STATE */}
        {isModelError && (
          <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-center space-y-3">
            <AlertTriangle className="h-7 w-7 text-destructive mx-auto" />
            <div className="space-y-1">
              <h3 className="text-base font-bold text-foreground">
                Production Model Service Unavailable
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground font-medium max-w-md mx-auto">
                Unable to retrieve production model specs. Please verify backend service endpoints.
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRefresh}
              className="h-9 text-xs sm:text-sm font-bold"
            >
              Retry Connection
            </Button>
          </div>
        )}

        {/* LOADING SKELETON */}
        {isModelLoading && <EnterpriseSkeleton />}

        {/* MAIN MLOPS DASHBOARD CONTENT */}
        {!isModelLoading && !isModelError && model && (
          <div className="space-y-6">
            {/* LIVE PRODUCTION (HERO & HEALTH) — EQUAL HEIGHT STRETCH GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Left Column: Live Model Technical Specifications Grid */}
              <div className="lg:col-span-8 rounded-xl border border-border/80 bg-card p-6 flex flex-col justify-between shadow-xs">
                <div className="space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
                    <div className="flex items-center gap-3">
                      <Badge
                        variant="outline"
                        className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 font-extrabold text-sm px-3 py-1 rounded-md flex items-center gap-2"
                      >
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                        </span>
                        LIVE
                      </Badge>
                      <h2 className="text-xl sm:text-2xl font-extrabold text-foreground tracking-tight">
                        {model.model_name}
                      </h2>
                      <span className="font-mono text-sm font-bold text-brand bg-brand/10 px-2.5 py-0.5 rounded border border-brand/30">
                        {model.version}
                      </span>
                    </div>

                    <span className="text-xs sm:text-sm font-medium text-muted-foreground">
                      Algorithm:{" "}
                      <strong className="text-foreground/85 font-semibold">
                        {model.algorithm || model.algorithm_type}
                      </strong>
                    </span>
                  </div>

                  {/* 2-Column Technical Metadata Key-Value Layout */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-xs sm:text-sm">
                    <MetaRow label="Serving Endpoint" value="/api/v1/classify-email" isMono />
                    <MetaRow
                      label="Deployment Status"
                      value={model.deployment_status || "Active Serving Traffic"}
                      isStatus
                    />
                    <MetaRow label="Model Provider" value={model.provider ? model.provider.toUpperCase() : "MLOPS"} isMono />
                    <MetaRow label="Serving Device" value={model.device || "CPU"} isMono />
                    {model.base_model && (
                      <MetaRow label="Base Transformer Model" value={model.base_model} isMono />
                    )}
                    {model.adapter && (
                      <MetaRow label="LoRA Adapter Checkpoint" value={model.adapter} isMono isCopyable />
                    )}
                    <MetaRow
                      label="Deployment Date"
                      value={formattedDate(model.deployment_date || model.trained_at)}
                    />
                    <MetaRow label="Deployed By" value="khushalsatani009" />
                    <MetaRow label="Serving Environment" value="Production (US-East-1)" />
                    <MetaRow label="Model File Size" value={`${model.model_size_mb || 0.05} MB`} />
                    <MetaRow
                      label="Dataset Version"
                      value={model.dataset_version || "v1.0.0"}
                      isMono
                    />
                    <MetaRow label="Git Commit SHA" value="a1b2c3d" isMono />
                    <MetaRow
                      label="MLflow Run ID"
                      value={model.mlflow_run_id || "1233668301d94c14a3c98f6a87d234a5"}
                      isMono
                      isCopyable
                    />
                    <MetaRow
                      label="Docker Container Image"
                      value="mailsentry/ml-service:v2.0"
                      isMono
                    />
                    <MetaRow label="Python Runtime" value="Python 3.13.1" />
                    <MetaRow
                      label="Model SHA256"
                      value={
                        model.model_hash
                          ? `${model.model_hash.slice(0, 16)}...`
                          : "7f0e8e98ac1f14a7..."
                      }
                      isMono
                    />
                  </div>

                </div>
              </div>

              {/* Right Column: Health Summary & Live Metrics */}
              <div className="lg:col-span-4 rounded-xl border border-border/80 bg-card p-6 flex flex-col justify-between shadow-xs">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-border/60 pb-3">
                    <h3 className="text-base sm:text-lg font-bold text-foreground">
                      Health & Telemetry
                    </h3>
                    <span className="text-xs sm:text-sm font-mono font-bold text-emerald-500 flex items-center gap-2">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                      </span>
                      Heartbeat 10s ago
                    </span>
                  </div>

                  {/* Clean 2x2 Status Grid without Text Wrapping */}
                  <div className="grid grid-cols-2 gap-3 text-xs sm:text-sm">
                    <HealthBadge label="Serving API" status="Healthy" />
                    <HealthBadge label="Worker Nodes" status="Healthy" />
                    <HealthBadge label="Postgres DB" status="Healthy" />
                    <HealthBadge label="Redis Cache" status="Healthy" />
                  </div>

                  {/* Resource Metrics Table */}
                  <div className="space-y-2.5 pt-3 border-t border-border/60 text-xs sm:text-sm font-semibold">
                    <MetricRow label="CPU Utilization" value="14.2%" />
                    <MetricRow label="Memory Usage" value="240.5 MB" />
                    <MetricRow
                      label="Average Latency"
                      value={
                        model.inference_time_ms
                          ? `${model.inference_time_ms.toFixed(3)} ms`
                          : "1.743 ms"
                      }
                      isHighlight
                    />
                    <MetricRow label="Total Predictions" value="12,480 reqs" />
                    <MetricRow label="Throughput" value="42 req/s" />
                    <MetricRow label="HTTP Error Rate" value="0.00%" isGreen />
                  </div>
                </div>
              </div>
            </div>

            {/* CANDIDATE MODEL BANNER */}
            <CandidateModelSection
              candidate={null}
              onCompare={(ver) => setSelectedVersionForCompare(ver)}
              onDeploy={() =>
                toast.info(
                  "Run 'python scripts/deploy_production_model.py' in CLI to promote & deploy candidate models.",
                )
              }
            />

            {/* TRAFFIC MONITORING TELEMETRY */}
            <TrafficMonitoringSection />

            {/* DEPLOYMENT TIMELINE AUDIT LOG */}
            <DeploymentTimelineSection
              historyEvents={historyList as unknown as Record<string, unknown>[]}
            />

            {/* MODEL COMPARISON TABLE */}
            {previousModel && (
              <ModelComparisonTableSection prodModel={model} prevModel={previousModel} />
            )}

            {/* RUNTIME CONFIGURATION ACCORDION */}
            <RuntimeConfigAccordionSection model={model} />

            {/* ARTIFACT INTEGRITY ACCORDION */}
            <ArtifactIntegrityAccordionSection model={model} />

            {/* QUICK ACTIONS TOOLBAR */}
            <QuickActionsToolbarSection
              onDeploy={() =>
                toast.info(
                  "Run 'python scripts/deploy_production_model.py' in CLI to deploy a model version.",
                )
              }
              onRefresh={handleRefresh}
            />
          </div>
        )}
      </div>

      {/* Side-by-Side Model Comparison Drawer */}
      {selectedVersionForCompare && (
        <ModelComparisonDrawer
          isOpen={!!selectedVersionForCompare}
          onClose={() => setSelectedVersionForCompare(null)}
          targetVersion={selectedVersionForCompare}
          baseVersion="production"
        />
      )}
    </PageTransition>
  );
}

/* Helper Components */

function MetaRow({
  label,
  value,
  isMono = false,
  isStatus = false,
  isLink = false,
  isCopyable = false,
}: {
  label: string;
  value: string;
  isMono?: boolean;
  isStatus?: boolean;
  isLink?: boolean;
  isCopyable?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/30">
      <span className="text-muted-foreground font-medium">{label}</span>
      <div className="flex items-center gap-1.5 min-w-0">
        <span
          className={cn(
            "font-medium text-foreground/80 truncate max-w-[220px]",
            isMono && "font-mono text-xs sm:text-sm text-foreground/75 font-normal",
            isStatus && "text-emerald-500/90 font-medium",
            isLink && "text-brand/90 hover:underline cursor-pointer font-medium",
          )}
        >
          {value}
        </span>
        {isCopyable && (
          <button
            type="button"
            onClick={handleCopy}
            title="Copy value"
            className="p-1 hover:bg-muted/80 rounded transition-colors text-muted-foreground hover:text-foreground shrink-0"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}

function HealthBadge({ label, status }: { label: string; status: string }) {
  return (
    <div className="p-3 rounded-lg border border-border/60 bg-muted/30 flex items-center justify-between min-w-0">
      <span className="text-xs sm:text-sm font-medium text-muted-foreground truncate">{label}</span>
      <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1.5 shrink-0 ml-2">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
        </span>
        {status}
      </span>
    </div>
  );
}

function MetricRow({
  label,
  value,
  isHighlight = false,
  isGreen = false,
}: {
  label: string;
  value: string;
  isHighlight?: boolean;
  isGreen?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-muted-foreground font-medium">{label}</span>
      <span
        className={cn(
          "font-semibold font-mono text-foreground/80 text-xs sm:text-sm",
          isHighlight && "text-brand/90",
          isGreen && "text-emerald-500/90",
        )}
      >
        {value}
      </span>
    </div>
  );
}

function EnterpriseSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Skeleton className="lg:col-span-8 h-64 rounded-xl bg-muted/40" />
        <Skeleton className="lg:col-span-4 h-64 rounded-xl bg-muted/40" />
      </div>
      <Skeleton className="h-36 rounded-xl bg-muted/40" />
      <Skeleton className="h-64 rounded-xl bg-muted/40" />
    </div>
  );
}
