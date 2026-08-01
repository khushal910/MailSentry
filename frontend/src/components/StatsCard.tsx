import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  accent?: "brand" | "success" | "destructive" | "cyan";
  className?: string;
}

const accentClasses: Record<NonNullable<StatsCardProps["accent"]>, string> = {
  brand: "text-brand bg-brand/10 border-brand/20 shadow-[0_0_15px_-3px_rgba(79,70,229,0.3)]",
  success: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20 shadow-[0_0_15px_-3px_rgba(16,185,129,0.3)]",
  destructive: "text-rose-500 bg-rose-500/10 border-rose-500/20 shadow-[0_0_15px_-3px_rgba(244,63,94,0.3)]",
  cyan: "text-cyan bg-cyan/10 border-cyan/20 shadow-[0_0_15px_-3px_rgba(6,182,212,0.3)]",
};

export function StatsCard({
  label,
  value,
  icon: Icon,
  trend,
  accent = "brand",
  className,
}: StatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3, scale: 1.01 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "glass glow-card-hover rounded-2xl p-5 shadow-soft border border-border/50 bg-card/60 backdrop-blur-xl",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {label}
          </p>
          <p className="mt-2 text-2xl font-bold tracking-tight text-foreground">
            {value}
          </p>
          {trend && <p className="mt-1.5 text-xs font-medium text-muted-foreground">{trend}</p>}
        </div>
        <span
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl border transition-all duration-300",
            accentClasses[accent],
          )}
        >
          <Icon className="h-5 w-5" />
        </span>
      </div>
    </motion.div>
  );
}
