import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  Scale,
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

  const formatMetricValue = (val: number, unit: string) => {
    if (unit === "%") {
      const pct = val <= 1.0 ? val * 100 : val;
      return `${pct.toFixed(2)}%`;
    }
    return `${val} ${unit}`;
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/75 backdrop-blur-md p-2 sm:p-4">
        {/* Backdrop overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0"
        />

        {/* Drawer container — High Contrast Design */}
        <motion.div
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 250 }}
          className="relative z-10 flex h-full max-h-[92vh] w-full max-w-2xl flex-col rounded-3xl border border-slate-700 bg-slate-950 p-6 shadow-2xl overflow-hidden subpixel-antialiased"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/20 text-brand">
                <Scale className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-black tracking-tight text-white">
                  Model Version Comparison
                </h2>
                <p className="text-xs text-slate-300 font-semibold mt-0.5">
                  Comparing <span className="font-bold text-brand">{targetVersion}</span> vs{" "}
                  <span className="font-bold text-emerald-400">Current Production</span>
                </p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="rounded-full text-slate-300 hover:text-white hover:bg-slate-800"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto py-4 space-y-6 pr-1 custom-scrollbar">
            {isLoading && <ComparisonSkeleton />}

            {error && (
              <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-5 text-center text-xs font-bold text-rose-300">
                {error}
              </div>
            )}

            {!isLoading && !error && data && (
              <>
                {/* Models Header Overview Cards */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Target Version Card (Selected) */}
                  <div className="rounded-2xl p-4 border border-slate-700/80 bg-slate-900/90 space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="border-slate-600 bg-slate-800/80 text-slate-200 text-xs font-bold">
                        Selected Version
                      </Badge>
                      <span className="text-xs font-black text-brand font-mono">{data.v1.version}</span>
                    </div>
                    <div>
                      <span className="block text-sm font-black text-white">
                        {data.v1.algorithm || data.v1.model_name}
                      </span>
                      <span className="block text-xs font-semibold text-slate-300 mt-0.5">
                        Dataset: {data.v1.dataset_version}
                      </span>
                    </div>
                  </div>

                  {/* Production Version Card */}
                  <div className="rounded-2xl p-4 border border-emerald-500/40 bg-emerald-950/40 space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge
                        variant="outline"
                        className="border-emerald-500/40 bg-emerald-500/20 text-emerald-400 text-xs font-extrabold"
                      >
                        ● Production
                      </Badge>
                      <span className="text-xs font-black text-emerald-400 font-mono">{data.v2.version}</span>
                    </div>
                    <div>
                      <span className="block text-sm font-black text-white">
                        {data.v2.algorithm || data.v2.model_name}
                      </span>
                      <span className="block text-xs font-semibold text-slate-300 mt-0.5">
                        Dataset: {data.v2.dataset_version}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Metrics Comparison Breakdown Table */}
                <div className="rounded-2xl border border-slate-800 overflow-hidden bg-slate-900/80">
                  <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 text-xs font-black text-white uppercase tracking-wider">
                    Performance Metric Differences
                  </div>

                  <div className="divide-y divide-slate-800">
                    {Object.entries(data.comparison).map(([key, item]) => {
                      const isImproved = item.status === "improved";
                      const isDecreased = item.status === "decreased";

                      const v1Formatted = formatMetricValue(item.v1_value, item.unit);
                      const v2Formatted = formatMetricValue(item.v2_value, item.unit);

                      return (
                        <div
                          key={key}
                          className="px-4 py-3.5 flex items-center justify-between hover:bg-slate-800/50 transition-colors text-xs"
                        >
                          <div className="w-1/3">
                            <span className="font-bold text-white text-xs">{item.label}</span>
                          </div>

                          {/* Values */}
                          <div className="flex items-center justify-center gap-3 w-1/3 text-center">
                            <span className="text-slate-300 font-semibold tabular-nums">
                              {v1Formatted}
                            </span>
                            <span className="text-slate-500">→</span>
                            <span className="font-extrabold text-white tabular-nums">
                              {v2Formatted}
                            </span>
                          </div>

                          {/* Delta Indicator */}
                          <div className="w-1/3 flex justify-end">
                            <span
                              className={cn(
                                "inline-flex items-center gap-1 font-black px-2.5 py-1 rounded-lg text-xs border tabular-nums shadow-xs",
                                isImproved &&
                                  "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
                                isDecreased &&
                                  "bg-rose-500/20 text-rose-400 border-rose-500/40",
                                !isImproved &&
                                  !isDecreased &&
                                  "bg-slate-800 text-slate-300 border-slate-700"
                              )}
                            >
                              {isImproved && <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />}
                              {isDecreased && <TrendingDown className="h-3.5 w-3.5 text-rose-400" />}
                              {!isImproved && !isDecreased && <Minus className="h-3.5 w-3.5 text-slate-400" />}
                              {item.diff > 0 ? `+${item.diff}` : item.diff}{item.unit === "%" ? "%" : ""}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Hyperparameters Comparison */}
                <div className="rounded-2xl border border-slate-800 p-4 space-y-3 bg-slate-900/80">
                  <div className="flex items-center gap-2 text-xs font-black text-white uppercase tracking-wider">
                    <Code2 className="h-4 w-4 text-brand" />
                    Hyperparameters Comparison
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <span className="block text-[10px] font-sans font-bold text-slate-400 uppercase">
                        {data.v1.version} Config
                      </span>
                      <pre className="text-[11px] text-slate-200 font-semibold whitespace-pre-wrap">
                        {JSON.stringify(data.v1.hyperparameters, null, 2)}
                      </pre>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 space-y-1">
                      <span className="block text-[10px] font-sans font-bold text-emerald-400 uppercase">
                        Production ({data.v2.version}) Config
                      </span>
                      <pre className="text-[11px] text-emerald-100 font-semibold whitespace-pre-wrap">
                        {JSON.stringify(data.v2.hyperparameters, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-slate-800 pt-4 flex justify-end">
            <Button variant="outline" onClick={onClose} className="rounded-xl border-slate-700 text-white hover:bg-slate-800 font-bold text-xs">
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
        <Skeleton className="h-24 rounded-2xl bg-slate-800/50" />
        <Skeleton className="h-24 rounded-2xl bg-slate-800/50" />
      </div>
      <Skeleton className="h-64 rounded-2xl bg-slate-800/50" />
      <Skeleton className="h-32 rounded-2xl bg-slate-800/50" />
    </div>
  );
}
