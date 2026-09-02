import { Link, useRouterState } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Sparkles, ArrowRight } from "lucide-react";
import { useClassification } from "@/context/ClassificationContext";

export function GlobalClassificationIndicator() {
  const { isClassifying, jobProgress } = useClassification();
  const routerState = useRouterState();
  const currentPath = routerState.location.pathname;

  // Don't render the floating indicator if already on the auto-classifier page
  const isOnAutoClassifierPage = currentPath === "/dashboard/auto-classifier";

  if (!isClassifying || !jobProgress || isOnAutoClassifierPage) {
    return null;
  }

  const processed = jobProgress.processed;
  const total = Math.max(1, jobProgress.total);
  const percent = Math.min(100, Math.round((processed / total) * 100));

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 30, scale: 0.95 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3.5 rounded-2xl border border-brand/30 bg-card/95 px-4 py-3 shadow-2xl backdrop-blur-md"
      >
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
          <Loader2 className="h-5 w-5 animate-spin text-brand" />
          <Sparkles className="absolute -right-1 -top-1 h-3.5 w-3.5 text-brand" />
        </div>

        <div className="flex flex-col gap-1 min-w-[170px]">
          <div className="flex items-center justify-between text-xs font-semibold text-foreground">
            <span>Classifying Emails…</span>
            <span className="text-brand font-mono">{percent}%</span>
          </div>

          {/* Mini progress bar */}
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/60">
            <motion.div
              className="h-full bg-gradient-to-r from-brand to-cyan-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${percent}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>
              {processed} of {total}
            </span>
            {jobProgress.estRemainingSec > 0 && (
              <span>~{jobProgress.estRemainingSec}s left</span>
            )}
          </div>
        </div>

        <Link
          to="/dashboard/auto-classifier"
          className="ml-1 flex h-8 items-center gap-1 rounded-lg bg-secondary px-2.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-brand hover:text-white"
        >
          <span>View</span>
          <ArrowRight className="h-3 w-3" />
        </Link>
      </motion.div>
    </AnimatePresence>
  );
}
