import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Search, X, RefreshCw, Sparkles, ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react";

import { PageTransition } from "@/components/PageTransition";
import { ClassifiedEmailsTable } from "@/components/ClassifiedEmailsTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDebounce } from "@/hooks/useDebounce";
import { usePredictiveHistory } from "@/hooks/usePredictiveHistory";

export const Route = createFileRoute("/dashboard/history")({
  head: () => ({
    meta: [
      { title: "Classified Emails — MailSentry" },
      {
        name: "description",
        content: "Search, filter, and inspect all classified emails in your database.",
      },
    ],
  }),
  component: HistoryPage,
});

const PAGE_SIZE = 15;

function HistoryPage() {
  // Search and Filter states
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearch = useDebounce(searchTerm, 250);

  const [filter, setFilter] = useState<string>("all");
  const [page, setPage] = useState(1);

  // TanStack Query with Intelligent Predictive Idle Prefetching
  const { emails, totalCount, pageCount, isLoading, isFetching, error } = usePredictiveHistory({
    page,
    limit: PAGE_SIZE,
    label: filter,
    search: debouncedSearch,
  });

  return (
    <PageTransition>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Classified Emails</h1>

          <p className="mt-1 text-sm text-muted-foreground">
            All classified emails stored in your MailSentry database.
          </p>

          <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
            {/* Category Legend */}
            <span className="inline-flex items-center gap-1.5 rounded-full bg-muted/60 px-3 py-1 font-medium text-foreground border border-border/70 shadow-xs">
              <span className="text-muted-foreground font-semibold">Category:</span>
              <span className="inline-flex items-center gap-1 text-destructive font-semibold">
                <ShieldAlert className="h-3.5 w-3.5" /> Spam
              </span>
              <span className="mx-0.5 opacity-40">·</span>
              <span className="inline-flex items-center gap-1 text-emerald-500 font-semibold">
                <ShieldCheck className="h-3.5 w-3.5" /> Safe
              </span>
              <span className="mx-0.5 opacity-40">·</span>
              <span className="inline-flex items-center gap-1 text-amber-500 font-bold">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500 animate-pulse" /> Disagreement with Gmail
              </span>
            </span>

            {/* AI Summary Tip Badge */}
            <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-brand/20 via-purple-500/15 to-primary/20 px-3.5 py-1 text-xs font-semibold text-primary border border-primary/30 shadow-xs backdrop-blur-xs transition-all hover:border-primary/60 hover:shadow-soft">
              <Sparkles className="h-3.5 w-3.5 text-brand animate-pulse" />
              <span>Click any row for <strong className="text-foreground font-bold">AI Summary & Details</strong></span>
            </span>
          </div>
        </div>

        {(isFetching || isLoading) && (
          <div className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary shadow-sm">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            <span className="hidden sm:inline">
              {isLoading ? "Loading Classified Emails..." : "Syncing Emails"}
            </span>
          </div>
        )}
      </div>

      {/* Main Container */}
      <div className="glass mt-6 rounded-2xl p-4 md:p-6 border border-border/60 shadow-lg">
        {/* Search & Filter Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[240px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="emails-search-input"
              placeholder="Search by subject, body, sender, or prediction…"
              className="pl-9 pr-8 bg-background/50 border-border/60 focus:border-brand"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
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

        {/* Interactive Classified Emails Table */}
        <div className="mt-5">
          <ClassifiedEmailsTable
            emails={emails}
            isLoading={isLoading}
            searchQuery={debouncedSearch}
            isCompact={false}
            page={page}
            pageSize={PAGE_SIZE}
            emptyMessage={debouncedSearch.trim() ? `No emails matching "${debouncedSearch}"` : "No stored emails found in database"}
            emptySubtitle={debouncedSearch.trim() ? "Try clearing your search query or adjusting the category filter." : "Fetch emails in the Auto Classifier page to view classified emails."}
          />
        </div>

        {/* Pagination Bar */}
        {isLoading ? (
          <div className="mt-5 flex items-center justify-between border-t border-border/40 pt-4 text-xs text-muted-foreground animate-pulse">
            <div className="h-4 w-32 rounded bg-muted/50" />
            <div className="flex gap-2">
              <div className="h-8 w-18 rounded-md bg-muted/40" />
              <div className="h-8 w-14 rounded-md bg-muted/40" />
            </div>
          </div>
        ) : totalCount > 0 ? (
          <div className="mt-5 flex items-center justify-between border-t border-border/40 pt-4 text-xs text-muted-foreground">
            <span>
              Page {page} of {pageCount} · {totalCount} total email
              {totalCount !== 1 ? "s" : ""}
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
        ) : null}
      </div>
    </PageTransition>
  );
}


