import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw,
  Mail,
  MailX,
  AlertTriangle,
  Plug,
  ChevronLeft,
  ChevronRight,
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
        content: "View your Gmail emails automatically fetched and classified by MailSentry AI.",
      },
    ],
  }),
  component: AutoClassifierPage,
});

const PAGE_SIZE = 20;

type PageState = "loading" | "gmail-not-connected" | "error" | "ready";

function AutoClassifierPage() {
  const navigate = useNavigate();

  const [pageState, setPageState] = useState<PageState>("loading");
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [newlyFetchedEmails, setNewlyFetchedEmails] = useState<ClassifiedEmail[]>([]);
  const [emails, setEmails] = useState<ClassifiedEmail[]>([]);
  const [activeTab, setActiveTab] = useState<"new" | "all">("new");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [loadingEmails, setLoadingEmails] = useState(false);

  const hasFetchedOnce = useRef(false);

  /* ─── helpers ─── */

  const loadEmails = useCallback(async (pg: number) => {
    setLoadingEmails(true);
    setFetchError(null);
    try {
      const res = await emailsApi.getEmails({ limit: PAGE_SIZE, page: pg });
      setEmails(res.emails);
      setTotalCount(res.total_count ?? res.total ?? res.count);
      setPage(pg);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to load emails.");
    } finally {
      setLoadingEmails(false);
    }
  }, []);

  const triggerFetch = useCallback(async () => {
    setIsFetching(true);
    setFetchError(null);
    try {
      const result = await emailsApi.fetchEmails();
      if (result.new_emails && result.new_emails.length > 0) {
        setNewlyFetchedEmails(result.new_emails);
        setActiveTab("new");
        toast.success(`Fetched & classified ${result.new_emails.length} new incoming email(s)!`, {
          duration: 4000,
        });
      } else if (result.fetched === 0) {
        toast.info("No new emails to classify.", { duration: 4000 });
        setActiveTab("all");
      } else if (result.skipped > 0) {
        toast.warning(
          `${result.classified} email(s) classified, ${result.skipped} skipped due to errors.`,
          { duration: 5000 },
        );
      }
      await loadEmails(1);
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
  }, [loadEmails]);


  /* ─── on mount: check Gmail status, then fetch + load ─── */
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

  /* ─── pagination ─── */
  const pageCount = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  const goToPage = (pg: number) => {
    if (pg < 1 || pg > pageCount) return;
    loadEmails(pg);
  };

  /* ─── render states ─── */

  if (pageState === "loading") {
    return (
      <PageTransition>
        <LoadingState message="Connecting to Gmail and classifying your emails…" />
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
              Your Gmail inbox fetched and classified by MailSentry AI.
            </p>
          </div>
          <Button
            id="refresh-btn"
            onClick={triggerFetch}
            disabled={isFetching || loadingEmails}
            className="bg-gradient-brand shadow-elegant shrink-0"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            {isFetching ? "Fetching…" : "Refresh"}
          </Button>
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

        {/* Controls & Tabs */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-b border-border/50 pb-3">
          <div className="flex gap-2">
            <Button
              variant={activeTab === "new" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("new")}
              className={activeTab === "new" ? "bg-brand text-brand-foreground" : ""}
            >
              Newly Incoming ({newlyFetchedEmails.length})
            </Button>
            <Button
              variant={activeTab === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("all")}
              className={activeTab === "all" ? "bg-brand text-brand-foreground" : ""}
            >
              All Stored Emails ({totalCount})
            </Button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/dashboard/history" })}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            View Full Prediction History →
          </Button>
        </div>

        {/* Email table */}
        <div className="glass mt-4 rounded-2xl p-4 md:p-6">
          {loadingEmails ? (
            <LoadingState message="Loading emails…" compact />
          ) : activeTab === "new" && newlyFetchedEmails.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <MailX className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">No new incoming emails in this fetch run</p>
              <p className="text-xs text-muted-foreground max-w-sm">
                Click <span className="font-semibold">Refresh</span> to check Gmail for new messages, or view all past classified emails.
              </p>
              <div className="flex gap-3 mt-2">
                <Button variant="outline" size="sm" onClick={() => setActiveTab("all")}>
                  Show All Stored Emails ({totalCount})
                </Button>
                <Button variant="outline" size="sm" onClick={() => navigate({ to: "/dashboard/history" })}>
                  Go to History Page
                </Button>
              </div>
            </div>
          ) : (
            <>
              {activeTab === "new" && (
                <div className="mb-4 flex items-center justify-between text-xs text-muted-foreground border-b border-border/30 pb-2">
                  <span>Showing {newlyFetchedEmails.length} newly fetched incoming email(s) from Gmail</span>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px] text-sm">
                  <thead>
                    <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                      <th className="pb-3 text-left font-medium w-[30%]">Subject</th>
                      <th className="pb-3 text-left font-medium w-[26%]">Preview</th>
                      <th className="pb-3 text-left font-medium w-[14%]">Category</th>
                      <th className="pb-3 text-left font-medium w-[15%]">Email Sent Date</th>
                      <th className="pb-3 text-right font-medium w-[15%]">Classified At</th>
                    </tr>
                  </thead>
                  <tbody>
                    <AnimatePresence mode="wait">
                      {(activeTab === "new" ? newlyFetchedEmails : emails).map((email, i) => (
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

              {/* Pagination for All Stored Emails */}
              {activeTab === "all" && (
                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
                  <span>
                    Page {page} of {pageCount} · {totalCount} email{totalCount !== 1 ? "s" : ""} total
                  </span>
                  <div className="flex gap-2">
                    <Button
                      id="prev-page-btn"
                      variant="outline"
                      size="sm"
                      disabled={page <= 1 || loadingEmails}
                      onClick={() => goToPage(page - 1)}
                    >
                      <ChevronLeft className="h-3.5 w-3.5 mr-1" />
                      Previous
                    </Button>
                    <Button
                      id="next-page-btn"
                      variant="outline"
                      size="sm"
                      disabled={page >= pageCount || loadingEmails}
                      onClick={() => goToPage(page + 1)}
                    >
                      Next
                      <ChevronRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
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

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/40 text-muted-foreground">
        <MailX className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-medium">No emails found</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Click <span className="font-semibold">Refresh</span> to fetch and classify your latest emails.
        </p>
      </div>
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
