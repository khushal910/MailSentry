import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import {
  RefreshCw,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  MoreVertical,
  Download,
  Terminal,
  ExternalLink,
} from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/production-model")({
  head: () => ({
    meta: [
      { title: "Production Model — MailSentry MLOps Platform" },
      {
        name: "description",
        content: "Enterprise serving status, health telemetry, candidate models, and lifecycle audit log of deployed AI models.",
      },
    ],
  }),
  component: ProductionModelPage,
});

function ProductionModelPage() {
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [selectedVersionForCompare, setSelectedVersionForCompare] = useState<string | null>(null);
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [isRollbackModalOpen, setIsRollbackModalOpen] = useState(false);

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
        {/* STICKY HEADER TOOLBAR */}
        <div className="sticky top-0 z-20 bg-background/95 backdrop-blur-md border-b border-border/80 pb-4 pt-2 -mx-4 px-4 sm:-mx-6 sm:px-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
                Production Model
              </h1>
              <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-extrabold text-sm px-3 py-1 rounded-full flex items-center gap-2 shadow-xs">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-[0_0_8px_#10b981]" />
                </span>
                Serving Traffic
              </Badge>
            </div>
            <p className="mt-1.5 text-sm sm:text-base text-muted-foreground font-semibold">
              Monitor and manage the model currently serving production traffic in MailSentry.
            </p>
          </div>

          {/* Sticky Actions Toolbar (Right side) */}
          <div className="flex flex-wrap items-center gap-2.5">
            <Button
              id="sticky-deploy-model-btn"
              size="sm"
              onClick={() => setIsDeployModalOpen(true)}
              className="bg-brand text-brand-foreground hover:bg-brand/90 font-extrabold text-xs sm:text-sm h-9 px-4 rounded-lg shadow-xs"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Deploy Model
            </Button>

            <Button
              id="sticky-rollback-btn"
              variant="outline"
              size="sm"
              onClick={() => setIsRollbackModalOpen(true)}
              className="border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 font-extrabold text-xs sm:text-sm h-9 px-4 rounded-lg"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Rollback
            </Button>

            <Button
              id="sticky-refresh-btn"
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isModelLoading || isModelFetching || isManualRefreshing}
              className="border-border/80 text-foreground font-extrabold text-xs sm:text-sm h-9 px-4 rounded-lg"
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
                <Button variant="outline" size="icon" className="h-9 w-9 rounded-lg border-border/80">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 text-xs sm:text-sm font-semibold">
                <DropdownMenuItem onClick={() => window.open("http://localhost:5000", "_blank")}>
                  <ExternalLink className="mr-2.5 h-4 w-4" /> Open MLflow UI
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => alert("Model artifacts downloaded")}>
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
              <h3 className="text-base font-bold text-foreground">Production Model Service Unavailable</h3>
              <p className="text-xs sm:text-sm text-muted-foreground font-medium max-w-md mx-auto">
                Unable to retrieve production model specs. Please verify backend service endpoints.
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={handleRefresh} className="h-9 text-xs sm:text-sm font-bold">
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
                      <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 font-extrabold text-sm px-3 py-1 rounded-md flex items-center gap-2">
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
                      Algorithm: <strong className="text-foreground/85 font-semibold">{model.algorithm || model.algorithm_type}</strong>
                    </span>
                  </div>

                  {/* 2-Column Technical Metadata Key-Value Layout */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-xs sm:text-sm">
                    <MetaRow label="Serving Endpoint" value="/api/v1/classify-email" isMono />
                    <MetaRow label="Deployment Status" value={model.deployment_status || "Active Serving Traffic"} isStatus />
                    <MetaRow label="Deployment Date" value={formattedDate(model.deployment_date || model.trained_at)} />
                    <MetaRow label="Deployed By" value="khushalsatani009" />
                    <MetaRow label="Serving Environment" value="Production (US-East-1)" />
                    <MetaRow label="Model File Size" value={`${model.model_size_mb || 0.05} MB`} />
                    <MetaRow label="Dataset Version" value={model.dataset_version || "v1.0.0"} isMono />
                    <MetaRow label="Git Commit SHA" value="a1b2c3d" isMono />
                    <MetaRow label="MLflow Run ID" value="1233668301d94c14a3c98f6a87d234a5" isMono isLink />
                    <MetaRow label="Docker Container Image" value="mailsentry/ml-service:v2.0" isMono />
                    <MetaRow label="Python Runtime" value="Python 3.13.1" />
                    <MetaRow label="Model SHA256" value={model.model_hash ? `${model.model_hash.slice(0, 16)}...` : "7f0e8e98ac1f14a7..."} isMono />
                    <MetaRow label="Training Pipeline Ver" value="v1.2.0" isMono />
                    <MetaRow label="Feature Store Ver" value="v1.0" isMono />
                  </div>
                </div>
              </div>

              {/* Right Column: Health Summary & Live Metrics */}
              <div className="lg:col-span-4 rounded-xl border border-border/80 bg-card p-6 flex flex-col justify-between shadow-xs">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-border/60 pb-3">
                    <h3 className="text-base sm:text-lg font-bold text-foreground">Health & Telemetry</h3>
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
                    <MetricRow label="Average Latency" value={model.inference_time_ms ? `${model.inference_time_ms.toFixed(3)} ms` : "1.743 ms"} isHighlight />
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
              onDeploy={(ver) => setIsDeployModalOpen(true)}
            />

            {/* TRAFFIC MONITORING TELEMETRY */}
            <TrafficMonitoringSection />

            {/* DEPLOYMENT TIMELINE AUDIT LOG */}
            <DeploymentTimelineSection historyEvents={historyList} />

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
              onDeploy={() => setIsDeployModalOpen(true)}
              onRollback={() => setIsRollbackModalOpen(true)}
              onRefresh={handleRefresh}
            />
          </div>
        )}
      </div>

      {/* Deploy Model Confirmation Dialog */}
      <Dialog open={isDeployModalOpen} onOpenChange={setIsDeployModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold">Promote Candidate to Production</DialogTitle>
            <DialogDescription className="text-xs sm:text-sm">
              Are you sure you want to promote the latest candidate model to production serving?
            </DialogDescription>
          </DialogHeader>

          <div className="p-3.5 rounded-lg bg-muted/40 border border-border/60 text-xs sm:text-sm space-y-1 font-mono">
            <div>Current Production: <strong>{model?.version} ({model?.model_name})</strong></div>
            <div>Promoting Target: <strong className="text-emerald-500">v3 (Candidate)</strong></div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" size="sm" onClick={() => setIsDeployModalOpen(false)} className="text-xs sm:text-sm font-semibold">
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setIsDeployModalOpen(false);
                toast.success("Candidate model promoted to production successfully");
              }}
              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-bold"
            >
              Confirm Promotion
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rollback Model Confirmation Dialog */}
      <Dialog open={isRollbackModalOpen} onOpenChange={setIsRollbackModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold">Rollback Production Model</DialogTitle>
            <DialogDescription className="text-xs sm:text-sm text-amber-600 dark:text-amber-400 font-semibold">
              Warning: Rolling back will revert serving traffic to the previous model version.
            </DialogDescription>
          </DialogHeader>

          <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs sm:text-sm space-y-1 font-mono">
            <div>Active Version: <strong>{model?.version}</strong></div>
            <div>Rollback Target: <strong>{previousModel ? previousModel.version : "v1.0.0"}</strong></div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" size="sm" onClick={() => setIsRollbackModalOpen(false)} className="text-xs sm:text-sm font-semibold">
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setIsRollbackModalOpen(false);
                toast.success("Production model rolled back successfully");
              }}
              className="bg-amber-600 hover:bg-amber-700 text-white text-xs sm:text-sm font-bold"
            >
              Confirm Rollback
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
}: {
  label: string;
  value: string;
  isMono?: boolean;
  isStatus?: boolean;
  isLink?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/30">
      <span className="text-muted-foreground font-medium">{label}</span>
      <span
        className={cn(
          "font-medium text-foreground/80 truncate max-w-[240px]",
          isMono && "font-mono text-xs sm:text-sm text-foreground/75 font-normal",
          isStatus && "text-emerald-500/90 font-medium",
          isLink && "text-brand/90 hover:underline cursor-pointer font-medium"
        )}
      >
        {value}
      </span>
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
          isGreen && "text-emerald-500/90"
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
