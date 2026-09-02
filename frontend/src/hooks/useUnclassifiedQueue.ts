import { useState } from "react";
import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { emailsApi, type UnclassifiedEmail } from "@/services/emailsApi";
import { googleAuthApi } from "@/services/googleAuthApi";

export const UNCLASSIFIED_EMAILS_QUERY_KEY = ["unclassified-emails"] as const;

/**
 * Background prefetch helper:
 * Silently fetches unclassified raw emails from Gmail and primes the TanStack Query cache.
 * Executes completely asynchronously in the background — NEVER blocks navigation, auth, or other services.
 */
export async function prefetchUnclassifiedEmails(
  queryClient: QueryClient,
): Promise<UnclassifiedEmail[]> {
  try {
    // Check if Google account is connected before attempting fetch
    const status = await googleAuthApi.getStatus();
    if (!status.connected) {
      return [];
    }

    // Directly execute network fetch without being blocked by staleTime
    const result = await emailsApi.fetchUnclassifiedEmails();
    const emails = result.unclassified_emails || [];
    queryClient.setQueryData<UnclassifiedEmail[]>(UNCLASSIFIED_EMAILS_QUERY_KEY, emails);
    return emails;
  } catch (err) {
    // Non-blocking: background sync failures are logged quietly without interrupting other services
    console.debug("[Background Fetch] Silent Gmail unclassified queue sync skipped or failed:", err);
    return [];
  }
}

/**
 * React hook to access and manage the unclassified emails queue.
 * - Does NOT auto-fetch on mount (prevents blocking spinners on navigation).
 * - Reads immediately from the primed cache populated during login / background sync.
 * - Always triggers a real Gmail network fetch when `fetchQueue` is called explicitly by the user.
 */
export function useUnclassifiedQueue() {
  const queryClient = useQueryClient();
  const [isFetchingQueue, setIsFetchingQueue] = useState(false);

  const query = useQuery<UnclassifiedEmail[]>({
    queryKey: UNCLASSIFIED_EMAILS_QUERY_KEY,
    queryFn: async () => {
      const result = await emailsApi.fetchUnclassifiedEmails();
      return result.unclassified_emails || [];
    },
    staleTime: Infinity,
    gcTime: 1000 * 60 * 30, // 30 minutes cache retention
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    enabled: false, // Never automatically fetch on mount
  });

  const setEmails = (
    updater: UnclassifiedEmail[] | ((prev: UnclassifiedEmail[]) => UnclassifiedEmail[]),
  ) => {
    queryClient.setQueryData<UnclassifiedEmail[]>(UNCLASSIFIED_EMAILS_QUERY_KEY, (prev = []) => {
      if (typeof updater === "function") {
        return updater(prev);
      }
      return updater;
    });
  };

  /**
   * Explicitly fetches new unclassified emails from Gmail.
   * Bypasses cache check so real live messages are queried over HTTP.
   */
  const fetchQueue = async (): Promise<UnclassifiedEmail[]> => {
    setIsFetchingQueue(true);
    try {
      const result = await emailsApi.fetchUnclassifiedEmails();
      const emails = result.unclassified_emails || [];
      queryClient.setQueryData<UnclassifiedEmail[]>(UNCLASSIFIED_EMAILS_QUERY_KEY, emails);
      return emails;
    } finally {
      setIsFetchingQueue(false);
    }
  };

  return {
    emails: query.data ?? [],
    isFetching: query.isFetching || isFetchingQueue,
    setEmails,
    fetchQueue,
  };
}
