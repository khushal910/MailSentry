import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface VerticalMetricItem {
  label: string;
  value: number;
  description: string;
  gradient: string;
  badgeBg: string;
  textColor: string;
}

interface VerticalPerformanceChartProps {
  metrics: VerticalMetricItem[];
}

export function VerticalPerformanceChart({ metrics }: VerticalPerformanceChartProps) {
  return (
    <div className="pt-8 pb-2">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 md:gap-8 items-end h-64">
        {metrics.map((m, idx) => {
          const percentage = Math.min(100, Math.max(0, m.value));
          return (
            <div
              key={m.label}
              className="group relative flex flex-col items-center h-full justify-end"
            >
              {/* Floating Interactive Hover Tooltip */}
              <div className="absolute -top-14 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 group-hover:-top-16 transition-all duration-300 pointer-events-none z-30 whitespace-nowrap bg-popover text-popover-foreground text-xs font-semibold px-3.5 py-2 rounded-xl shadow-elegant border border-border/70 flex flex-col items-center gap-0.5">
                <span className="font-bold text-foreground">
                  {m.label}: {percentage.toFixed(2)}%
                </span>
                <span className="text-[10px] text-muted-foreground font-normal">
                  {m.description}
                </span>
              </div>

              {/* Vertical Track & Animated Bar */}
              <div className="relative w-full max-w-[96px] h-full rounded-2xl bg-muted/40 p-1.5 border border-border/40 flex items-end overflow-visible group-hover:border-brand/60 group-hover:bg-muted/60 transition-all duration-300 shadow-inner">
                <motion.div
                  initial={{ height: "0%" }}
                  animate={{ height: `${percentage}%` }}
                  transition={{ duration: 0.9, delay: idx * 0.12, ease: "easeOut" }}
                  className={cn(
                    "w-full rounded-xl shadow-soft relative overflow-hidden group-hover:brightness-110 transition-all duration-300",
                    m.gradient
                  )}
                >
                  {/* Subtle shine overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/10 to-white/25 pointer-events-none" />

                  {/* Percentage value inside bar top */}
                  <div className="absolute top-2 left-1/2 -translate-x-1/2 text-[11px] font-extrabold text-white tracking-tight drop-shadow-sm opacity-90 group-hover:scale-110 transition-transform">
                    {percentage.toFixed(1)}%
                  </div>
                </motion.div>
              </div>

              {/* Label & Score Badge below bar */}
              <div className="mt-3 text-center space-y-0.5">
                <span className="block text-xs font-bold tracking-tight text-foreground group-hover:text-brand transition-colors">
                  {m.label}
                </span>
                <span
                  className={cn(
                    "inline-block text-[11px] font-bold px-2 py-0.5 rounded-md border border-border/30 shadow-xs",
                    m.badgeBg,
                    m.textColor
                  )}
                >
                  {percentage.toFixed(2)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* Backward compatible export if needed */
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
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-foreground tracking-tight">{label}</span>
        <span className="font-bold text-brand">{percentage.toFixed(2)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted/60 p-0.5 border border-border/40">
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
