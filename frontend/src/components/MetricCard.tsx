import { type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  description: string;
  accentColor?: string;
  delay?: number;
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  accentColor = "text-brand",
  delay = 0,
}: MetricCardProps) {
  const formattedPercentage = `${value.toFixed(2)}%`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="glass-strong relative overflow-hidden rounded-2xl p-5 border border-border/60 shadow-soft hover:shadow-elegant transition-all duration-300 group"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 shadow-sm transition-transform duration-300 group-hover:scale-110",
            accentColor
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-3">
        <div className="text-3xl font-bold tracking-tight text-foreground">
          {formattedPercentage}
        </div>
        <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
          {description}
        </p>
      </div>

      {/* Ambient background glow */}
      <div className="pointer-events-none absolute -bottom-6 -right-6 h-20 w-20 rounded-full bg-brand/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    </motion.div>
  );
}
