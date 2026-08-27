import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { emailSummaryService, type EmailSummaryData } from "@/services/emailSummaryService";
import type { ClassifiedEmail } from "@/services/emailsApi";

export const EMAIL_SUMMARY_QUERY_KEY = "email-summary";

/**
 * Builds the unique TanStack Query key for a given email summary.
 */
export const getEmailSummaryQueryKey = (emailId?: string | null) => [
  EMAIL_SUMMARY_QUERY_KEY,
  emailId ? String(emailId).trim() : "",
];

/**
 * Highly-optimized TanStack Query hook for AI Email Summaries.
 * - Instant 0ms memory retrieval on repeat opens (no loading spinners).
 * - 24-hour cache persistence to prevent duplicate network calls.
 * - Background generation on first encounter with seamless optimistic updates.
 */
export function useEmailSummary(
  emailId?: string | null,
  options?: {
    enabled?: boolean;
    initialData?: EmailSummaryData;
  }
) {
  const cleanId = emailId ? String(emailId).trim() : "";
  const isEnabled = options?.enabled !== false && Boolean(cleanId);

  return useQuery<EmailSummaryData, Error>({
    queryKey: getEmailSummaryQueryKey(cleanId),
    queryFn: async () => {
      if (!cleanId) throw new Error("Email ID is required");
      return await emailSummaryService.getEmailSummary(cleanId);
    },
    enabled: isEnabled,
    staleTime: 1000 * 60 * 60 * 24, // 24 hours fresh (instant 0ms response)
    gcTime: 1000 * 60 * 60 * 24, // 24 hours garbage collection retention
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    retry: 1,
    initialData: options?.initialData,
  });
}

/**
 * Proactively prefetches an email summary into memory when the user hovers over
 * a table row, button, or link, ensuring 0ms instant loading when clicked.
 */
export function prefetchEmailSummary(
  queryClient: QueryClient,
  emailId?: string | null
): void {
  if (!emailId || !queryClient) return;
  const cleanId = String(emailId).trim();
  if (!cleanId) return;

  const key = getEmailSummaryQueryKey(cleanId);
  const existing = queryClient.getQueryData<EmailSummaryData>(key);

  // If already in TanStack cache, avoid prefetching
  if (existing) return;

  queryClient.prefetchQuery({
    queryKey: key,
    queryFn: () => emailSummaryService.getEmailSummary(cleanId),
    staleTime: 1000 * 60 * 60 * 24,
  });
}

/**
 * Seeds the TanStack query cache directly from pre-existing email documents
 * (e.g. from the classified emails list) so clicking them opens instantly without any network request.
 */
export function seedEmailSummaryQuery(
  queryClient: QueryClient,
  email: Partial<ClassifiedEmail>
): void {
  if (!email || !queryClient) return;
  if (!email.summary || !email.summary.trim()) return;

  const primaryId = email.message_id || email.email_id || email.id || email._id;
  if (!primaryId) return;

  const summaryData: EmailSummaryData = {
    email_id: String(primaryId),
    subject: email.subject || "",
    sender: email.sender || undefined,
    receiver: email.receiver || undefined,
    predicted_label: email.predicted_label,
    predicted_score: email.predicted_score !== null ? email.predicted_score : undefined,
    sent_at: email.sent_at || email.received_at || email.classified_at || undefined,
    body: email.body || email.snippet || undefined,
    summary: email.summary.trim(),
    summary_created_at: email.summary_created_at || null,
    summary_model: email.summary_model || null,
    cached: true,
    message_id: email.message_id,
    thread_id: email.thread_id || undefined,
  };

  // Seed TanStack query cache under all available ID keys
  const keysToSeed = new Set<string>();
  if (primaryId) keysToSeed.add(String(primaryId).trim());
  if (email.message_id) keysToSeed.add(String(email.message_id).trim());
  if (email.email_id) keysToSeed.add(String(email.email_id).trim());
  if (email._id) keysToSeed.add(String(email._id).trim());
  if (email.id) keysToSeed.add(String(email.id).trim());

  keysToSeed.forEach((k) => {
    if (k) {
      queryClient.setQueryData(getEmailSummaryQueryKey(k), summaryData);
    }
  });

  // Also seed emailSummaryService client memory cache
  emailSummaryService.seedCache(summaryData);
}

/**
 * Force-invalidates and regenerates an email summary for a specific email.
 */
export async function regenerateEmailSummary(
  queryClient: QueryClient,
  emailId: string
): Promise<EmailSummaryData> {
  const cleanId = String(emailId).trim();
  emailSummaryService.clearCache(cleanId);

  // Call API directly with forceRefresh
  const freshData = await emailSummaryService.getEmailSummary(cleanId, true);

  // Update query client cache immediately
  queryClient.setQueryData(getEmailSummaryQueryKey(cleanId), freshData);
  if (freshData.message_id) {
    queryClient.setQueryData(getEmailSummaryQueryKey(freshData.message_id), freshData);
  }
  if (freshData.email_id) {
    queryClient.setQueryData(getEmailSummaryQueryKey(freshData.email_id), freshData);
  }

  return freshData;
}
