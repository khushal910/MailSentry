import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, ShieldCheck, Sparkles } from "lucide-react";
import type { PredictionResponse } from "@/services/predictionApi";
import { formatConfidence } from "@/utils/format";
import { cn } from "@/lib/utils";

interface ResultCardProps {
  result: PredictionResponse | null;
  className?: string;
}

export function ResultCard({ result, className }: ResultCardProps) {
  if (!result) return null;

  const isSpam = String(result.prediction || "").toLowerCase() === "spam";
  const confValue = typeof result.confidence === "number" ? result.confidence : 0.85;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={`${result.prediction}-${confValue}`}
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -8, scale: 0.98 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className={cn(
          "glass-strong relative overflow-hidden rounded-2xl p-6 shadow-elegant",
          isSpam ? "border-destructive/30" : "border-success/30",
          className,
        )}
      >
        <div
          className={cn(
            "absolute inset-x-0 top-0 h-1",
            isSpam
              ? "bg-gradient-to-r from-destructive/60 to-destructive"
              : "bg-gradient-to-r from-success/60 to-success",
          )}
        />
        <div className="flex items-start gap-4">
          <motion.span
            initial={{ scale: 0.6, rotate: -8 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 18 }}
            className={cn(
              "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border",
              isSpam
                ? "border-destructive/40 bg-destructive/15 text-destructive"
                : "border-success/40 bg-success/15 text-success",
            )}
          >
            {isSpam ? <ShieldAlert className="h-6 w-6" /> : <ShieldCheck className="h-6 w-6" />}
          </motion.span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold tracking-tight">
                {isSpam ? "Spam Email" : "Safe Email"}
              </h3>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {formatConfidence(confValue)} confidence
              </span>
            </div>
            <p className="mt-2 flex items-start gap-1.5 text-sm text-muted-foreground">
              <Sparkles className="mt-0.5 h-3.5 w-3.5 text-brand" />
              <span>{result.reason || (isSpam ? "Flagged as Spam" : "Verified Safe Email")}</span>
            </p>
            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${Math.min(100, confValue <= 1 ? confValue * 100 : confValue)}%`,
                }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className={cn("h-full rounded-full", isSpam ? "bg-destructive" : "bg-success")}
              />
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
