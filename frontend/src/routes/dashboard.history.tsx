import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Search, MailX, X, SearchX, RefreshCw } from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { EmailLabelBadge } from "@/components/EmailLabelBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatConfidence, formatDate, truncate } from "@/utils/format";
import { useDebounce } from "@/hooks/useDebounce";
import { usePredictiveHistory } from "@/hooks/usePredictiveHistory";
import { HighlightText } from "@/components/HighlightText";

export const Route = createFileRoute("/dashboard/history")({
  head: () => ({
    meta: [
      { title: "Prediction History — MailSentry" },
      { name: "description", content: "Search and filter every stored email prediction in your database." },
    ],
  }),
  component: HistoryPage,
});

const PAGE_SIZE = 10;

function HistoryPage() {
  const navigate = useNavigate();

  // Search and Filter states
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearch = useDebounce(searchTerm, 300);

  const [filter, setFilter] = useState<string>("all");
  const [page, setPage] = useState(1);

  // TanStack Query with Intelligent Predictive Idle Prefetching
  const {
    emails,
    totalCount,
    pageCount,
    isLoading,
    isFetching,
    error,
  } = usePredictiveHistory({
    page,
    limit: PAGE_SIZE,
    label: filter,
    search: debouncedSearch,
  });

  return (
    <PageTransition>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Prediction History</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            All classified emails stored in your MailSentry database.
          </p>
        </div>
        {isFetching && !isLoading && (
          <div className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary shadow-sm">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            <span className="hidden sm:inline">Predictive Sync Active</span>
          </div>
        )}
      </div>

      <div className="glass mt-6 rounded-2xl p-4 md:p-6">
        <div className="flex flex-wrap items-center gap-3">
          {/* Real-time search bar */}
          <div className="relative min-w-[240px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="history-search-input"
              placeholder="Search by subject, body, prediction, or sender…"
              className="pl-9 pr-8 bg-background/50 border-border/60 focus:border-brand"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1); // Reset to page 1 on typing search
              }}
            />
            {searchTerm && (
              <button
                onClick={() => {
                  setSearchTerm("");
                  setPage(1);
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          <Select
            value={filter}
            onValueChange={(v) => {
              setFilter(v);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-44 bg-background/50 border-border/60">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="spam">Spam</SelectItem>
              <SelectItem value="ham">Safe / Inbox</SelectItem>
              <SelectItem value="important">Important</SelectItem>
              <SelectItem value="promotions">Promotions</SelectItem>
              <SelectItem value="social">Social</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="mt-5 overflow-x-auto">
          {isLoading ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              Loading prediction history from database…
            </div>
          ) : emails.length === 0 ? (
            debouncedSearch.trim() ? (
              <div className="flex flex-col items-center justify-center gap-3 py-14 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted/40 text-muted-foreground">
                  <SearchX className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm font-semibold">No emails found</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    No stored email matches "<span className="font-medium text-foreground">{debouncedSearch}</span>".
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSearchTerm("");
                    setPage(1);
                  }}
                  className="mt-2 text-xs"
                >
                  Clear Search
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
                <MailX className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium">No stored emails found in database</p>
                <p className="text-xs text-muted-foreground">
                  Fetch emails in the Auto Classifier page to save predictions.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => navigate({ to: "/dashboard/auto-classifier" })}
                >
                  Go to Auto Classifier
                </Button>
              </div>
            )
          ) : (
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="pb-3 text-left font-medium w-[5%]">#</th>
                  <th className="pb-3 text-left font-medium w-[17%]">Email Sent Date</th>
                  <th className="pb-3 text-left font-medium w-[26%]">Subject</th>
                  <th className="pb-3 text-left font-medium w-[24%]">Snippet</th>
                  <th className="pb-3 text-left font-medium w-[12%]">Category</th>
                  <th className="pb-3 text-left font-medium w-[8%]">Score</th>
                  <th className="pb-3 text-right font-medium w-[8%]">Classified</th>
                </tr>
              </thead>
              <tbody>
                {emails.map((email, index) => {
                  const rowNumber = (page - 1) * PAGE_SIZE + index + 1;
                  return (
                    <tr key={email.message_id} className="border-b border-border/40 last:border-0 hover:bg-muted/20 transition-colors">
                      <td className="py-3 pr-2 text-xs font-semibold text-muted-foreground">
                        {rowNumber}
                      </td>
                      <td className="py-3 text-muted-foreground text-xs font-medium pr-2">
                        {email.sent_at || email.received_at ? formatDate(email.sent_at || email.received_at!) : "—"}
                      </td>
                      <td className="py-3 font-medium pr-2">
                        <HighlightText
                          text={truncate(email.subject || "(no subject)", 38)}
                          query={debouncedSearch}
                        />
                      </td>
                      <td className="py-3 text-muted-foreground pr-2">
                        <HighlightText
                          text={truncate(email.snippet || "—", 42)}
                          query={debouncedSearch}
                        />
                      </td>
                      <td className="py-3 pr-2">
                        <EmailLabelBadge label={email.predicted_label} />
                      </td>
                      <td className="py-3 font-medium text-xs">
                        {typeof email.predicted_score === "number"
                          ? formatConfidence(email.predicted_score)
                          : "—"}
                      </td>
                      <td className="py-3 text-right text-muted-foreground text-xs">
                        {email.classified_at ? formatDate(email.classified_at) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {!isLoading && totalCount > 0 && (
          <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Page {page} of {pageCount} · {totalCount} total prediction{totalCount !== 1 ? "s" : ""}
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
      </div>
    </PageTransition>
  );
}
