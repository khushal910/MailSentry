import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { PredictionBadge } from "@/components/PredictionBadge";
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

export const Route = createFileRoute("/dashboard/history")({
  head: () => ({
    meta: [
      { title: "History — MailSentry" },
      { name: "description", content: "Search and filter every prediction MailSentry has made." },
    ],
  }),
  component: HistoryPage,
});

type Row = {
  id: string;
  date: string;
  subject: string;
  prediction: "Spam" | "Ham";
  confidence: number;
};

const seed: Row[] = Array.from({ length: 47 }).map((_, i) => {
  const isSpam = i % 3 === 0;
  return {
    id: String(i + 1),
    date: new Date(Date.now() - i * 3.6e6).toISOString(),
    subject: isSpam
      ? [
          "Claim your free crypto reward",
          "URGENT: account will be locked",
          "You won a $500 Amazon gift card",
          "Verify your bank details now",
        ][i % 4]
      : [
          "Sprint planning notes",
          "Q3 board deck draft",
          "Design review — Wed 3pm",
          "Weekly newsletter",
        ][i % 4],
    prediction: isSpam ? "Spam" : "Ham",
    confidence: 80 + Math.random() * 19,
  };
});

const PAGE_SIZE = 8;

function HistoryPage() {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "spam" | "ham">("all");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    return seed.filter((r) => {
      if (filter === "spam" && r.prediction !== "Spam") return false;
      if (filter === "ham" && r.prediction !== "Ham") return false;
      if (q && !r.subject.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [q, filter]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <PageTransition>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">History</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Every classification MailSentry has run for you.
        </p>
      </div>

      <div className="glass mt-6 rounded-2xl p-4 md:p-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search subject…"
              className="pl-9"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <Select
            value={filter}
            onValueChange={(v) => {
              setFilter(v as typeof filter);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All predictions</SelectItem>
              <SelectItem value="spam">Spam only</SelectItem>
              <SelectItem value="ham">Safe only</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
                <th className="pb-3 text-left font-medium">Date</th>
                <th className="pb-3 text-left font-medium">Subject</th>
                <th className="pb-3 text-left font-medium">Prediction</th>
                <th className="pb-3 text-right font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-muted-foreground">
                    No predictions match your filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((r) => (
                  <tr key={r.id} className="border-b border-border/40 last:border-0">
                    <td className="py-3 text-muted-foreground">{formatDate(r.date)}</td>
                    <td className="py-3">{truncate(r.subject, 60)}</td>
                    <td className="py-3">
                      <PredictionBadge prediction={r.prediction} />
                    </td>
                    <td className="py-3 text-right font-medium">
                      {formatConfidence(r.confidence)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Page {page} of {pageCount} · {filtered.length} results
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
      </div>
    </PageTransition>
  );
}
