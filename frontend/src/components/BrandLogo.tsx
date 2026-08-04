import { cn } from "@/lib/utils";

interface BrandLogoProps {
  className?: string;
  showText?: boolean;
}

export function BrandLogo({ className, showText = true }: BrandLogoProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border/30 shadow-sm">
        <img src="/favicon.ico" alt="MailSentry Logo" className="h-full w-full object-cover" />
      </div>
      {showText && (
        <span className="text-base font-semibold tracking-tight text-foreground">MailSentry</span>
      )}
    </div>
  );
}
