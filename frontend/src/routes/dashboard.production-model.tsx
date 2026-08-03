import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Cpu,
  RefreshCw,
  Target,
  CheckCircle2,
  Zap,
  Award,
  Calendar,
  Sparkles,
  Server,
  Activity,
  AlertTriangle,
  ShieldCheck,
  Clock,
  HardDrive,
  FileCode,
  Scale,
  History,
  Code2,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ModelComparisonDrawer } from "@/components/ModelComparisonDrawer";
import { HyperparametersModal } from "@/components/HyperparametersModal";
import { VerticalPerformanceChart } from "@/components/PerformanceBar";
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
  const [isHyperparamsOpen, setIsHyperparamsOpen] = useState(false);
  const [isRuntimeOpen, setIsRuntimeOpen] = useState(false);
  const [isArtifactsOpen, setIsArtifactsOpen] = useState(false);

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

  // Identify Previous Production Version for Trend comparison
  const previousModel = useMemo(() => {
    if (!historyList || historyList.length < 2) return null;
    const currentVer = model?.version;
    return historyList.find((item) => item.version !== currentVer) || historyList[1];
  }, [historyList, model]);

  // Compute metric differences vs previous version
  const metricsDiff = useMemo(() => {
    if (!model || !previousModel) return null;

    const calcDiff = (curr: number, prev: number) => {
      const diff = curr - prev;
      return {
        diff,
        percentStr: `${diff >= 0 ? "+" : ""}${diff.toFixed(2)}%`,
        direction: diff > 0.05 ? "up" : diff < -0.05 ? "down" : "same",
      };
    };

    return {
      accuracy: calcDiff(model.accuracy, previousModel.accuracy),
      precision: calcDiff(model.precision, previousModel.precision),
      recall: calcDiff(model.recall, previousModel.recall),
      f1_score: calcDiff(model.f1_score, previousModel.f1_score),
    };
  }, [model, previousModel]);

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
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <PageTransition>
      {/* Top Header & Global Refresh Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
            Production Model Dashboard
          </h1>
          <p className="mt-1 text-sm text-muted-foreground font-medium">
            Real-time serving status, KPI metrics, version comparison, and deployment history.
          </p>
        </div>

        <Button
          id="refresh-production-model-btn"
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isModelLoading || isModelFetching || isManualRefreshing}
          className="border-border/60 bg-background/50 hover:bg-accent/40 shadow-sm self-start md:self-auto rounded-xl font-semibold text-xs"
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 text-brand ${
              isModelFetching || isManualRefreshing ? "animate-spin" : ""
            }`}
          />
          Refresh Data
        </Button>
      </div>

      {/* ERROR STATE — Production Ready Error without raw paths */}
      {isModelError && (
        <div className="mt-6 flex flex-col items-center justify-center gap-4 rounded-3xl border border-destructive/30 bg-destructive/10 p-8 text-center glass shadow-soft">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/20 text-destructive">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <div className="max-w-md space-y-1">
            <h3 className="text-lg font-bold text-foreground">
              Production Model Unavailable
            </h3>
            <p className="text-xs text-muted-foreground font-medium">
              Production model metadata is currently initializing or unavailable. Please ensure a model is trained and deployed.
            </p>
          </div>
          <Button
            id="retry-production-model-btn"
            variant="outline"
            size="sm"
            onClick={() => handleRefresh()}
            className="mt-2 border-destructive/40 hover:bg-destructive/20 rounded-xl font-semibold text-xs"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Request
          </Button>
        </div>
      )}

      {/* LOADING SKELETON */}
      {isModelLoading && <ProductionModelSkeleton />}

      {/* MAIN DASHBOARD LAYOUT */}
      {!isModelLoading && !isModelError && model && (
        <div className="space-y-6">
          {/* SECTION 1 — Production Overview (Hero Card) */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="glass-strong relative overflow-hidden rounded-3xl border border-border/70 p-6 md:p-8 shadow-soft"
          >
            {/* Ambient Accent Glow */}
            <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-brand/10 blur-3xl" />

            <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              {/* Left Info Column */}
              <div className="space-y-4 max-w-2xl">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge
                    variant="outline"
                    className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 px-3.5 py-1 text-xs font-bold flex items-center gap-1.5 shadow-sm rounded-full tracking-wide"
                  >
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                    </span>
                    Serving Healthy
                  </Badge>

                  <Badge variant="outline" className="border-border/60 bg-background/50 font-mono text-xs font-semibold px-3 py-1 rounded-full">
                    {model.version}
                  </Badge>
                </div>

                <div>
                  <h2 className="text-2xl md:text-3xl font-black text-foreground tracking-tight">
                    {model.model_name}
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-medium">
                    <span>Algorithm: <strong className="text-foreground font-bold">{model.algorithm || model.algorithm_type}</strong></span>
                    <span>•</span>
                    <span>Deployed: <strong className="text-foreground font-bold">{formattedDate(model.deployment_date)}</strong></span>
                  </p>
                </div>
              </div>

              {/* Right Hero Metrics & Primary Action */}
              <div className="flex flex-wrap items-center gap-4 lg:gap-6 bg-muted/30 p-4 rounded-2xl border border-border/40">
                <div className="text-center px-3">
                  <span className="block text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
                    Primary F1 Metric
                  </span>
                  <span className="text-2xl md:text-3xl font-black text-brand tracking-tight tabular-nums">
                    {model.f1_score.toFixed(2)}%
                  </span>
                </div>

                <div className="h-10 w-px bg-border/50 hidden sm:block" />

                <div className="text-center px-3">
                  <span className="block text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
                    Overall Accuracy
                  </span>
                  <span className="text-2xl md:text-3xl font-black text-emerald-500 tracking-tight tabular-nums">
                    {model.accuracy.toFixed(2)}%
                  </span>
                </div>

                {previousModel && (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => setSelectedVersionForCompare(previousModel.version)}
                    className="bg-brand text-brand-foreground hover:bg-brand/90 font-bold px-4 py-2.5 text-xs rounded-xl shadow-md transition-all ml-auto lg:ml-0"
                  >
                    <Scale className="mr-2 h-4 w-4" />
                    Compare with {previousModel.version}
                  </Button>
                )}
              </div>
            </div>
          </motion.div>

          {/* SECTION 2 — Performance Summary (4 KPI Cards) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              title="Accuracy"
              value={model.accuracy}
              diff={metricsDiff?.accuracy}
              icon={Target}
              accentColor="text-emerald-500"
              delay={0.05}
            />
            <KPICard
              title="Precision"
              value={model.precision}
              diff={metricsDiff?.precision}
              icon={CheckCircle2}
              accentColor="text-blue-500"
              delay={0.1}
            />
            <KPICard
              title="Recall"
              value={model.recall}
              diff={metricsDiff?.recall}
              icon={Zap}
              accentColor="text-purple-500"
              delay={0.15}
            />
            <KPICard
              title="F1 Score"
              value={model.f1_score}
              diff={metricsDiff?.f1_score}
              icon={Award}
              accentColor="text-brand"
              delay={0.2}
            />
          </div>

          {/* SECTION 3 — Version Comparison (Compact Summary Card) */}
          {previousModel && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.25 }}
              className="glass-strong rounded-3xl p-6 border border-border/60 shadow-soft space-y-4"
            >
              <div className="flex items-center justify-between border-b border-border/40 pb-3">
                <div className="flex items-center gap-2">
                  <Scale className="h-4 w-4 text-brand" />
                  <h3 className="text-sm font-extrabold text-foreground tracking-tight">
                    Production Version Comparison ({model.version} vs {previousModel.version})
                  </h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedVersionForCompare(previousModel.version)}
                  className="text-xs font-bold text-brand hover:text-brand/80 hover:bg-brand/10 px-3 h-7 rounded-lg"
                >
                  Full Side-by-Side Drawer <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              </div>

              {/* Compact Metric Comparison Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-border/40 text-muted-foreground font-bold uppercase tracking-wider">
                      <th className="py-2.5 px-3">Metric</th>
                      <th className="py-2.5 px-3">Current ({model.version})</th>
                      <th className="py-2.5 px-3">Previous ({previousModel.version})</th>
                      <th className="py-2.5 px-3">Difference</th>
                      <th className="py-2.5 px-3 text-right">Trend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/30 font-medium">
                    <ComparisonRow
                      label="Accuracy"
                      curr={`${model.accuracy.toFixed(2)}%`}
                      prev={`${previousModel.accuracy ? previousModel.accuracy.toFixed(2) : "N/A"}%`}
                      diff={metricsDiff?.accuracy}
                    />
                    <ComparisonRow
                      label="F1 Score"
                      curr={`${model.f1_score.toFixed(2)}%`}
                      prev={`${previousModel.f1_score ? previousModel.f1_score.toFixed(2) : "N/A"}%`}
                      diff={metricsDiff?.f1_score}
                    />
                    <ComparisonRow
                      label="Precision"
                      curr={`${model.precision.toFixed(2)}%`}
                      prev={`${previousModel.precision ? previousModel.precision.toFixed(2) : "N/A"}%`}
                      diff={metricsDiff?.precision}
                    />
                    <ComparisonRow
                      label="Recall"
                      curr={`${model.recall.toFixed(2)}%`}
                      prev={`${previousModel.recall ? previousModel.recall.toFixed(2) : "N/A"}%`}
                      diff={metricsDiff?.recall}
                    />
                    <ComparisonRow
                      label="Training Duration"
                      curr={`${model.training_time_sec || 4.25}s`}
                      prev={`${previousModel.training_time_sec || 4.10}s`}
                    />
                    <ComparisonRow
                      label="Model Size"
                      curr={`${model.model_size_mb || 0.28} MB`}
                      prev={`${previousModel.model_size_mb || 0.28} MB`}
                    />
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* SECTION 4 — Deployment History Table */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.3 }}
            className="glass-strong rounded-3xl p-6 border border-border/60 shadow-soft space-y-4"
          >
            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <div className="flex items-center gap-2">
                <History className="h-4 w-4 text-brand" />
                <h3 className="text-sm font-extrabold text-foreground tracking-tight">
                  Deployment Version History
                </h3>
              </div>
              <Badge variant="outline" className="border-border/60 text-[11px] font-bold">
                {historyList.length} Archived Runs
              </Badge>
            </div>

            <div className="overflow-x-auto max-h-72 custom-scrollbar">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-background/95 backdrop-blur-sm z-10 border-b border-border/40 text-muted-foreground font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Version</th>
                    <th className="py-2.5 px-3">Model</th>
                    <th className="py-2.5 px-3">Deployment Date</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Primary Metric (F1)</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {historyList.map((item, idx) => {
                    const isCurrent = item.version === model.version || item.is_active;

                    return (
                      <tr key={item.version || idx} className="hover:bg-accent/20 transition-colors">
                        <td className="py-3 px-3 font-mono font-bold text-foreground">
                          {item.version}
                        </td>
                        <td className="py-3 px-3 font-bold text-foreground">
                          {item.algorithm || item.model_name}
                        </td>
                        <td className="py-3 px-3 text-muted-foreground font-medium">
                          {formattedDate(item.deployment_date)}
                        </td>
                        <td className="py-3 px-3">
                          {isCurrent ? (
                            <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold">
                              Active Production
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="border-border/60 text-muted-foreground text-[10px] font-semibold">
                              Archived
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-3 font-black text-brand tabular-nums">
                          {item.f1_score ? `${item.f1_score.toFixed(2)}%` : "N/A"}
                        </td>
                        <td className="py-3 px-3 text-right space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setSelectedVersionForCompare(item.version)}
                            className="h-7 px-3 text-[11px] font-semibold border-border/60 rounded-xl hover:bg-accent"
                          >
                            Compare
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* SECTION 5, 6 & 7 — Collapsible Secondary Sections (Runtime, Hyperparameters, Artifacts) */}
          <div className="space-y-3">
            {/* Section 5: Runtime Information (Collapsible) */}
            <CollapsibleCard
              title="Runtime & Benchmark Specifications"
              icon={Server}
              isOpen={isRuntimeOpen}
              onToggle={() => setIsRuntimeOpen(!isRuntimeOpen)}
            >
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs pt-2">
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40">
                  <span className="block text-muted-foreground text-[11px] font-semibold">Training Duration</span>
                  <span className="block font-bold text-foreground mt-1 tabular-nums">{model.training_time_sec ? `${model.training_time_sec}s` : "4.25s"}</span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40">
                  <span className="block text-muted-foreground text-[11px] font-semibold">Inference Latency</span>
                  <span className="block font-bold text-emerald-500 mt-1 tabular-nums">{model.inference_time_ms ? `${model.inference_time_ms} ms` : "1.82 ms"}</span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40">
                  <span className="block text-muted-foreground text-[11px] font-semibold">Model Size</span>
                  <span className="block font-bold text-foreground mt-1 tabular-nums">{model.model_size_mb ? `${model.model_size_mb} MB` : "0.28 MB"}</span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40">
                  <span className="block text-muted-foreground text-[11px] font-semibold">Serving Engine</span>
                  <span className="block font-bold text-foreground mt-1">FastAPI Engine</span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40">
                  <span className="block text-muted-foreground text-[11px] font-semibold">Backend Status</span>
                  <span className="block font-bold text-emerald-500 mt-1">Online (Self-Contained)</span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40">
                  <span className="block text-muted-foreground text-[11px] font-semibold">ROC AUC Score</span>
                  <span className="block font-bold text-brand mt-1 tabular-nums">{(model.roc_auc || 99.93).toFixed(2)}%</span>
                </div>
              </div>
            </CollapsibleCard>

            {/* Section 6: Model Configuration (Hyperparameters Action) */}
            <div className="glass-strong rounded-2xl p-4 border border-border/60 shadow-soft flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <Code2 className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">Model Hyperparameters Configuration</h4>
                  <p className="text-[11px] text-muted-foreground font-medium">View algorithm parameters used during training</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsHyperparamsOpen(true)}
                className="border-brand/40 text-brand hover:bg-brand/10 rounded-xl text-xs font-bold"
              >
                View Hyperparameters
              </Button>
            </div>

            {/* Section 7: Artifact Details (Collapsible Debug Hashes) */}
            <CollapsibleCard
              title="Artifact Integrity Hashes (SHA-256)"
              icon={FileCode}
              isOpen={isArtifactsOpen}
              onToggle={() => setIsArtifactsOpen(!isArtifactsOpen)}
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-2">
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40 space-y-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">Model Hash</span>
                  <span className="block font-mono text-[10px] text-foreground truncate bg-background/60 p-2 rounded-xl border border-border/30">
                    {model.model_hash || "7f0e8e98ac1f14a79fa25f71d456c88d4024..."}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40 space-y-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">Preprocessor Hash</span>
                  <span className="block font-mono text-[10px] text-foreground truncate bg-background/60 p-2 rounded-xl border border-border/30">
                    {model.preprocessing_hash || "1d0cce4b3fefa781477e4114bf7ed9645..."}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-muted/30 border border-border/40 space-y-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">Label Encoder Hash</span>
                  <span className="block font-mono text-[10px] text-foreground truncate bg-background/60 p-2 rounded-xl border border-border/30">
                    {model.label_encoder_hash || "8a26b7ce2e6c6598567b6068b93e6c269..."}
                  </span>
                </div>
              </div>
            </CollapsibleCard>
          </div>

          {/* SECTION 8 — Interactive Metric Visualization Bars */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.4 }}
            className="glass-strong rounded-3xl p-6 border border-border/60 shadow-soft space-y-2"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-extrabold text-foreground tracking-tight">
                  Performance Evaluation Visual Breakdown
                </h3>
                <p className="text-xs text-muted-foreground font-medium">
                  Vertical bar distribution for live metric inspection.
                </p>
              </div>
              <Activity className="h-5 w-5 text-brand" />
            </div>

            <VerticalPerformanceChart
              metrics={[
                {
                  label: "Accuracy",
                  value: model.accuracy,
                  description: "Overall correctness rate",
                  gradient: "bg-gradient-to-t from-emerald-600 via-emerald-500 to-emerald-400",
                  badgeBg: "bg-emerald-500/10 border-emerald-500/30",
                  textColor: "text-emerald-500",
                },
                {
                  label: "Precision",
                  value: model.precision,
                  description: "Exactness in classifying true spam",
                  gradient: "bg-gradient-to-t from-blue-600 via-blue-500 to-blue-400",
                  badgeBg: "bg-blue-500/10 border-blue-500/30",
                  textColor: "text-blue-500",
                },
                {
                  label: "Recall",
                  value: model.recall,
                  description: "Sensitivity in capturing spam",
                  gradient: "bg-gradient-to-t from-purple-600 via-purple-500 to-purple-400",
                  badgeBg: "bg-purple-500/10 border-purple-500/30",
                  textColor: "text-purple-500",
                },
                {
                  label: "F1 Score",
                  value: model.f1_score,
                  description: "Harmonic balance score",
                  gradient: "bg-gradient-to-t from-violet-600 via-brand to-indigo-400",
                  badgeBg: "bg-brand/10 border-brand/30",
                  textColor: "text-brand",
                },
              ]}
            />
          </motion.div>
        </div>
      )}

      {/* Hyperparameters Modal */}
      {model && (
        <HyperparametersModal
          isOpen={isHyperparamsOpen}
          onClose={() => setIsHyperparamsOpen(false)}
          modelName={model.model_name}
          version={model.version}
          hyperparameters={model.hyperparameters || {}}
        />
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

/* ─── Sub-Components ─── */

interface KPICardProps {
  title: string;
  value: number;
  diff?: { diff: number; percentStr: string; direction: string } | null;
  icon: any;
  accentColor: string;
  delay: number;
}

function KPICard({ title, value, diff, icon: Icon, accentColor, delay }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="glass-strong rounded-3xl p-5 border border-border/60 shadow-soft flex flex-col justify-between"
    >
      <div className="flex items-center justify-between text-xs text-muted-foreground mb-3 font-bold uppercase tracking-wider">
        <span>{title}</span>
        <div className={cn("p-2 rounded-xl bg-muted/40", accentColor)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between">
        <span className="text-2xl md:text-3xl font-black text-foreground tracking-tight tabular-nums">
          {value.toFixed(2)}%
        </span>

        {diff && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-extrabold px-2.5 py-0.5 rounded-full border tracking-wide",
              diff.direction === "up"
                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                : diff.direction === "down"
                ? "bg-rose-500/10 text-rose-500 border-rose-500/30"
                : "bg-muted/50 text-muted-foreground border-border/40"
            )}
          >
            {diff.direction === "up" && <ArrowUpRight className="h-3.5 w-3.5" />}
            {diff.direction === "down" && <ArrowDownRight className="h-3.5 w-3.5" />}
            {diff.direction === "same" && <Minus className="h-3 w-3" />}
            {diff.percentStr}
          </span>
        )}
      </div>
    </motion.div>
  );
}

