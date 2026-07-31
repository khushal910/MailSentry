import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoaderProps {
  className?: string;
  label?: string;
  size?: number;
}

export function Loader({ className, label, size = 20 }: LoaderProps) {
  return (
    <div className={cn("inline-flex items-center gap-2 text-muted-foreground", className)}>
      <Loader2 className="animate-spin" style={{ width: size, height: size }} />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
