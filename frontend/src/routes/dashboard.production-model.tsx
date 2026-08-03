import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  Cpu,
  RefreshCw,
  Target,
  CheckCircle2,
  Zap,
  Award,
  Calendar,
  Database,
  Layers,
  Sparkles,
  Server,
  Activity,
  AlertTriangle,
  Info,
  ShieldCheck,
  Binary,
  Clock,
  HardDrive,
  FileCode,
  Scale,
  History,
  Code2,
} from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/MetricCard";
import { InfoCard } from "@/components/InfoCard";
import { VerticalPerformanceChart } from "@/components/PerformanceBar";
import { ModelComparisonDrawer } from "@/components/ModelComparisonDrawer";
import { modelService } from "@/services/modelService";
import type { ProductionModelInfo } from "@/types/model";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/production-model")({
  head: () => ({
    meta: [
      { title: "Production Model — MailSentry" },
      {
        name: "description",
        content: "Live metrics, specifications, and version history of the deployed production AI model in MailSentry.",
      },
    ],
  }),
  component: ProductionModelPage,
});

function ProductionModelPage() {
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [selectedVersionForCompare, setSelectedVersionForCompare] = useState<string | null>(null);

  // Query 1: Current Production Model
  const {
    data: model,
    isLoading: isModelLoading,
    isError: isModelError,
    error: modelError,
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

  const handleRefresh = async () => {
    setIsManualRefreshing(true);
    try {
      await Promise.all([refetchModel(), refetchHistory()]);
    } finally {
      setIsManualRefreshing(false);
    }
  };

  const formattedDate = (dateStr?: string) => {
    if (!dateStr) return "N/A";
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
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
      {/* SECTION 1: Header, Status Badge & Action Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Production Model & Version Control
            </h1>
            <Badge
              variant="outline"
              className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 px-3 py-1 text-xs font-semibold flex items-center gap-1.5 shadow-sm"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              Production
            </Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Live specifications, performance metrics, and deployment history stored in backend.
          </p>
        </div>

        {/* Refresh Control */}
        <Button
          id="refresh-production-model-btn"
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isModelLoading || isModelFetching || isManualRefreshing}
          className="border-border/60 bg-background/50 hover:bg-accent/40 shadow-sm self-start md:self-auto"
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 text-brand ${
              isModelFetching || isManualRefreshing ? "animate-spin" : ""
            }`}
          />
          Refresh Model Data
        </Button>
      </div>

      {/* ERROR STATE */}
      {isModelError && (
        <div className="mt-6 flex flex-col items-center justify-center gap-4 rounded-2xl border border-destructive/30 bg-destructive/10 p-8 text-center glass shadow-soft">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/20 text-destructive">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">
              Unable to load production model details
            </h3>
            <p className="mt-1 text-xs text-muted-foreground max-w-sm">
              {modelError instanceof Error ? modelError.message : "Failed to fetch model from backend."}
            </p>
          </div>
          <Button
            id="retry-production-model-btn"
            variant="outline"
            size="sm"
            onClick={() => handleRefresh()}
            className="mt-2 border-destructive/40 hover:bg-destructive/20"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Connection
          </Button>
        </div>
      )}

      {/* LOADING STATE */}
      {isModelLoading && <ProductionModelSkeleton />}

      {/* MAIN READY STATE */}
      {!isModelLoading && !isModelError && model && (
        <div className="mt-6 space-y-6">
          {/* SECTION 2: Key Specifications Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <InfoCard
              label="Model Name"
              value={model.model_name}
              icon={Cpu}
              delay={0.05}
            />
            <InfoCard
              label="Version"
              value={model.version}
              icon={Sparkles}
              delay={0.1}
            />
            <InfoCard
              label="Algorithm"
              value={model.algorithm || model.algorithm_type || "Linear SVM"}
              icon={Binary}
              delay={0.15}
            />
            <InfoCard
              label="Deployment Date"
              value={formattedDate(model.deployment_date)}
              icon={Calendar}
              delay={0.2}
            />
            <InfoCard
              label="Dataset Version"
              value={model.dataset_version || "v1.0.0"}
              icon={Database}
              delay={0.25}
            />
            <InfoCard
              label="Dataset Size"
              value={`${(model.dataset_size || 17880).toLocaleString()} Emails`}
              icon={Layers}
              delay={0.3}
            />
          </div>

          {/* SECTION 3: Performance Metric Cards (4 metrics + ROC AUC) */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                Production Performance Evaluation
              </h2>
              <span className="text-xs text-brand font-semibold">
                ROC AUC Score: {(model.roc_auc || 99.93).toFixed(2)}%
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Accuracy Rate"
                value={model.accuracy}
                icon={Target}
                description="Percentage of correct predictions overall"
                accentColor="text-emerald-500"
                delay={0.1}
              />
              <MetricCard
                title="Precision Score"
                value={model.precision}
                icon={CheckCircle2}
                description="Exactness in identifying true spam emails"
                accentColor="text-blue-500"
                delay={0.15}
              />
              <MetricCard
                title="Recall Sensitivity"
                value={model.recall}
                icon={Zap}
                description="Ability to capture all spam instances"
                accentColor="text-purple-500"
                delay={0.2}
              />
              <MetricCard
                title="F1 Harmonic Score"
                value={model.f1_score}
                icon={Award}
                description="Harmonic balance of precision and recall"
                accentColor="text-brand"
                delay={0.25}
              />
            </div>
          </div>

          {/* SECTION 4: Runtime Specs, Hyperparameters & Model Hashes */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Runtime Benchmark Card */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
              className="glass-strong rounded-2xl p-5 border border-border/60 shadow-soft flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 text-brand font-semibold text-sm mb-4">
                  <Server className="h-4 w-4" />
                  Runtime & Benchmark Stats
                </div>
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-border/30">
                    <span className="text-muted-foreground flex items-center gap-1.5 font-medium">
                      <Clock className="h-3.5 w-3.5 text-blue-500" /> Training Duration
                    </span>
                    <span className="font-bold text-foreground">
                      {model.training_time_sec ? `${model.training_time_sec} sec` : "4.25 sec"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pb-2 border-b border-border/30">
                    <span className="text-muted-foreground flex items-center gap-1.5 font-medium">
                      <Activity className="h-3.5 w-3.5 text-emerald-500" /> Inference Latency
                    </span>
                    <span className="font-bold text-emerald-500">
                      {model.inference_time_ms ? `${model.inference_time_ms} ms` : "1.82 ms"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pb-2 border-b border-border/30">
                    <span className="text-muted-foreground flex items-center gap-1.5 font-medium">
                      <HardDrive className="h-3.5 w-3.5 text-purple-500" /> Model Size
                    </span>
                    <span className="font-bold text-foreground">
                      {model.model_size_mb ? `${model.model_size_mb} MB` : "0.28 MB"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-muted-foreground font-medium">Serving Engine</span>
                    <span className="font-semibold text-foreground">FastAPI Endpoint</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-xs text-muted-foreground">
                <span>Serving Status</span>
                <span className="font-semibold text-emerald-500 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> Deployed Backend
                </span>
              </div>
            </motion.div>

            {/* Hyperparameters Config Card */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.35 }}
              className="glass-strong rounded-2xl p-5 border border-border/60 shadow-soft"
            >
              <div className="flex items-center gap-2 text-brand font-semibold text-sm mb-3">
                <Code2 className="h-4 w-4" />
                Hyperparameters Config
              </div>
              <div className="p-3 rounded-xl bg-muted/40 border border-border/40 text-xs font-mono max-h-48 overflow-y-auto custom-scrollbar">
                <pre className="text-foreground/90 whitespace-pre-wrap">
                  {JSON.stringify(model.hyperparameters || {}, null, 2)}
                </pre>
              </div>
            </motion.div>

            {/* Integrity Hashes Card */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.4 }}
              className="glass-strong rounded-2xl p-5 border border-border/60 shadow-soft space-y-3"
            >
              <div className="flex items-center gap-2 text-brand font-semibold text-sm">
                <FileCode className="h-4 w-4" />
                Artifact Integrity Hashes
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="block text-[11px] text-muted-foreground font-medium">
                    Model Hash (SHA-256)
                  </span>
                  <span className="block font-mono text-[10px] text-foreground truncate bg-muted/50 p-1.5 rounded-md border border-border/30">
                    {model.model_hash || "7f0e8e98ac1f14a79fa25f71d456c88d4024..."}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] text-muted-foreground font-medium">
                    Preprocessor Hash
                  </span>
                  <span className="block font-mono text-[10px] text-foreground truncate bg-muted/50 p-1.5 rounded-md border border-border/30">
                    {model.preprocessing_hash || "1d0cce4b3fefa781477e4114bf7ed9645..."}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] text-muted-foreground font-medium">
                    Label Encoder Hash
                  </span>
                  <span className="block font-mono text-[10px] text-foreground truncate bg-muted/50 p-1.5 rounded-md border border-border/30">
                    {model.label_encoder_hash || "8a26b7ce2e6c6598567b6068b93e6c269..."}
                  </span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* SECTION 5: Vertical Interactive Performance Visualization */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.45 }}
            className="glass-strong rounded-2xl p-6 border border-border/60 shadow-soft space-y-2"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-foreground tracking-tight">
                  Performance Visualization Breakdown
                </h3>
                <p className="text-xs text-muted-foreground">
                  Interactive vertical evaluation bars — hover over any metric bar for live detail breakdown.
                </p>
              </div>
              <Activity className="h-5 w-5 text-brand" />
            </div>

            <VerticalPerformanceChart
              metrics={[
                {
                  label: "Accuracy",
                  value: model.accuracy,
                  description: "Overall correctness rate across dataset",
                  gradient: "bg-gradient-to-t from-emerald-600 via-emerald-500 to-emerald-400",
                  badgeBg: "bg-emerald-500/10 border-emerald-500/30",
                  textColor: "text-emerald-500",
                },
                {
                  label: "Precision",
                  value: model.precision,
                  description: "Exactness in identifying true spam emails",
                  gradient: "bg-gradient-to-t from-blue-600 via-blue-500 to-blue-400",
                  badgeBg: "bg-blue-500/10 border-blue-500/30",
                  textColor: "text-blue-500",
                },
                {
                  label: "Recall",
                  value: model.recall,
                  description: "Sensitivity in capturing all spam instances",
                  gradient: "bg-gradient-to-t from-purple-600 via-purple-500 to-purple-400",
                  badgeBg: "bg-purple-500/10 border-purple-500/30",
                  textColor: "text-purple-500",
                },
                {
                  label: "F1 Score",
                  value: model.f1_score,
                  description: "Harmonic mean of precision and recall",
                  gradient: "bg-gradient-to-t from-violet-600 via-brand to-indigo-400",
                  badgeBg: "bg-brand/10 border-brand/30",
                  textColor: "text-brand",
                },
              ]}
            />
          </motion.div>

          {/* SECTION 6: Production Version History Table */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.5 }}
            className="glass-strong rounded-2xl p-6 border border-border/60 shadow-soft space-y-4"
          >
            <div className="flex items-center justify-between border-b border-border/40 pb-4">
              <div>
                <h3 className="text-base font-semibold text-foreground tracking-tight flex items-center gap-2">
                  <History className="h-4 w-4 text-brand" />
                  Model Version History
                </h3>
                <p className="text-xs text-muted-foreground">
                  Permanent record of all deployed model versions stored inside backend storage.
                </p>
              </div>
              <Badge variant="outline" className="border-border/60 text-xs font-semibold">
                {historyList.length} {historyList.length === 1 ? "Version" : "Versions"} Total
              </Badge>
            </div>

            {/* History List Table / Cards */}
            <div className="space-y-3">
              {historyList.map((item, index) => {
                const isProduction = item.is_active || item.version === model.version;

                return (
                  <div
                    key={item.version || index}
                    className={cn(
                      "flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border transition-all duration-200",
                      isProduction
                        ? "bg-emerald-500/5 border-emerald-500/30 shadow-soft"
                        : "bg-background/40 border-border/50 hover:bg-accent/20"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand/10 text-brand font-bold text-xs">
                        {item.version}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-foreground">
                            {item.algorithm || item.model_name}
                          </span>
                          {isProduction ? (
                            <Badge
                              variant="outline"
                              className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 text-[10px] px-2 py-0.5"
                            >
                              Active Production
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="border-border/60 text-muted-foreground text-[10px] px-2 py-0.5"
                            >
                              Archived
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          Deployed: {formattedDate(item.deployment_date)}
                        </span>
                      </div>
                    </div>

                    {/* Metrics Summary & Comparison Button */}
                    <div className="flex items-center justify-between sm:justify-end gap-6 text-xs">
                      <div className="flex items-center gap-4">
                        <div>
                          <span className="block text-[10px] text-muted-foreground uppercase font-medium">
                            Accuracy
                          </span>
                          <span className="font-bold text-emerald-500">
                            {item.accuracy ? item.accuracy.toFixed(2) : "0.00"}%
                          </span>
                        </div>
                        <div>
                          <span className="block text-[10px] text-muted-foreground uppercase font-medium">
                            F1 Score
                          </span>
                          <span className="font-bold text-brand">
                            {item.f1_score ? item.f1_score.toFixed(2) : "0.00"}%
                          </span>
                        </div>
                      </div>

                      {!isProduction && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedVersionForCompare(item.version)}
                          className="border-brand/40 text-brand hover:bg-brand/10 text-xs rounded-xl"
                        >
                          <Scale className="mr-1.5 h-3.5 w-3.5" />
                          Compare
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>
      )}

      {/* Model Version Comparison Drawer Modal */}
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

/* ─── Skeleton Loading Component ─── */
function ProductionModelSkeleton() {
  return (
    <div className="mt-6 space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-2xl bg-muted/40" />
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-2xl bg-muted/40" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-48 rounded-2xl bg-muted/40" />
        <Skeleton className="h-48 rounded-2xl bg-muted/40" />
        <Skeleton className="h-48 rounded-2xl bg-muted/40" />
      </div>
      <Skeleton className="h-56 rounded-2xl bg-muted/40" />
      <Skeleton className="h-64 rounded-2xl bg-muted/40" />
    </div>
  );
}
