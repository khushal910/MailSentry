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
} from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/MetricCard";
import { InfoCard } from "@/components/InfoCard";
import { VerticalPerformanceChart } from "@/components/PerformanceBar";
import { modelService } from "@/services/modelService";

export const Route = createFileRoute("/dashboard/production-model")({
  head: () => ({
    meta: [
      { title: "Production Model — MailSentry" },
      {
        name: "description",
        content: "Live metrics and specifications of the deployed production AI model in MailSentry.",
      },
    ],
  }),
  component: ProductionModelPage,
});

function ProductionModelPage() {
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);

  const {
    data: model,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["production-model"],
    queryFn: () => modelService.getProductionModel(),
    staleTime: 1000 * 60 * 5, // 5 minutes cache
  });

  const handleRefresh = async () => {
    setIsManualRefreshing(true);
    try {
      await refetch();
    } finally {
      setIsManualRefreshing(false);
    }
  };

  return (
    <PageTransition>
      {/* SECTION 1: Large Header & Subtitle & Status Badge & Refresh Button */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Production Model
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
            Currently deployed AI model powering MailSentry email classification.
          </p>
        </div>

        {/* SECTION 7: Refresh Button */}
        <Button
          id="refresh-production-model-btn"
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isLoading || isFetching || isManualRefreshing}
          className="border-border/60 bg-background/50 hover:bg-accent/40 shadow-sm self-start md:self-auto"
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 text-brand ${
              isFetching || isManualRefreshing ? "animate-spin" : ""
            }`}
          />
          Refresh Model Info
        </Button>
      </div>

      {/* ERROR STATE */}
      {isError && (
        <div className="mt-6 flex flex-col items-center justify-center gap-4 rounded-2xl border border-destructive/30 bg-destructive/10 p-8 text-center glass shadow-soft">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/20 text-destructive">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">
              Unable to load production model information
            </h3>
            <p className="mt-1 text-xs text-muted-foreground max-w-sm">
              {error instanceof Error ? error.message : "Failed to fetch model details from backend."}
            </p>
          </div>
          <Button
            id="retry-production-model-btn"
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="mt-2 border-destructive/40 hover:bg-destructive/20"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Connection
          </Button>
        </div>
      )}

      {/* LOADING STATE (Skeleton Loaders) */}
      {isLoading && <ProductionModelSkeleton />}

      {/* READY STATE: Display All Sections */}
      {!isLoading && !isError && model && (
        <div className="mt-6 space-y-6">
          {/* SECTION 2: Information Cards Grid */}
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
              label="Task"
              value={model.task}
              icon={Layers}
              delay={0.15}
            />
            <InfoCard
              label="Algorithm"
              value={model.algorithm_type}
              icon={Binary}
              delay={0.2}
            />
            <InfoCard
              label="Training Date"
              value={model.training_date}
              icon={Calendar}
              delay={0.25}
            />
            <InfoCard
              label="Dataset Size"
              value={`${model.dataset_size.toLocaleString()} Emails`}
              icon={Database}
              delay={0.3}
            />
          </div>

          {/* SECTION 3: Model Performance Metric Cards */}
          <div>
            <h2 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-3">
              Model Performance Metrics
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Accuracy"
                value={model.accuracy}
                icon={Target}
                description="Percentage of correct predictions overall"
                accentColor="text-emerald-500"
                delay={0.1}
              />
              <MetricCard
                title="Precision"
                value={model.precision}
                icon={CheckCircle2}
                description="Exactness in identifying true spam emails"
                accentColor="text-blue-500"
                delay={0.15}
              />
              <MetricCard
                title="Recall"
                value={model.recall}
                icon={Zap}
                description="Ability to capture all spam instances"
                accentColor="text-purple-500"
                delay={0.2}
              />
              <MetricCard
                title="F1 Score"
                value={model.f1_score}
                icon={Award}
                description="Harmonic mean of precision and recall"
                accentColor="text-brand"
                delay={0.25}
              />
            </div>
          </div>

          {/* SECTION 4 & 5: Model Description & Deployment Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* SECTION 4: Model Description */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
              className="glass-strong rounded-2xl p-5 border border-border/60 shadow-soft flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 text-brand font-semibold text-sm">
                  <Info className="h-4 w-4" />
                  Model Overview & Description
                </div>
                <p className="mt-3 text-sm text-foreground/90 leading-relaxed">
                  {model.description}
                </p>
              </div>

              <div className="mt-5 pt-4 border-t border-border/40 flex items-center justify-between text-xs text-muted-foreground">
                <span>Active Status</span>
                <span className="font-semibold text-emerald-500 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Verified Active Engine
                </span>
              </div>
            </motion.div>

            {/* SECTION 5: Deployment Information */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.35 }}
              className="glass-strong rounded-2xl p-5 border border-border/60 shadow-soft"
            >
              <div className="flex items-center gap-2 text-brand font-semibold text-sm mb-4">
                <Server className="h-4 w-4" />
                Deployment Architecture & Runtime
              </div>

              <div className="space-y-3 divide-y divide-border/30 text-xs">
                <div className="flex items-center justify-between pt-1">
                  <span className="text-muted-foreground font-medium">Deployment Status</span>
                  <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 text-xs">
                    {model.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between pt-2.5">
                  <span className="text-muted-foreground font-medium">Prediction Type</span>
                  <span className="font-semibold text-foreground">Binary Classification</span>
                </div>
                <div className="flex items-center justify-between pt-2.5">
                  <span className="text-muted-foreground font-medium">Framework</span>
                  <span className="font-semibold text-foreground">PyTorch + HuggingFace Transformers</span>
                </div>
                <div className="flex items-center justify-between pt-2.5">
                  <span className="text-muted-foreground font-medium">Serving Backend</span>
                  <span className="font-semibold text-foreground">FastAPI Engine</span>
                </div>
                <div className="flex items-center justify-between pt-2.5">
                  <span className="text-muted-foreground font-medium">Inference Latency Mode</span>
                  <span className="font-semibold text-emerald-500 flex items-center gap-1">
                    <Activity className="h-3.5 w-3.5 animate-pulse" />
                    Real-Time Inference
                  </span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* SECTION 6: Vertical Interactive Performance Visualization Chart */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.4 }}
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
        </div>
      )}
    </PageTransition>
  );
}

/* ─── Skeleton Loading Component ─── */
function ProductionModelSkeleton() {
  return (
    <div className="mt-6 space-y-6">
      {/* Info Cards Skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-2xl bg-muted/40" />
        ))}
      </div>

      {/* Metric Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-2xl bg-muted/40" />
        ))}
      </div>

      {/* Description & Deployment Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Skeleton className="h-48 rounded-2xl bg-muted/40" />
        <Skeleton className="h-48 rounded-2xl bg-muted/40" />
      </div>

      {/* Progress Visualization Skeleton */}
      <Skeleton className="h-44 rounded-2xl bg-muted/40" />
    </div>
  );
}
