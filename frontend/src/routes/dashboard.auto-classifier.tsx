import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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

function AutoClassifierPage() {
  const navigate = useNavigate();

  const [pageState, setPageState] = useState<PageState>("loading");
  const [isFetching, setIsFetching] = useState(false);
  const [isClassifying, setIsClassifying] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Search state
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearch = useDebounce(searchTerm, 300);

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

    try {
      const result = await emailsApi.classifyEmails(unclassifiedEmails);
      const count = result.classified || unclassifiedEmails.length;

      // Remove classified emails from Auto Classifier page immediately after successful storage
      setUnclassifiedEmails([]);
      setSearchTerm("");

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
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to classify emails.";
      setFetchError(msg);
      toast.error(msg);
    } finally {
      setIsClassifying(false);
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
              className="bg-gradient-brand shadow-elegant shrink-0"
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
                  className="bg-gradient-brand text-xs shadow-elegant"
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
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-sm">
                <thead>
                  <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-3 text-left font-medium w-[32%]">Subject</th>
                    <th className="pb-3 text-left font-medium w-[36%]">Preview</th>
                    <th className="pb-3 text-left font-medium w-[15%]">Status</th>
                    <th className="pb-3 text-right font-medium w-[17%]">Email Sent Date</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence mode="wait">
                    {filteredEmails.map((email, i) => (
                      <motion.tr
                        key={email.message_id}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ delay: i * 0.02 }}
                        className="border-b border-border/40 last:border-0 hover:bg-muted/20 transition-colors"
                      >
                        <td className="py-3 pr-4 font-medium">
                          <span title={email.subject}>
                            <HighlightText
                              text={truncate(email.subject ?? "(no subject)", 45)}
                              query={debouncedSearch}
                            />
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">
                          <HighlightText
                            text={truncate(email.snippet ?? "—", 60)}
                            query={debouncedSearch}
                          />
                        </td>
                        <td className="py-3 pr-4">
                          <Badge variant="outline" className="border-brand/40 bg-brand/10 text-brand text-xs font-normal">
                            Unclassified
                          </Badge>
                        </td>
                        <td className="py-3 text-right text-muted-foreground text-xs">
                          {email.sent_at || email.received_at ? formatDate(email.sent_at || email.received_at!) : "—"}
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
