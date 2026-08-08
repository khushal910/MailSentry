import { cn } from "@/lib/utils";
import { ShieldAlert, ShieldCheck, Star, Tag, Users, Inbox, HelpCircle } from "lucide-react";

const LABEL_CONFIG: Record<
  string,
  {
    icon: React.ElementType;
    label: string;
    className: string;
  }
> = {
  spam: {
    icon: ShieldAlert,
    label: "Spam",
    className: "border-destructive/30 bg-destructive/10 text-destructive",
  },
  important: {
    icon: Star,
    label: "Important",
    className: "border-warning/30 bg-warning/10 text-warning",
  },
  promotions: {
    icon: Tag,
    label: "Promotions",
    className: "border-cyan/30 bg-cyan/10 text-cyan",
  },
  social: {
    icon: Users,
    label: "Social",
    className: "border-success/30 bg-success/10 text-success",
  },
  safe: {
    icon: ShieldCheck,
    label: "Safe",
    className: "border-success/30 bg-success/10 text-success",
  },
  inbox: {
    icon: ShieldCheck,
    label: "Safe",
    className: "border-success/30 bg-success/10 text-success",
  },
  ham: {
    icon: ShieldCheck,
    label: "Safe",
    className: "border-success/30 bg-success/10 text-success",
  },
};

interface EmailLabelBadgeProps {
  label: string;
  className?: string;
}

export function EmailLabelBadge({ label, className }: EmailLabelBadgeProps) {
  const key = label.toLowerCase();
  const config = LABEL_CONFIG[key] ?? {
    icon: HelpCircle,
    label: label.charAt(0).toUpperCase() + label.slice(1),
    className: "border-muted-foreground/30 bg-muted/30 text-muted-foreground",
  };

  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1.5 rounded-full border px-2.5 text-xs font-medium shrink-0 whitespace-nowrap",
        config.className,
        className,
      )}
    >

      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </span>
  );
}
