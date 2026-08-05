import React, { useEffect, useState } from "react";
import {
  Sparkles,
  ArrowLeft,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  Clock,
  CheckCircle2,
  Calendar,
  CheckSquare,
  MessageSquare,
  Mail,
  User,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmailLabelBadge } from "@/components/EmailLabelBadge";
import { emailSummaryService, type EmailSummaryData } from "@/services/emailSummaryService";
import { formatConfidence, formatDate } from "@/utils/format";
import { getGmailUrl, openGmailInNewTab } from "@/utils/gmail";

interface EmailSummaryPageViewProps {
  emailId: string;
  onBack?: () => void;
}

export const EmailSummaryPageView: React.FC<EmailSummaryPageViewProps> = ({
  emailId,
  onBack,
}) => {
  const [data, setData] = useState<EmailSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showRegenerateTooltip, setShowRegenerateTooltip] = useState(false);

  const fetchSummary = async () => {
    if (!emailId || !emailId.trim()) {
      setError("Invalid Email ID provided.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Call GET /emails/{email_id}/summary using Axios service
      const res = await emailSummaryService.getEmailSummary(emailId.trim());
      setData(res);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to fetch email summary. The email ID may be invalid or missing.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [emailId]);

  // Helper to extract structured items (Purpose, Dates, Actions, Tone) from summary text
  const parseSummarySections = (rawSummary: string) => {
    if (!rawSummary) return { mainText: "", purpose: "", dates: "", actions: "", tone: "" };

    const lines = rawSummary.split("\n").map((l) => l.trim()).filter(Boolean);
    let purpose = "";
    let dates = "";
    let actions = "";
    let tone = "";
    const cleanLines: string[] = [];

    lines.forEach((line) => {
      const lower = line.toLowerCase();
      if (lower.startsWith("purpose:") || lower.startsWith("- purpose:")) {
        purpose = line.replace(/^[-*]?\s*purpose:\s*/i, "");
      } else if (lower.startsWith("important dates:") || lower.startsWith("- important dates:")) {
        dates = line.replace(/^[-*]?\s*important dates:\s*/i, "");
      } else if (lower.startsWith("required actions:") || lower.startsWith("- required actions:")) {
        actions = line.replace(/^[-*]?\s*required actions:\s*/i, "");
      } else if (lower.startsWith("deadlines:") || lower.startsWith("- deadlines:")) {
        const dl = line.replace(/^[-*]?\s*deadlines:\s*/i, "");
        if (dl && dl.toLowerCase() !== "none" && dl.toLowerCase() !== "n/a") {
          dates = dates ? `${dates} | Deadline: ${dl}` : `Deadline: ${dl}`;
        }
      } else if (lower.startsWith("tone:") || lower.startsWith("- tone:")) {
        tone = line.replace(/^[-*]?\s*tone:\s*/i, "");
      } else {
        cleanLines.push(line);
      }
    });

    return {
      mainText: cleanLines.join("\n") || rawSummary,
      purpose,
      dates,
      actions,
      tone,
    };
  };

  const handleBackNavigation = () => {
    if (onBack) {
      onBack();
    } else if (typeof window !== "undefined") {
      window.history.back();
    }
  };

  const parsed = data ? parseSummarySections(data.summary) : null;
  const gmailUrl = data ? getGmailUrl(data.message_id, data.thread_id) : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-12 animate-in fade-in duration-300">
      {/* Navigation & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBackNavigation}
          className="gap-2 bg-background/50 border-border/60 hover:bg-muted"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to History
        </Button>

        <div className="flex items-center gap-3">
          {gmailUrl && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => openGmailInNewTab(gmailUrl)}
              className="gap-2 border-primary/30 text-primary hover:bg-primary/10"
            >
              <ExternalLink className="h-4 w-4" />
              View Original Email
            </Button>
          )}

          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowRegenerateTooltip(!showRegenerateTooltip)}
              onMouseEnter={() => setShowRegenerateTooltip(true)}
              onMouseLeave={() => setShowRegenerateTooltip(false)}
              className="gap-2 text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className="h-4 w-4" />
              Regenerate Summary
            </Button>

            {showRegenerateTooltip && (
              <div className="absolute right-0 top-10 z-20 w-64 rounded-xl border border-border/80 bg-popover p-3 text-xs shadow-xl text-popover-foreground animate-in fade-in zoom-in-95">
                <p className="font-semibold text-primary flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5" /> Future Feature
                </p>
                <p className="mt-1 text-muted-foreground">
                  Summaries are cached in MongoDB to eliminate redundant API costs. Force re-summarize will be enabled in v2.0.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SKELETON LOADERS WHILE LOADING */}
      {isLoading && (
        <div className="space-y-6">
          {/* Top Card Skeleton */}
          <div className="glass rounded-2xl p-6 md:p-8 space-y-4 animate-pulse">
            <div className="flex items-center justify-between gap-4">
              <div className="h-6 w-24 rounded-full bg-muted/60" />
              <div className="h-4 w-32 rounded bg-muted/40" />
            </div>
            <div className="h-8 w-3/4 rounded-lg bg-muted/70" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="h-5 w-48 rounded bg-muted/50" />
              <div className="h-5 w-48 rounded bg-muted/50" />
            </div>
          </div>

          {/* Summary Card Skeleton */}
          <div className="glass rounded-2xl p-6 md:p-8 space-y-4 animate-pulse">
            <div className="flex items-center justify-between pb-2">
              <div className="h-6 w-40 rounded-lg bg-muted/60" />
              <div className="h-5 w-28 rounded-full bg-muted/40" />
            </div>
            <div className="space-y-2">
              <div className="h-4 w-full rounded bg-muted/50" />
              <div className="h-4 w-5/6 rounded bg-muted/50" />
              <div className="h-4 w-4/6 rounded bg-muted/50" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
              <div className="h-20 rounded-xl bg-muted/30" />
              <div className="h-20 rounded-xl bg-muted/30" />
              <div className="h-20 rounded-xl bg-muted/30" />
            </div>
          </div>
        </div>
      )}

      {/* ERROR STATE / INVALID EMAIL ID */}
      {!isLoading && error && (
        <div className="glass rounded-2xl p-8 text-center space-y-4 border-destructive/30">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
            <AlertCircle className="h-7 w-7" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Email Summary Not Available</h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-md mx-auto">{error}</p>
          </div>
          <div className="flex justify-center gap-3 pt-2">
            <Button variant="outline" onClick={fetchSummary} className="gap-2">
              <RefreshCw className="h-4 w-4" /> Try Again
            </Button>
            <Button onClick={handleBackNavigation}>Back to History</Button>
          </div>
        </div>
      )}

      {/* CONTENT WHEN FINISHED LOADING */}
      {!isLoading && !error && data && (
        <>
          {/* TOP CARD: Email Metadata */}
          <div className="glass rounded-2xl p-6 md:p-8 border border-border/60 shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-4">
              <div className="flex items-center gap-2.5">
                <EmailLabelBadge label={data.predicted_label || "ham"} />
                {typeof data.predicted_score === "number" && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-full border border-border/50">
                    <ShieldCheck className="h-3.5 w-3.5 text-brand" />
                    {formatConfidence(data.predicted_score)} confidence
                  </span>
                )}
              </div>
              {data.sent_at && (
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                  {formatDate(data.sent_at)}
                </span>
              )}
            </div>

            <h1 className="mt-4 text-xl md:text-2xl font-bold tracking-tight text-foreground leading-snug">
              {data.subject || "(No Subject)"}
            </h1>

            <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-medium text-muted-foreground bg-muted/20 rounded-xl p-3.5 border border-border/40">
              <div className="flex items-center gap-2 min-w-0">
                <User className="h-4 w-4 shrink-0 text-primary" />
                <span className="truncate">
                  <strong className="text-foreground">From:</strong> {data.sender || "Unknown Sender"}
                </span>
              </div>
              <div className="flex items-center gap-2 min-w-0">
                <Mail className="h-4 w-4 shrink-0 text-primary" />
                <span className="truncate">
                  <strong className="text-foreground">To:</strong> {data.receiver || "Authenticated User"}
                </span>
              </div>
            </div>
          </div>

          {/* SUMMARY CARD: AI Generated Summary */}
          <div className="glass rounded-2xl p-6 md:p-8 border border-primary/25 bg-primary/5 shadow-xl relative overflow-hidden">
            {/* Subtle Gradient Accent Background */}
            <div className="absolute top-0 right-0 -mt-8 -mr-8 h-32 w-32 rounded-full bg-primary/10 blur-2xl pointer-events-none" />

            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-primary/15 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/15 text-primary">
                  <Sparkles className="h-4 w-4 animate-pulse" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-foreground">Executive AI Summary</h2>
                  <p className="text-[11px] text-muted-foreground">Powered by Google Gemini 2.5 Flash</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {data.cached ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-muted/80 px-3 py-1 text-xs font-medium text-muted-foreground border border-border/50 shadow-sm">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                    Cached in Database
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 px-3 py-1 text-xs font-medium border border-emerald-500/30 shadow-sm">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Generated via Gemini API
                  </span>
                )}
              </div>
            </div>

            {/* AI Summary Text */}
            <div className="mt-5 text-sm md:text-base leading-relaxed text-foreground font-normal whitespace-pre-line">
              {parsed?.mainText}
            </div>

            {/* Key Structured Insights Cards */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              {/* Action Items */}
              <div className="rounded-xl border border-border/50 bg-background/60 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                  <CheckSquare className="h-4 w-4" />
                  Action Items
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {parsed?.actions || "No specific action items explicitly requested in body."}
                </p>
              </div>

              {/* Important Dates & Deadlines */}
              <div className="rounded-xl border border-border/50 bg-background/60 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-500">
                  <Calendar className="h-4 w-4" />
                  Important Dates & Deadlines
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {parsed?.dates || "No specific dates or deadlines extracted."}
                </p>
              </div>

              {/* Email Tone */}
              <div className="rounded-xl border border-border/50 bg-background/60 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-semibold text-indigo-500">
                  <MessageSquare className="h-4 w-4" />
                  Email Tone
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed capitalize">
                  {parsed?.tone || "Professional / Informational"}
                </p>
              </div>
            </div>
          </div>

          {/* ORIGINAL EMAIL CONTENT PREVIEW */}
          <div className="glass rounded-2xl p-6 border border-border/50 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Mail className="h-3.5 w-3.5" />
              Full Email Body Preview
            </h3>
            <div className="rounded-xl border border-border/40 bg-muted/20 p-4 text-xs font-mono leading-relaxed text-muted-foreground max-h-60 overflow-y-auto whitespace-pre-wrap">
              {data.body || "(No text body available for preview)"}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default EmailSummaryPageView;
