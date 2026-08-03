import { type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface InfoCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  delay?: number;
}

export function InfoCard({ label, value, icon: Icon, delay = 0 }: InfoCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay }}
      className="glass rounded-2xl p-4 border border-border/50 flex items-center gap-3.5 hover:border-brand/40 transition-colors"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-muted/60 text-brand">
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <span className="block text-xs text-muted-foreground font-medium uppercase tracking-wider">
          {label}
        </span>
        <span className="block text-sm font-semibold tracking-tight text-foreground truncate mt-0.5">
          {value}
        </span>
      </div>
    </motion.div>
  );
}
