import { cn } from "@/lib/utils";
import { ShieldAlert, ShieldCheck } from "lucide-react";

interface PredictionBadgeProps {
  prediction: "Spam" | "Ham";
  className?: string;
}

export function PredictionBadge({ prediction, className }: PredictionBadgeProps) {
  const isSpam = prediction === "Spam";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        isSpam
          ? "border-destructive/30 bg-destructive/10 text-destructive"
          : "border-success/30 bg-success/10 text-success",
        className,
      )}
    >
      {isSpam ? (
        <ShieldAlert className="h-3.5 w-3.5" />
      ) : (
        <ShieldCheck className="h-3.5 w-3.5" />
      )}
      {isSpam ? "Spam" : "Safe"}
    </span>
  );
}
