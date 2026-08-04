import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw,
  Mail,
  AlertTriangle,
  Plug,
  Sparkles,
  History as HistoryIcon,
  Wand2,
  CheckCircle2,
  Search,
  X,
  SearchX,
} from "lucide-react";
import { toast } from "sonner";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { emailsApi, type UnclassifiedEmail } from "@/services/emailsApi";
import { googleAuthApi } from "@/services/googleAuthApi";
import { formatDate, truncate } from "@/utils/format";
import { useDebounce } from "@/hooks/useDebounce";
import { HighlightText } from "@/components/HighlightText";
import { GmailOpenButton } from "@/components/GmailOpenButton";
import { getGmailUrl, openGmailInNewTab } from "@/utils/gmail";

export const Route = createFileRoute("/dashboard/auto-classifier")({
  head: () => ({
    meta: [
      { title: "Auto Classifier — MailSentry" },
      {
        name: "description",
        content: "Queue of unclassified incoming Gmail messages waiting to be classified by MailSentry AI.",
      },
    ],
  }),
  component: AutoClassifierPage,
});

type PageState = "loading" | "gmail-not-connected" | "error" | "ready";
const PAGE_SIZE = 10;

function AutoClassifierPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const handleConnectGmail = async () => {
    try {
      await googleAuthApi.initiateConnect();
    } catch (err) {
      toast.error("Failed to initiate Google OAuth connection.");
    }
  };

  const [pageState, setPageState] = useState<PageState>("loading");
  const [isFetching, setIsFetching] = useState(false);
  const [isClassifying, setIsClassifying] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<{
    processed: number;
    total: number;
    status: string;
    current_subject?: string | null;
    startTime?: number;
  } | null>(null);

  // Search & Pagination state
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearch = useDebounce(searchTerm, 300);
  const [page, setPage] = useState(1);

  // Auto Classifier strictly represents the queue of UNCLASSIFIED emails (max 50 new)
  const [unclassifiedEmails, setUnclassifiedEmails] = useState<UnclassifiedEmail[]>([]);

  const hasFetchedOnce = useRef(false);

  /* ─── Fetch unclassified emails from Gmail ─── */
  const triggerFetch = useCallback(async () => {
    setIsFetching(true);
    setFetchError(null);
    try {
      const result = await emailsApi.fetchUnclassifiedEmails();
      const newItems = result.unclassified_emails || [];
      setUnclassifiedEmails(newItems);
      setPage(1);

      if (newItems.length > 0) {
        toast.info(`Fetched ${newItems.length} unclassified email(s) from Gmail.`, {
          duration: 4000,
        });
      } else {
        toast.info("No new unclassified emails found in Gmail.", { duration: 4000 });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch unclassified emails.";
      if (msg.toLowerCase().includes("wait")) {
        toast.warning(msg, { duration: 5000 });
      } else {
        setFetchError(msg);
      }
    } finally {
      setIsFetching(false);
    }
  }, []);

  /* ─── Classify displayed unclassified emails ─── */
  const handleClassify = async () => {
    if (unclassifiedEmails.length === 0) return;
    setIsClassifying(true);
    setFetchError(null);
    const startMs = Date.now();

    try {
      // Step 1: Start background job (returns in <100ms)
      const job = await emailsApi.startClassifyJob(unclassifiedEmails);
      setJobProgress({
        processed: job.processed,
        total: job.total || unclassifiedEmails.length,
        status: job.status,
        current_subject: job.current_subject,
        startTime: startMs,
      });

      // Step 2: Poll status every 1.0s until complete or failed
      await new Promise<void>((resolve, reject) => {
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await emailsApi.getJobStatus(job.job_id);
            setJobProgress({
              processed: statusRes.processed,
              total: statusRes.total || unclassifiedEmails.length,
              status: statusRes.status,
              current_subject: statusRes.current_subject,
              startTime: startMs,
            });

            if (statusRes.status === "completed") {
              clearInterval(pollInterval);
              const count = statusRes.classified ?? 0;
              const skipped = statusRes.skipped ?? 0;

              // Force refetch and invalidate history query cache immediately!
              await queryClient.resetQueries({ queryKey: ["history"] });
              await queryClient.invalidateQueries({ queryKey: ["history"] });
              await queryClient.invalidateQueries({ queryKey: ["dashboard_stats"] });

              if (count > 0) {
                setUnclassifiedEmails([]);
                setSearchTerm("");
                setPage(1);

                toast.success(
                  `Successfully classified & stored ${count} email(s) in MongoDB! View them in Prediction History.`,
                  {
                    duration: 5000,
                    action: {
                      label: "View History",
                      onClick: () => navigate({ to: "/dashboard/history" }),
                    },
                  }
                );
              } else if (skipped > 0) {
                toast.error(
                  `Classification completed, but ${skipped} email(s) failed to save. Please try again.`,
                  { duration: 5000 }
                );
              } else {
                toast.info("No emails were classified.");
              }
              resolve();
            } else if (statusRes.status === "failed") {
              clearInterval(pollInterval);
              reject(new Error(statusRes.error || "Background classification job failed."));
            }
          } catch (pollErr) {
            clearInterval(pollInterval);
            reject(pollErr);
          }
        }, 1000);
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to classify emails.";
      setFetchError(msg);
      toast.error(msg);
    } finally {
      setIsClassifying(false);
      setJobProgress(null);
    }
  };

  /* ─── Real-time frontend search filtering ─── */
  const filteredEmails = useMemo(() => {
    if (!debouncedSearch.trim()) return unclassifiedEmails;
    const q = debouncedSearch.toLowerCase().trim();
    return unclassifiedEmails.filter((email) => {
      const subjectMatch = (email.subject || "").toLowerCase().includes(q);
      const snippetMatch = (email.snippet || "").toLowerCase().includes(q);
      return subjectMatch || snippetMatch;
    });
  }, [unclassifiedEmails, debouncedSearch]);

  // Reset page when search term changes
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const pageCount = Math.max(1, Math.ceil(filteredEmails.length / PAGE_SIZE));
  const paginatedEmails = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredEmails.slice(start, start + PAGE_SIZE);
  }, [filteredEmails, page]);

  /* ─── on mount: check Gmail status, then fetch unclassified queue ─── */
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
        <LoadingState message="Connecting to Gmail & fetching unclassified email queue…" />
      </PageTransition>
    );
  }

  if (pageState === "gmail-not-connected") {
    return (
      <PageTransition>
        <GmailNotConnectedState onConnect={handleConnectGmail} />
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
            <h1 className="text-2xl font-semibold tracking-tight">Auto Classifier Queue</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Pending unclassified Gmail messages waiting to be analyzed by MailSentry AI.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              id="refresh-btn"
              variant="outline"
              onClick={triggerFetch}
              disabled={isFetching || isClassifying}
              className="shrink-0"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              {isFetching ? "Syncing Gmail…" : "Fetch Queue"}
            </Button>
            <Button
              id="classify-btn"
              onClick={handleClassify}
              disabled={isClassifying || isFetching || unclassifiedEmails.length === 0}
              className="bg-gradient-brand shadow-elegant shrink-0 font-semibold"
            >
              {isClassifying ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Classifying & Saving…
                </>
              ) : (
                <>
                  <Wand2 className="mr-2 h-4 w-4" />
                  Classify {unclassifiedEmails.length > 0 ? `(${unclassifiedEmails.length})` : ""} Emails
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              onClick={() => navigate({ to: "/dashboard/history" })}
              className="shrink-0 text-muted-foreground hover:text-foreground"
            >
              <HistoryIcon className="mr-2 h-4 w-4" />
              History
            </Button>
          </div>
        </div>

        {/* Live Progress Bar Banner */}
        <AnimatePresence>
          {jobProgress && (
            <motion.div
              key="job-progress-banner"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-6 overflow-hidden rounded-xl border border-primary/40 bg-card/60 p-5 shadow-elegant backdrop-blur-sm"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <RefreshCw className="h-5 w-5 animate-spin" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground">Classifying Emails...</h4>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {jobProgress.processed} / {jobProgress.total} emails processed
                      {jobProgress.startTime && jobProgress.processed > 0 && jobProgress.processed < jobProgress.total && (
                        <span className="ml-2 text-primary font-medium">
                          • Est. remaining: ~{Math.max(1, Math.ceil(((jobProgress.total - jobProgress.processed) * ((Date.now() - jobProgress.startTime) / 1000 / jobProgress.processed))))}s
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-base font-bold text-primary">
                    {Math.round((jobProgress.processed / (jobProgress.total || 1)) * 100)}%
                  </span>
                </div>
              </div>

              {jobProgress.current_subject && (
                <p className="mt-3 text-xs text-muted-foreground truncate border-t border-border/40 pt-2">
                  <span className="font-semibold text-foreground">Current Email:</span> {jobProgress.current_subject}
                </p>
              )}

              <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-gradient-brand transition-all duration-300 ease-out"
                  style={{
                    width: `${Math.min(100, Math.max(5, Math.round((jobProgress.processed / (jobProgress.total || 1)) * 100)))}%`,
                  }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

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
            <span>
              Unclassified Email Queue ({filteredEmails.length}
              {unclassifiedEmails.length !== filteredEmails.length ? ` of ${unclassifiedEmails.length}` : ""} pending, max 50)
            </span>
          </div>
          <span className="text-xs">
            Classified emails are saved directly to{" "}
            <Link to="/dashboard/history" className="text-brand underline underline-offset-2 hover:text-brand/80">
              Prediction History
            </Link>
          </span>
        </div>

        {/* Email table container */}
        <div className="glass mt-4 rounded-2xl p-4 md:p-6">
          {/* Search bar & Action bar */}
          {unclassifiedEmails.length > 0 && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-4">
              <div className="relative flex-1 min-w-[240px] max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="auto-classifier-search"
                  type="text"
                  placeholder="Search unclassified emails by subject or body..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 pr-8 text-xs sm:text-sm bg-background/50 border-border/60 focus:border-brand"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm("")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={handleClassify}
                  disabled={isClassifying || isFetching}
                  className="bg-gradient-brand text-xs shadow-elegant font-semibold"
                >
                  <Wand2 className="mr-1.5 h-3.5 w-3.5" />
                  Classify All ({unclassifiedEmails.length})
                </Button>
              </div>
            </div>
          )}

          {isFetching && unclassifiedEmails.length === 0 ? (
            <LoadingState message="Fetching unclassified Gmail queue…" compact />
          ) : unclassifiedEmails.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-success/10 text-success">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <p className="text-sm font-semibold">Queue is empty!</p>
                <p className="mt-1 text-xs text-muted-foreground max-w-md">
                  All latest emails in your connected Gmail account have been classified and stored in MongoDB. Click <span className="font-semibold">Fetch Queue</span> to check for new incoming messages.
                </p>
              </div>
              <div className="flex flex-wrap gap-3 mt-3">
                <Button variant="outline" size="sm" onClick={triggerFetch} disabled={isFetching}>
                  <RefreshCw className="mr-2 h-3.5 w-3.5" />
                  Fetch New Messages
                </Button>
                <Button variant="default" size="sm" onClick={() => navigate({ to: "/dashboard/history" })}>
                  <HistoryIcon className="mr-2 h-3.5 w-3.5" />
                  View Prediction History
                </Button>
              </div>
            </div>
          ) : filteredEmails.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-14 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted/40 text-muted-foreground">
                <SearchX className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-semibold">No matching emails found</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  No unclassified email matches "<span className="font-medium text-foreground">{searchTerm}</span>".
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => setSearchTerm("")} className="mt-2 text-xs">
                Clear Search
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px] text-sm">
                  <thead>
                    <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                      <th className="pb-3 text-left font-medium w-[6%]">#</th>
                      <th className="pb-3 text-left font-medium w-[28%]">Subject</th>
                      <th className="pb-3 text-left font-medium w-[30%]">Preview</th>
                      <th className="pb-3 text-left font-medium w-[12%]">Status</th>
                      <th className="pb-3 text-left font-medium w-[18%]">Email Sent Date</th>
                      <th className="pb-3 text-center font-medium w-[6%]">Open</th>
                    </tr>
                  </thead>
                  <tbody>
                    <AnimatePresence>
                      {paginatedEmails.map((email, index) => {
                        const rowNumber = (page - 1) * PAGE_SIZE + index + 1;
                        const msgId = email.message_id || email.gmail_message_id;
                        const gmailUrl = getGmailUrl(msgId, email.thread_id);
                        return (
                          <motion.tr
                            key={msgId || index}
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ delay: index * 0.02 }}
                            onClick={(e) => {
                              // Prevent triggering if user clicked an interactive child element
                              const target = e.target as HTMLElement;
                              if (target.closest("button, a, input, select, [role='button']")) return;
                              if (gmailUrl) openGmailInNewTab(gmailUrl);
                            }}
                            className={`border-b border-border/40 last:border-0 transition-colors group ${
                              gmailUrl ? "hover:bg-muted/30 cursor-pointer" : "hover:bg-muted/10"
                            }`}
                          >
                            <td className="py-3 pr-2 text-xs font-semibold text-muted-foreground">
                              {rowNumber}
                            </td>
                            <td className="py-3 pr-4 font-medium">
                              <span title={email.subject}>
                                <HighlightText
                                  text={truncate(email.subject ?? "(no subject)", 42)}
                                  query={debouncedSearch}
                                />
                              </span>
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground">
                              <HighlightText
                                text={truncate(email.snippet ?? "—", 55)}
                                query={debouncedSearch}
                              />
                            </td>
                            <td className="py-3 pr-4">
                              <Badge variant="outline" className="border-brand/40 bg-brand/10 text-brand text-xs font-normal">
                                Unclassified
                              </Badge>
                            </td>
                            <td className="py-3 text-left text-muted-foreground text-xs pr-2">
                              {email.sent_at || email.received_at ? formatDate(email.sent_at || email.received_at!) : "—"}
                            </td>
                            <td className="py-3 text-center">
                              <GmailOpenButton
                                messageId={msgId}
                                threadId={email.thread_id}
                              />
                            </td>
                          </motion.tr>
                        );
                      })}
                    </AnimatePresence>
                  </tbody>
                </table>
              </div>

              {/* Pagination controls for Auto Classifier */}
              {filteredEmails.length > PAGE_SIZE && (
                <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground border-t border-border/40 pt-4">
                  <span>
                    Page {page} of {pageCount} · {filteredEmails.length} unclassified email{filteredEmails.length !== 1 ? "s" : ""}
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page >= pageCount}
                      onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                    >
                      Next
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
