import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  Scale,
  Cpu,
  Calendar,
  Sparkles,
  Database,
  Code2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { modelService } from "@/services/modelService";
import type { ModelComparisonResult } from "@/types/model";
import { cn } from "@/lib/utils";

interface ModelComparisonDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  targetVersion: string;
  baseVersion?: string;
}

export function ModelComparisonDrawer({
  isOpen,
  onClose,
  targetVersion,
  baseVersion = "production",
}: ModelComparisonDrawerProps) {
  const [data, setData] = useState<ModelComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && targetVersion) {
      setIsLoading(true);
      setError(null);
      modelService
        .compareModels(targetVersion, baseVersion)
        .then((res) => {
          setData(res);
        })
        .catch((err) => {
          setError(err.message || "Failed to compare model versions");
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [isOpen, targetVersion, baseVersion]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-end bg-background/80 backdrop-blur-sm p-2 sm:p-4">
        {/* Backdrop overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0"
        />

        {/* Drawer container */}
        <motion.div
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 250 }}
          className="glass-strong relative z-10 flex h-full max-h-[92vh] w-full max-w-2xl flex-col rounded-3xl border border-border/70 p-6 shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border/40 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
                <Scale className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold tracking-tight text-foreground">
                  Model Version Comparison
                </h2>
                <p className="text-xs text-muted-foreground">
                  Comparing <span className="font-semibold text-brand">{targetVersion}</span> vs{" "}
                  <span className="font-semibold text-emerald-500">Current Production</span>
                </p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="rounded-full hover:bg-accent/50"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto py-4 space-y-6 pr-1 custom-scrollbar">
            {isLoading && <ComparisonSkeleton />}

            {error && (
              <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-5 text-center text-xs text-destructive">
                {error}
              </div>
            )}

            {!isLoading && !error && data && (
              <>
                {/* Models Header Overview Cards */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Target Version Card (Selected) */}
                  <div className="rounded-2xl p-4 border border-border/60 bg-muted/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="border-border/60 text-xs">
                        Selected Version
                      </Badge>
                      <span className="text-xs font-bold text-brand">{data.v1.version}</span>
                    </div>
                    <div>
                      <span className="block text-sm font-bold text-foreground">
                        {data.v1.algorithm || data.v1.model_name}
                      </span>
                      <span className="block text-[11px] text-muted-foreground">
                        Dataset: {data.v1.dataset_version}
                      </span>
                    </div>
                  </div>

                  {/* Production Version Card */}
                  <div className="rounded-2xl p-4 border border-emerald-500/30 bg-emerald-500/5 space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge
                        variant="outline"
                        className="border-emerald-500/40 bg-emerald-500/10 text-emerald-500 text-xs font-semibold"
                      >
                        ● Production
                      </Badge>
                      <span className="text-xs font-bold text-emerald-500">{data.v2.version}</span>
                    </div>
                    <div>
                      <span className="block text-sm font-bold text-foreground">
                        {data.v2.algorithm || data.v2.model_name}
                      </span>
                      <span className="block text-[11px] text-muted-foreground">
                        Dataset: {data.v2.dataset_version}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Metrics Comparison Breakdown Table */}
                <div className="rounded-2xl border border-border/60 overflow-hidden bg-background/40">
                  <div className="bg-muted/40 px-4 py-3 border-b border-border/40 text-xs font-bold text-foreground uppercase tracking-wider">
                    Performance Metric Differences
                  </div>

                  <div className="divide-y divide-border/30">
                    {Object.entries(data.comparison).map(([key, item]) => {
                      const isImproved = item.status === "improved";
                      const isDecreased = item.status === "decreased";

                      return (
                        <div
                          key={key}
                          className="px-4 py-3 flex items-center justify-between hover:bg-accent/20 transition-colors text-xs"
                        >
                          <div className="w-1/3">
                            <span className="font-semibold text-foreground">{item.label}</span>
                          </div>

                          {/* Values */}
                          <div className="flex items-center justify-center gap-4 w-1/3 text-center">
                            <span className="text-muted-foreground font-medium">
                              {item.v1_value}
                              {item.unit === "%" ? "%" : ` ${item.unit}`}
                            </span>
                            <span className="text-muted-foreground">→</span>
                            <span className="font-bold text-foreground">
                              {item.v2_value}
                              {item.unit === "%" ? "%" : ` ${item.unit}`}
                            </span>
                          </div>

                          {/* Delta Indicator */}
                          <div className="w-1/3 flex justify-end">
                            <span
                              className={cn(
                                "inline-flex items-center gap-1 font-bold px-2.5 py-1 rounded-lg text-xs border shadow-xs",
                                isImproved &&
                                  "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
                                isDecreased &&
                                  "bg-destructive/10 text-destructive border-destructive/30",
                                !isImproved &&
                                  !isDecreased &&
                                  "bg-muted/50 text-muted-foreground border-border/40"
                              )}
                            >
                              {isImproved && <TrendingUp className="h-3.5 w-3.5" />}
                              {isDecreased && <TrendingDown className="h-3.5 w-3.5" />}
                              {!isImproved && !isDecreased && <Minus className="h-3.5 w-3.5" />}
                              {item.diff > 0 ? `+${item.diff}` : item.diff}{" "}
                              {item.unit === "%" ? "%" : ""} ({item.percentage_change > 0 ? `+${item.percentage_change}%` : `${item.percentage_change}%`})
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Hyperparameters Comparison */}
                <div className="rounded-2xl border border-border/60 p-4 space-y-3 bg-background/40">
                  <div className="flex items-center gap-2 text-xs font-bold text-foreground uppercase tracking-wider">
                    <Code2 className="h-4 w-4 text-brand" />
                    Hyperparameters Comparison
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-3 rounded-xl bg-muted/40 border border-border/40 space-y-1">
                      <span className="block text-[10px] font-sans font-semibold text-muted-foreground uppercase">
                        {data.v1.version} Config
                      </span>
                      <pre className="text-[11px] text-foreground/90 whitespace-pre-wrap">
                        {JSON.stringify(data.v1.hyperparameters, null, 2)}
                      </pre>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-1">
                      <span className="block text-[10px] font-sans font-semibold text-emerald-500 uppercase">
                        Production ({data.v2.version}) Config
                      </span>
                      <pre className="text-[11px] text-foreground/90 whitespace-pre-wrap">
                        {JSON.stringify(data.v2.hyperparameters, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-border/40 pt-4 flex justify-end">
            <Button variant="outline" onClick={onClose} className="rounded-xl">
              Close Comparison
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

function ComparisonSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-24 rounded-2xl bg-muted/40" />
        <Skeleton className="h-24 rounded-2xl bg-muted/40" />
      </div>
      <Skeleton className="h-64 rounded-2xl bg-muted/40" />
      <Skeleton className="h-32 rounded-2xl bg-muted/40" />
    </div>
  );
}
