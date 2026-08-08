import React, { useEffect, useState } from "react";
import { Sparkles, X, RefreshCw, AlertCircle, CheckCircle2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmailLabelBadge } from "@/components/EmailLabelBadge";
import { GmailSpamIndicator } from "@/components/GmailSpamIndicator";
import { emailSummaryService, type EmailSummaryData } from "@/services/emailSummaryService";


export interface HistoryEmailItem {
  email_id?: string;
  message_id?: string;
  id?: string;
  subject: string;
  sender?: string | null;
  receiver?: string | null;
  body?: string | null;
  snippet?: string | null;
  prediction?: string | null;
  predicted_label?: string | null;
  predicted_score?: number | null;
  gmail_classification?: any;
}

interface EmailSummaryModalProps {
  email: HistoryEmailItem | null;
  isOpen: boolean;
  onClose: () => void;
}


export const EmailSummaryModal: React.FC<EmailSummaryModalProps> = ({
  email,
  isOpen,
  onClose,
}) => {
  const [summaryData, setSummaryData] = useState<EmailSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const emailId = email?.email_id || email?.message_id || email?.id;

  const fetchSummary = async () => {
    if (!emailId) return;

    setIsLoading(true);
    setError(null);
    try {
      // Call GET /emails/{email_id}/summary using Axios service
      const data = await emailSummaryService.getEmailSummary(emailId);
      setSummaryData(data);
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : "Failed to generate email summary. Please try again.";
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && emailId) {
      setSummaryData(null);
      fetchSummary();
    } else {
      setSummaryData(null);
      setError(null);
      setIsLoading(false);
    }
  }, [isOpen, emailId]);

  if (!isOpen || !email) return null;

  const label = email.predicted_label || email.prediction || "ham";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-2xl border border-border/60 bg-background/95 p-6 shadow-2xl backdrop-blur-md dark:bg-card/95">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border/40 pb-4">
          <div className="space-y-1 pr-6">
            <div className="flex items-center gap-2">
              <GmailSpamIndicator
                mailsentryLabel={label}
                gmailClassification={email.gmail_classification}
              />
              {email.predicted_score !== undefined && email.predicted_score !== null && (
                <span className="text-xs text-muted-foreground font-medium">
                  {(email.predicted_score * 100).toFixed(1)}% confidence
                </span>
              )}
            </div>

            <h2 className="text-lg font-semibold tracking-tight text-foreground line-clamp-2 mt-1">
              {email.subject || "(No Subject)"}
            </h2>
            {email.sender && (
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">From:</span> {email.sender}
              </p>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content Body & Summary */}
        <div className="mt-5 space-y-5 max-h-[70vh] overflow-y-auto pr-1">
          {/* AI Executive Summary Card */}
          <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between gap-2 border-b border-primary/10 pb-2.5 mb-3">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Sparkles className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-semibold text-foreground">AI Email Summary</h3>
              </div>

              {summaryData && (
                <div className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
                  {summaryData.cached ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-muted-foreground border border-border/40">
                      <Clock className="h-3 w-3" /> Cached
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 border border-emerald-500/20">
                      <CheckCircle2 className="h-3 w-3" /> Generated via Gemini
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Loading State */}
            {isLoading && (
              <div className="flex flex-col items-center justify-center py-6 text-center text-sm text-muted-foreground">
                <RefreshCw className="h-5 w-5 animate-spin text-primary mb-2" />
                <p className="font-medium text-foreground">Generating concise summary with Gemini API…</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Extracting key topics, action items, deadlines, and tone.
                </p>
              </div>
            )}

            {/* Error State */}
            {error && !isLoading && (
              <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchSummary}
                    className="mt-2 h-7 px-2.5 text-xs border-destructive/40 text-destructive hover:bg-destructive/10"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" /> Retry
                  </Button>
                </div>
              </div>
            )}

            {/* Summary Result */}
            {summaryData && !isLoading && (
              <div className="text-sm leading-relaxed text-foreground whitespace-pre-line font-normal">
                {summaryData.summary}
              </div>
            )}
          </div>

          {/* Full Email Body / Snippet Preview */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Email Content Preview
            </h4>
            <div className="rounded-xl border border-border/50 bg-muted/20 p-4 text-xs leading-relaxed text-muted-foreground max-h-48 overflow-y-auto font-mono">
              {email.body || email.snippet || "(No email body content available)"}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 flex items-center justify-end gap-3 border-t border-border/40 pt-4">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EmailSummaryModal;