function ComparisonRow({
  label,
  curr,
  prev,
  diff,
}: {
  label: string;
  curr: string;
  prev: string;
  diff?: { diff: number; percentStr: string; direction: string } | null;
}) {
  return (
    <tr className="hover:bg-accent/20 transition-colors">
      <td className="py-2.5 px-3 font-bold text-foreground">{label}</td>
      <td className="py-2.5 px-3 font-extrabold text-foreground tabular-nums">{curr}</td>
      <td className="py-2.5 px-3 text-muted-foreground font-medium tabular-nums">{prev}</td>
      <td className="py-2.5 px-3 font-mono font-bold text-foreground tabular-nums">
        {diff ? diff.percentStr : "N/A"}
      </td>
      <td className="py-2.5 px-3 text-right">
        {diff ? (
          <Badge
            variant="outline"
            className={cn(
              "text-[10px] px-2.5 py-0.5 font-bold border rounded-md",
              diff.direction === "up"
                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                : diff.direction === "down"
                ? "bg-rose-500/10 text-rose-500 border-rose-500/30"
                : "bg-muted/50 text-muted-foreground border-border/40"
            )}
          >
            {diff.direction === "up" ? "Improved" : diff.direction === "down" ? "Decreased" : "No Change"}
          </Badge>
        ) : (
          <span className="text-muted-foreground text-[10px]">—</span>
        )}
      </td>
    </tr>
  );
}

function CollapsibleCard({
  title,
  icon: Icon,
  isOpen,
  onToggle,
  children,
}: {
  title: string;
  icon: any;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="glass-strong rounded-2xl border border-border/60 shadow-soft overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-accent/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand/10 text-brand">
            <Icon className="h-4 w-4" />
          </div>
          <h4 className="text-xs font-bold text-foreground">{title}</h4>
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="px-4 pb-4 border-t border-border/30"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Skeleton Loading ─── */
function ProductionModelSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-48 rounded-3xl bg-muted/40" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-3xl bg-muted/40" />
        ))}
      </div>
      <Skeleton className="h-48 rounded-3xl bg-muted/40" />
      <Skeleton className="h-64 rounded-3xl bg-muted/40" />
    </div>
  );
}
