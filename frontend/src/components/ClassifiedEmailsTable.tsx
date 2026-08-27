import React, { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { MailX, Sparkles } from "lucide-react";
import { GmailSpamIndicator } from "./GmailSpamIndicator";
import { GmailOpenButton } from "./GmailOpenButton";
import { HighlightText } from "./HighlightText";
import { formatConfidence, formatDate, truncate } from "@/utils/format";
import type { ClassifiedEmail } from "@/services/emailsApi";
import { prefetchEmailSummary, seedEmailSummaryQuery } from "@/hooks/useEmailSummary";

export interface ClassifiedEmailsTableProps {
  emails: ClassifiedEmail[];
  isLoading?: boolean;
  searchQuery?: string;
  isCompact?: boolean;
  page?: number;
  pageSize?: number;
  onRowClick?: (email: ClassifiedEmail) => void;
  emptyMessage?: string;
  emptySubtitle?: string;
}

export const ClassifiedEmailsTable: React.FC<ClassifiedEmailsTableProps> = ({
  emails,
  isLoading = false,
  searchQuery = "",
  isCompact = false,
  page = 1,
  pageSize = 10,
  onRowClick,
  emptyMessage = "No classified emails found",
  emptySubtitle = "Emails fetched from Gmail or processed by the classifier will appear here.",
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Automatically seed TanStack query cache for all emails in this page that already have summaries
  useEffect(() => {
    if (emails && emails.length > 0) {
      emails.forEach((email) => {
        if (email.summary) {
          seedEmailSummaryQuery(queryClient, email);
        }
      });
    }
  }, [emails, queryClient]);

  const handleRowClick = (email: ClassifiedEmail, e: React.MouseEvent) => {
    // Prevent navigation if clicking interactive child elements (e.g. Gmail open button or external link)
    const target = e.target as HTMLElement;
    if (target.closest("button, a, input, select, [role='button']")) return;

    if (onRowClick) {
      onRowClick(email);
      return;
    }

    const targetId = email.message_id || (email as any)._id || (email as any).id;
    if (targetId) {
      navigate({
        to: "/dashboard/email-summary/$emailId",
        params: { emailId: String(targetId) },
      });
    }
  };

  if (isLoading) {
    return (
      <div className="py-12 space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="flex items-center justify-between gap-4 p-3.5 rounded-xl bg-muted/20 animate-pulse border border-border/30"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="h-4 w-20 rounded bg-muted/60" />
              <div className="h-4 w-48 rounded bg-muted/80" />
            </div>
            <div className="h-6 w-20 rounded-full bg-muted/40" />
            <div className="h-4 w-12 rounded bg-muted/50" />
          </div>
        ))}
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2.5 py-12 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted/40 text-muted-foreground border border-border/40">
          <MailX className="h-6 w-6" />
        </div>
        <p className="text-sm font-semibold text-foreground">{emptyMessage}</p>
        <p className="max-w-md text-xs text-muted-foreground">{emptySubtitle}</p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground">
            {!isCompact && <th className="pb-3 text-left font-medium w-[5%] pl-2">#</th>}
            <th className={`pb-3 text-left font-medium ${isCompact ? "w-[22%]" : "w-[16%]"}`}>
              {isCompact ? "Date" : "Email Sent Date"}
            </th>
            <th className={`pb-3 text-left font-medium ${isCompact ? "w-[42%]" : "w-[26%]"}`}>
              Subject
            </th>
            {!isCompact && <th className="pb-3 text-left font-medium w-[24%]">Snippet</th>}
            <th className={`pb-3 text-left font-medium ${isCompact ? "w-[18%]" : "w-[13%]"}`}>
              Category
            </th>
            <th className={`pb-3 text-left font-medium ${isCompact ? "w-[10%]" : "w-[9%]"}`}>
              Score
            </th>
            <th className={`pb-3 text-center font-medium ${isCompact ? "w-[8%]" : "w-[7%]"}`}>
              Open
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30">
          {emails.map((email, index) => {
            const rowNumber = (page - 1) * pageSize + index + 1;
            const dateVal =
              email.sent_at || email.received_at || email.classified_at || email.fetch_time;

            const targetId = email.message_id || (email as any)._id || (email as any).id;

            return (
              <motion.tr
                key={email.message_id || index}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15, delay: index * 0.02 }}
                onClick={(e) => handleRowClick(email, e)}
                onMouseEnter={() => targetId && prefetchEmailSummary(queryClient, String(targetId))}
                onFocus={() => targetId && prefetchEmailSummary(queryClient, String(targetId))}
                className="group transition-colors hover:bg-muted/40 cursor-pointer border-b border-border/40 last:border-0"
              >
                {!isCompact && (
                  <td className="py-3 pl-2 text-xs font-semibold text-muted-foreground align-middle">
                    {rowNumber}
                  </td>
                )}
                <td className="py-3 text-xs text-muted-foreground font-medium align-middle whitespace-nowrap pr-2">
                  {dateVal ? formatDate(dateVal) : "—"}
                </td>
                <td className="py-3 align-middle pr-3">
                  <div className="flex items-center gap-1.5 font-medium text-foreground group-hover:text-primary transition-colors">
                    <HighlightText
                      text={truncate(email.subject || "(no subject)", isCompact ? 50 : 38)}
                      query={searchQuery}
                    />
                    <Sparkles className="h-3 w-3 text-primary shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  {email.sender && (
                    <p className="text-xs text-muted-foreground/80 truncate max-w-sm mt-0.5">
                      {email.sender}
                    </p>
                  )}
                </td>
                {!isCompact && (
                  <td className="py-3 text-xs text-muted-foreground align-middle pr-3">
                    <HighlightText
                      text={truncate(email.snippet || "—", 42)}
                      query={searchQuery}
                    />
                  </td>
                )}
                <td className="py-3 align-middle whitespace-nowrap pr-2">
                  <GmailSpamIndicator
                    mailsentryLabel={email.predicted_label}
                    gmailClassification={email.gmail_classification}
                  />
                </td>
                <td className="py-3 text-left font-medium text-xs align-middle whitespace-nowrap">
                  {typeof email.predicted_score === "number"
                    ? formatConfidence(email.predicted_score)
                    : "—"}
                </td>
                <td className="py-3 text-center align-middle">
                  <GmailOpenButton
                    messageId={email.message_id}
                    threadId={email.thread_id}
                  />
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
