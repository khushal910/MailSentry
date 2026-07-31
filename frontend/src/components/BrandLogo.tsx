import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

interface BrandLogoProps {
  className?: string;
  showText?: boolean;
}

export function BrandLogo({ className, showText = true }: BrandLogoProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-brand shadow-elegant">
        <ShieldCheck className="h-4 w-4 text-primary-foreground" strokeWidth={2.5} />
      </div>
      {showText && (
        <span className="text-base font-semibold tracking-tight text-foreground">
          MailSentry
        </span>
      )}
    </div>
  );
}
