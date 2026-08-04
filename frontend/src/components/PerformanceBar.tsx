import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight, Minus, Trophy, Scale } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DualMetricItem {
  label: string;
  currentValue: number;
  previousValue?: number;
  currentVersionTag?: string;
  previousVersionTag?: string;
  description: string;
}

interface VerticalPerformanceChartProps {
  metrics: DualMetricItem[];
  currentVersionTag?: string;
  previousVersionTag?: string;
}

const getNormalizedVal = (val?: number) => {
  if (val === undefined || val === null) return 0;
  return val <= 1.0 ? val * 100 : val;
};

export function VerticalPerformanceChart({
  metrics,
  currentVersionTag = "Current (Prod)",
  previousVersionTag = "Previous",
}: VerticalPerformanceChartProps) {
  return (
    <div className="pt-10 pb-4">
      {/* Chart Legend */}
      <div className="flex flex-wrap items-center justify-end gap-6 mb-6 text-xs font-extrabold">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-gradient-to-tr from-slate-600 to-indigo-500 border border-slate-400 shadow-sm" />
          <span className="text-slate-300">{previousVersionTag} Model</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-300 border border-emerald-400 shadow-sm" />
          <span className="text-emerald-400">{currentVersionTag} Production Model</span>
        </div>
      </div>

      {/* Main Dual Bars Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 items-end h-72">
        {metrics.map((m, idx) => {
          const currVal = getNormalizedVal(m.currentValue);
          const prevVal = getNormalizedVal(m.previousValue);
          const hasPrev = m.previousValue !== undefined && m.previousValue !== null;

          const diff = currVal - prevVal;
          const isCurrentBetter = diff > 0.01;
          const isPrevBetter = diff < -0.01;

          return (
            <div
              key={m.label}
              className="group relative flex flex-col items-center h-full justify-end bg-slate-900/60 p-4 rounded-3xl border border-slate-800 hover:border-slate-700 transition-all duration-300"
            >
              {/* Floating Interactive Mouse Tooltip */}
              <div className="absolute -top-20 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 group-hover:-top-24 transition-all duration-300 pointer-events-none z-30 whitespace-nowrap bg-slate-950 text-white text-xs font-bold px-4 py-3 rounded-2xl shadow-2xl border border-slate-700 flex flex-col items-center gap-1.5 subpixel-antialiased">
                <div className="flex items-center gap-2 border-b border-slate-800 pb-1 w-full justify-between">
                  <span className="font-extrabold text-white">{m.label} Comparison</span>
                  {isCurrentBetter ? (
                    <span className="text-[10px] font-black text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Trophy className="h-3 w-3 text-emerald-400" /> Current Wins (+
                      {diff.toFixed(2)}%)
                    </span>
                  ) : isPrevBetter ? (
                    <span className="text-[10px] font-black text-indigo-400 bg-indigo-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Scale className="h-3 w-3 text-indigo-400" /> Previous Higher (
                      {diff.toFixed(2)}%)
                    </span>
                  ) : (
                    <span className="text-[10px] font-black text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
                      Equal Performance
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4 text-[11px] font-mono pt-0.5">
                  <span className="text-slate-300">
                    {previousVersionTag}:{" "}
                    <strong className="text-indigo-300">{prevVal.toFixed(2)}%</strong>
                  </span>
                  <span className="text-slate-500">vs</span>
                  <span className="text-emerald-400">
                    {currentVersionTag}:{" "}
                    <strong className="text-emerald-300">{currVal.toFixed(2)}%</strong>
                  </span>
                </div>
              </div>

              {/* Dual Vertical Tracks Container */}
              <div className="relative w-full h-full rounded-2xl bg-slate-950 p-2 border border-slate-800/80 flex items-end justify-center gap-3 overflow-visible shadow-inner">
                {/* Bar 1: Previous Version (if present) */}
                {hasPrev && (
                  <div className="relative w-1/2 h-full flex items-end justify-center">
                    <motion.div
                      initial={{ height: "0%" }}
                      animate={{ height: `${prevVal}%` }}
                      transition={{ duration: 0.9, delay: idx * 0.1, ease: "easeOut" }}
                      className="w-full max-w-[36px] rounded-xl shadow-soft relative overflow-hidden bg-gradient-to-t from-slate-800 via-indigo-600 to-indigo-400 hover:brightness-125 transition-all duration-300"
                    >
                      <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/10 to-white/20 pointer-events-none" />
                      <div className="absolute top-1 left-1/2 -translate-x-1/2 text-[10px] font-black text-indigo-100 tracking-tight drop-shadow-md opacity-90 font-mono">
                        {prevVal.toFixed(1)}%
                      </div>
                    </motion.div>
                  </div>
                )}

                {/* Bar 2: Current Production Version */}
                <div className="relative w-1/2 h-full flex items-end justify-center">
                  <motion.div
                    initial={{ height: "0%" }}
                    animate={{ height: `${currVal}%` }}
                    transition={{ duration: 0.9, delay: idx * 0.12 + 0.1, ease: "easeOut" }}
                    className="w-full max-w-[36px] rounded-xl shadow-soft relative overflow-hidden bg-gradient-to-t from-emerald-700 via-emerald-500 to-teal-300 hover:brightness-125 transition-all duration-300 border border-emerald-400/40"
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/15 to-white/30 pointer-events-none" />
                    <div className="absolute top-1 left-1/2 -translate-x-1/2 text-[10px] font-black text-white tracking-tight drop-shadow-md font-mono">
                      {currVal.toFixed(1)}%
                    </div>
                  </motion.div>
                </div>
              </div>

              {/* Label & Dynamic Metric Badges below bars */}
              <div className="mt-3 text-center space-y-1 w-full">
                <span className="block text-xs font-black tracking-tight text-white group-hover:text-brand transition-colors">
                  {m.label}
                </span>

                <div className="flex items-center justify-center gap-1.5 font-mono text-[10px]">
                  {hasPrev && (
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 font-semibold">
                      {prevVal.toFixed(1)}%
                    </span>
                  )}
                  <span className="text-slate-500">→</span>
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-black">
                    {currVal.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* Backward compatible export */
export function PerformanceBar({
  label,
  value,
  colorClass = "bg-gradient-brand",
  delay = 0,
}: {
  label: string;
  value: number;
  colorClass?: string;
  delay?: number;
}) {
  const percentage = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs font-bold text-white">
        <span>{label}</span>
        <span className="font-extrabold text-brand font-mono">{percentage.toFixed(2)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-900 p-0.5 border border-slate-800">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, delay, ease: "easeOut" }}
          className={`h-full rounded-full ${colorClass} shadow-soft`}
        />
      </div>
    </div>
  );
}
