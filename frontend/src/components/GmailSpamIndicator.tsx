import React from "react";
import { AlertTriangle } from "lucide-react";
import { EmailLabelBadge } from "@/components/EmailLabelBadge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { GmailClassification } from "@/services/emailsApi";

interface GmailSpamIndicatorProps {
  mailsentryLabel: string;
  gmailClassification?: GmailClassification | null;
  className?: string;
  showMailSentryBadge?: boolean;
}

export function GmailSpamIndicator({
  mailsentryLabel,
  gmailClassification,
  className,
  showMailSentryBadge = true,
}: GmailSpamIndicatorProps) {
  const mailsentryIsSpam = mailsentryLabel.toLowerCase() === "spam";
  const gmailIsSpam = Boolean(gmailClassification?.is_spam);
  const classificationsDiffer = Boolean(gmailIsSpam) !== Boolean(mailsentryIsSpam);

  // If classifications AGREE: show only the clean MailSentry prediction badge
  if (!classificationsDiffer) {
    return showMailSentryBadge ? (
      <div
        className={cn(
          "inline-flex items-center gap-2 shrink-0 whitespace-nowrap align-middle",
          className
        )}
      >
        <EmailLabelBadge label={mailsentryLabel} />
      </div>
    ) : null;
  }

  // If classifications DISAGREE: show MailSentry badge + colored ⚠ warning icon
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 shrink-0 whitespace-nowrap align-middle",
        className
      )}
      onClick={(e) => e.stopPropagation()}
    >
      {showMailSentryBadge && <EmailLabelBadge label={mailsentryLabel} />}

      <TooltipProvider delayDuration={150}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              tabIndex={0}
              role="note"
              aria-label="Gmail and MailSentry classifications differ"
              className="inline-flex h-6 items-center justify-center gap-1 rounded-md px-2 text-xs font-bold tracking-tight transition-all border cursor-help select-none shrink-0 whitespace-nowrap shadow-2xs bg-amber-500/15 border-amber-500/40 text-amber-500 hover:bg-amber-500/25 animate-pulse"
            >
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            </span>
          </TooltipTrigger>

          <TooltipContent
            side="top"
            align="center"
            className="z-50 bg-popover text-popover-foreground border border-border shadow-xl rounded-xl p-3 max-w-xs space-y-2 text-xs font-sans"
          >
            {/* Header */}
            <div className="flex items-center justify-between gap-3 border-b border-border/60 pb-2">
              <span className="flex items-center gap-1.5 font-bold text-foreground">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                Classification Disagreement
              </span>
              <span className="text-[10px] bg-amber-500/15 text-amber-500 font-bold px-2 py-0.5 rounded border border-amber-500/30">
                ⚠ Differ
              </span>
            </div>

            {/* Detailed Body */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between font-medium">
                <span className="text-muted-foreground">MailSentry AI:</span>
                <span
                  className={
                    mailsentryIsSpam
                      ? "text-destructive font-bold"
                      : "text-emerald-500 font-bold"
                  }
                >
                  {mailsentryIsSpam ? "🔴 Spam" : "🟢 Safe"}
                </span>
              </div>
              <div className="flex items-center justify-between font-medium">
                <span className="text-muted-foreground">Gmail Status:</span>
                <span
                  className={
                    gmailIsSpam
                      ? "text-destructive font-bold"
                      : "text-emerald-500 font-bold"
                  }
                >
                  {gmailIsSpam ? "🔴 Spam" : "🟢 Not Spam (Inbox)"}
                </span>
              </div>
              <p className="text-[10px] text-amber-400 font-semibold pt-1 border-t border-border/40">
                ⚠ Gmail and MailSentry predicted differently for this email
              </p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}
