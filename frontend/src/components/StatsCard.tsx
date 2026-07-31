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
  brand: "text-brand bg-brand/10 border-brand/20",
  success: "text-success bg-success/10 border-success/20",
  destructive: "text-destructive bg-destructive/10 border-destructive/20",
  cyan: "text-cyan bg-cyan/10 border-cyan/20",
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn(
        "glass rounded-xl p-5 shadow-soft transition-all hover:shadow-elegant",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {label}
          </p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
            {value}
          </p>
          {trend && <p className="mt-1 text-xs text-muted-foreground">{trend}</p>}
        </div>
        <span
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg border",
            accentClasses[accent],
          )}
        >
          <Icon className="h-4 w-4" />
        </span>
      </div>
    </motion.div>
  );
}
