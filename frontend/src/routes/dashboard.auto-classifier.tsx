import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw,
  Mail,
  MailX,
  AlertTriangle,
  Plug,
  Sparkles,
  History as HistoryIcon,
} from "lucide-react";
import { toast } from "sonner";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { EmailLabelBadge } from "@/components/EmailLabelBadge";
import { emailsApi, type ClassifiedEmail } from "@/services/emailsApi";
import { googleAuthApi } from "@/services/googleAuthApi";
import { formatDate, truncate } from "@/utils/format";

export const Route = createFileRoute("/dashboard/auto-classifier")({
  head: () => ({
    meta: [
      { title: "Auto Classifier — MailSentry" },
      {
        name: "description",
        content: "Fetch and classify new incoming Gmail messages with MailSentry AI.",
      },
    ],
  }),
  component: AutoClassifierPage,
});

type PageState = "loading" | "gmail-not-connected" | "error" | "ready";

function AutoClassifierPage() {
  const navigate = useNavigate();

  const [pageState, setPageState] = useState<PageState>("loading");
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Auto Classifier strictly displays only new emails that have never been classified before (first 50 new)
  const [newlyFetchedEmails, setNewlyFetchedEmails] = useState<ClassifiedEmail[]>([]);

  const hasFetchedOnce = useRef(false);

  /* ─── Fetch pipeline trigger ─── */
  const triggerFetch = useCallback(async () => {
    setIsFetching(true);
    setFetchError(null);
    try {
      const result = await emailsApi.fetchEmails();
      const newItems = result.new_emails || [];
      setNewlyFetchedEmails(newItems);

      if (newItems.length > 0) {
        toast.success(`Fetched & classified ${newItems.length} new unclassified email(s)!`, {
          duration: 4000,
        });
      } else if (result.fetched === 0 || newItems.length === 0) {
        toast.info("No new unclassified emails found in Gmail.", { duration: 4000 });
      }

      if (result.skipped > 0) {
        toast.warning(
          `${result.classified} new email(s) classified, ${result.skipped} skipped due to errors.`,
          { duration: 5000 },
        );
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch emails.";
      if (msg.toLowerCase().includes("wait")) {
        toast.warning(msg, { duration: 5000 });
      } else {
        setFetchError(msg);
      }
    } finally {
      setIsFetching(false);
    }
  }, []);

  /* ─── on mount: check Gmail status, then fetch ─── */
  useEffect(() => {
    if (hasFetchedOnce.current) return;
    hasFetchedOnce.current = true;

    (async () => {
      try {
        const status = await googleAuthApi.getStatus();
        if (!status.connected) {
          setPageState("gmail-not-connected");
          return;
        }
        setPageState("loading");
        await triggerFetch();
        setPageState("ready");
      } catch {
        setPageState("error");
      }
    })();
  }, [triggerFetch]);

  /* ─── render states ─── */

  if (pageState === "loading") {
    return (
      <PageTransition>
        <LoadingState message="Connecting to Gmail & checking for unclassified emails…" />
      </PageTransition>
    );
  }

  if (pageState === "gmail-not-connected") {
    return (
      <PageTransition>
        <GmailNotConnectedState onConnect={() => navigate({ to: "/dashboard/settings" })} />
      </PageTransition>
    );
  }

  if (pageState === "error") {
    return (
      <PageTransition>
        <ErrorState
          message="Something went wrong loading the page."
          onRetry={() => {
            setPageState("loading");
            hasFetchedOnce.current = false;
          }}
        />
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div>
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Auto Classifier</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Displays new unclassified Gmail messages automatically processed by MailSentry AI.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              id="refresh-btn"
              onClick={triggerFetch}
              disabled={isFetching}
              className="bg-gradient-brand shadow-elegant shrink-0"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              {isFetching ? "Syncing Gmail…" : "Refresh"}
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate({ to: "/dashboard/history" })}
              className="shrink-0"
            >
              <HistoryIcon className="mr-2 h-4 w-4" />
              History
            </Button>
          </div>
        </div>

        {/* Fetch error banner */}
        <AnimatePresence>
          {fetchError && (
            <motion.div
              key="error-banner"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mt-4 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{fetchError}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Info Header Banner */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-brand/20 bg-brand/5 p-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2 font-medium text-foreground">
            <Sparkles className="h-4 w-4 text-brand" />
            <span>Showing only new unclassified emails from Gmail (max 50)</span>
          </div>
          <span className="text-xs">
            Previously classified emails are saved to your{" "}
            <Link to="/dashboard/history" className="text-brand underline underline-offset-2 hover:text-brand/80">
              Prediction History
            </Link>
          </span>
        </div>

        {/* Email table */}
        <div className="glass mt-4 rounded-2xl p-4 md:p-6">
          {isFetching && newlyFetchedEmails.length === 0 ? (
            <LoadingState message="Fetching & classifying new Gmail messages…" compact />
          ) : newlyFetchedEmails.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/40 text-muted-foreground">
                <MailX className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-semibold">No new unclassified emails found</p>
                <p className="mt-1 text-xs text-muted-foreground max-w-md">
                  All latest emails in your Gmail inbox have already been classified or stored. Click <span className="font-semibold">Refresh</span> to check for new incoming messages.
                </p>
              </div>
              <div className="flex flex-wrap gap-3 mt-3">
                <Button variant="outline" size="sm" onClick={triggerFetch} disabled={isFetching}>
                  <RefreshCw className="mr-2 h-3.5 w-3.5" />
                  Check Gmail Again
                </Button>
                <Button variant="default" size="sm" onClick={() => navigate({ to: "/dashboard/history" })}>
                  <HistoryIcon className="mr-2 h-3.5 w-3.5" />
                  View Prediction History
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-sm">
                <thead>
                  <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-3 text-left font-medium w-[30%]">Subject</th>
                    <th className="pb-3 text-left font-medium w-[26%]">Preview</th>
                    <th className="pb-3 text-left font-medium w-[14%]">Category</th>
                    <th className="pb-3 text-left font-medium w-[15%]">Email Date</th>
                    <th className="pb-3 text-right font-medium w-[15%]">Classified At</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence mode="wait">
                    {newlyFetchedEmails.map((email, i) => (
                      <motion.tr
                        key={email.message_id}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="border-b border-border/40 last:border-0 hover:bg-muted/20 transition-colors"
                      >
                        <td className="py-3 pr-4 font-medium">
                          <span title={email.subject}>
                            {truncate(email.subject ?? "(no subject)", 45)}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">
                          {truncate(email.snippet ?? "—", 55)}
                        </td>
                        <td className="py-3 pr-4">
                          <EmailLabelBadge label={email.predicted_label} />
                        </td>
                        <td className="py-3 pr-2 text-muted-foreground text-xs">
                          {email.sent_at || email.received_at ? formatDate(email.sent_at || email.received_at!) : "—"}
                        </td>
                        <td className="py-3 text-right text-muted-foreground text-xs">
                          {email.classified_at ? formatDate(email.classified_at) : "—"}
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  );
}

/* ─── Sub-components ─── */

function LoadingState({ message, compact = false }: { message: string; compact?: boolean }) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 text-center ${
        compact ? "py-16" : "min-h-[60vh]"
      }`}
    >
      <div className="relative flex h-16 w-16 items-center justify-center">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand/30" />
        <Mail className="relative h-7 w-7 text-brand" />
      </div>
      <p className="text-sm text-muted-foreground max-w-xs">{message}</p>
    </div>
  );
}

function GmailNotConnectedState({ onConnect }: { onConnect: () => void }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-brand/10 text-brand shadow-elegant">
        <Plug className="h-9 w-9" />
      </div>
      <div>
        <h2 className="text-xl font-semibold">Gmail Not Connected</h2>
        <p className="mt-2 text-sm text-muted-foreground max-w-sm">
          Connect your Gmail account to allow MailSentry to fetch and classify your emails automatically.
        </p>
      </div>
      <Button
        id="connect-gmail-btn"
        onClick={onConnect}
        className="bg-gradient-brand shadow-elegant px-6"
      >
        <Plug className="mr-2 h-4 w-4" />
        Connect Gmail
      </Button>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
        <AlertTriangle className="h-7 w-7" />
      </div>
      <div>
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="mt-1 text-sm text-muted-foreground max-w-sm">{message}</p>
      </div>
      <Button id="retry-btn" variant="outline" onClick={onRetry}>
        <RefreshCw className="mr-2 h-4 w-4" />
        Try Again
      </Button>
    </div>
  );
}
