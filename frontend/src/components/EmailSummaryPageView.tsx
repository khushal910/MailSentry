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
  Target,
  Tag,
  Inbox,
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
      // Strip leading bullet markers (*, -, •, 1.) and bold markdown asterisks (**)
      const strippedLine = line
        .replace(/^[-*•\d.]+\s*/, "")
        .replace(/\*\*/g, "")
        .trim();
      const lower = strippedLine.toLowerCase();

      if (lower.startsWith("purpose:")) {
        purpose = strippedLine.replace(/^purpose:\s*/i, "").trim();
      } else if (lower.startsWith("important dates:") || lower.startsWith("dates:")) {
        dates = strippedLine.replace(/^(important\s+)?dates:\s*/i, "").trim();
      } else if (
        lower.startsWith("required actions:") ||
        lower.startsWith("actions:") ||
        lower.startsWith("action items:")
      ) {
        actions = strippedLine.replace(/^(required\s+)?actions?( items)?:\s*/i, "").trim();
      } else if (lower.startsWith("deadlines:") || lower.startsWith("deadline:")) {
        const dl = strippedLine.replace(/^deadlines?:\s*/i, "").trim();
        if (dl && dl.toLowerCase() !== "none" && dl.toLowerCase() !== "n/a") {
          dates = dates ? `${dates} | Deadline: ${dl}` : `Deadline: ${dl}`;
        }
      } else if (lower.startsWith("tone:")) {
        tone = strippedLine.replace(/^tone:\s*/i, "").trim();
      } else {
        // Keep in main text summary body (cleaning outer asterisks for clean display)
        cleanLines.push(line.replace(/\*\*/g, ""));
      }
    });

    return {
      mainText: cleanLines.join("\n") || rawSummary.replace(/\*\*/g, ""),
      purpose: purpose.replace(/\*\*/g, ""),
      dates: dates.replace(/\*\*/g, ""),
      actions: actions.replace(/\*\*/g, ""),
      tone: tone.replace(/\*\*/g, ""),
    };
  };

  const handleBackNavigation = () => {
    if (onBack) {
      onBack();
    } else if (typeof window !== "undefined") {
      window.history.back();
    }
  };

  const formatDisplayEmail = (rawVal?: string, fallback = "Unknown") => {
    if (!rawVal) return fallback;
    const s = String(rawVal).trim();
    if (/^[0-9a-fA-F]{24}$/.test(s)) return fallback;
    return s;
  };

  const parsed = data ? parseSummarySections(data.summary) : null;
  const gmailUrl = data ? getGmailUrl(data.message_id, data.thread_id) : null;
  const displaySender = formatDisplayEmail(data?.sender, "Unknown Sender");
  const displayReceiver = formatDisplayEmail(data?.receiver, "Authenticated User");

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-12 animate-in fade-in duration-300">
      {/* Navigation & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/40 pb-4">
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
          {/* Main Summary Skeleton */}
          <div className="glass rounded-2xl p-6 md:p-8 space-y-4 animate-pulse border-2 border-primary/20">
            <div className="flex items-center justify-between pb-2">
              <div className="h-7 w-48 rounded-lg bg-primary/20" />
              <div className="h-6 w-32 rounded-full bg-muted/40" />
            </div>
            <div className="space-y-2">
              <div className="h-5 w-full rounded bg-primary/10" />
              <div className="h-5 w-5/6 rounded bg-primary/10" />
              <div className="h-5 w-4/6 rounded bg-primary/10" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-4">
              <div className="h-20 rounded-xl bg-muted/30" />
              <div className="h-20 rounded-xl bg-muted/30" />
              <div className="h-20 rounded-xl bg-muted/30" />
              <div className="h-20 rounded-xl bg-muted/30" />
            </div>
          </div>

          {/* Metadata Skeleton */}
          <div className="glass rounded-2xl p-6 md:p-8 space-y-4 animate-pulse">
            <div className="flex items-center justify-between gap-4">
              <div className="h-6 w-24 rounded-full bg-muted/60" />
              <div className="h-4 w-32 rounded bg-muted/40" />
            </div>
            <div className="h-8 w-3/4 rounded-lg bg-muted/70" />
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
          {/* PROMINENT HIGHLIGHTED AI EXECUTIVE SUMMARY CARD (FEATURED FIRST) */}
          <div className="glass rounded-2xl p-6 md:p-8 border-2 border-primary/40 bg-gradient-to-br from-primary/10 via-background to-primary/5 shadow-2xl relative overflow-hidden">
            {/* Subtle Glowing Background Accents */}
            <div className="absolute top-0 right-0 -mt-10 -mr-10 h-40 w-40 rounded-full bg-primary/20 blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 -mb-10 -ml-10 h-32 w-32 rounded-full bg-brand/15 blur-2xl pointer-events-none" />

            {/* AI Summary Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-primary/20 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/30">
                  <Sparkles className="h-5 w-5 animate-pulse" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground tracking-tight">AI Executive Summary</h2>
                  <p className="text-xs text-muted-foreground font-medium">Google Gemini 2.5 Flash Summary Engine</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {data.cached ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-semibold text-muted-foreground border border-border/60 shadow-sm">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                    Cached in MongoDB
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 px-3 py-1 text-xs font-semibold border border-emerald-500/30 shadow-sm">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Generated via Gemini API
                  </span>
                )}
              </div>
            </div>

            {/* Highlighted Main Summary Box */}
            <div className="mt-5 rounded-xl border border-primary/20 bg-background/80 p-5 text-sm md:text-base leading-relaxed text-foreground font-medium shadow-inner whitespace-pre-line">
              {parsed?.mainText}
            </div>

            {/* 4-Card Structured Insights Grid (Purpose, Action Items, Dates, Tone) */}
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-1">
              {/* Purpose Card */}
              <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-bold text-sky-600 dark:text-sky-400">
                  <Target className="h-4 w-4 shrink-0" />
                  Purpose
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed font-medium">
                  {parsed?.purpose || "Informational communication."}
                </p>
              </div>

              {/* Action Items Card */}
              <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-bold text-primary">
                  <CheckSquare className="h-4 w-4 shrink-0" />
                  Action Items
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed font-medium">
                  {parsed?.actions || "No required action items specified."}
                </p>
              </div>

              {/* Dates & Deadlines Card */}
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-600 dark:text-amber-400">
                  <Calendar className="h-4 w-4 shrink-0" />
                  Dates & Deadlines
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed font-medium">
                  {parsed?.dates || "No specific dates or deadlines extracted."}
                </p>
              </div>

              {/* Email Tone Card */}
              <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-4 space-y-1.5 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 dark:text-indigo-400">
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  Email Tone
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed font-medium capitalize">
                  {parsed?.tone || "Professional"}
                </p>
              </div>
            </div>
          </div>

          {/* EMAIL METADATA CARD (WITH EXPLICIT LABELS FOR SUBJECT, FROM, TO, CATEGORY, DATE) */}
          <div className="glass rounded-2xl p-6 md:p-8 border border-border/60 shadow-lg space-y-5">
            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Inbox className="h-4 w-4 text-primary" />
                Email Metadata & Classification Details
              </h3>
              {data.sent_at && (
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" />
                  <strong className="text-foreground">Sent Date:</strong> {formatDate(data.sent_at)}
                </span>
              )}
            </div>

            {/* EXPLICIT SUBJECT FIELD */}
            <div className="space-y-1.5 bg-muted/20 rounded-xl p-4 border border-border/40">
              <span className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5" />
                Subject:
              </span>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-foreground leading-snug">
                {data.subject || "(No Subject)"}
              </h1>
            </div>

            {/* SENDER, RECEIVER & CATEGORY BADGE GRID */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-medium">
              {/* FROM (Sender) */}
              <div className="rounded-xl bg-muted/20 p-3.5 border border-border/40 space-y-1">
                <span className="text-[11px] font-bold text-muted-foreground flex items-center gap-1.5 uppercase tracking-wider">
                  <User className="h-3.5 w-3.5 text-primary" /> From (Sender):
                </span>
                <p className="font-semibold text-foreground truncate">{displaySender}</p>
              </div>

              {/* TO (Receiver) */}
              <div className="rounded-xl bg-muted/20 p-3.5 border border-border/40 space-y-1">
                <span className="text-[11px] font-bold text-muted-foreground flex items-center gap-1.5 uppercase tracking-wider">
                  <Mail className="h-3.5 w-3.5 text-primary" /> To (Receiver):
                </span>
                <p className="font-semibold text-foreground truncate">{displayReceiver}</p>
              </div>

              {/* CATEGORY / PREDICTION */}
              <div className="rounded-xl bg-muted/20 p-3.5 border border-border/40 space-y-1">
                <span className="text-[11px] font-bold text-muted-foreground flex items-center gap-1.5 uppercase tracking-wider">
                  <ShieldCheck className="h-3.5 w-3.5 text-primary" /> Category / Prediction:
                </span>
                <div className="flex items-center gap-2 pt-0.5">
                  <EmailLabelBadge label={data.predicted_label || "ham"} />
                  {typeof data.predicted_score === "number" && (
                    <span className="text-[11px] font-semibold text-muted-foreground">
                      {(data.predicted_score * 100).toFixed(1)}% score
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* FULL EMAIL BODY PREVIEW */}
          <div className="glass rounded-2xl p-6 border border-border/50 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Mail className="h-3.5 w-3.5 text-primary" />
              Full Email Body Preview
            </h3>
            <div className="rounded-xl border border-border/40 bg-muted/30 p-4 text-xs font-mono leading-relaxed text-muted-foreground max-h-60 overflow-y-auto whitespace-pre-wrap">
              {data.body || "(No text body content available for preview)"}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default EmailSummaryPageView;
