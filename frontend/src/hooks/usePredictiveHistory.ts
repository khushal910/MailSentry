import { useEffect, useMemo } from "react";
import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { emailsApi, type GetEmailsResponse } from "@/services/emailsApi";
import { dashboardApi } from "@/services/dashboardApi";
import { DASHBOARD_STATS_QUERY_KEY } from "./useDashboardStats";
import { seedEmailSummaryQuery } from "./useEmailSummary";

export interface UsePredictiveHistoryOptions {
  page: number;
  limit?: number;
  label?: string;
  search?: string;
}

export const getHistoryQueryKey = (params: {
  page: number;
  limit?: number;
  label?: string;
  search?: string;
}) => {
  const activeLabel = params.label && params.label !== "all" ? params.label : undefined;
  const activeSearch = params.search?.trim() ? params.search.trim() : undefined;
  return [
    "history",
    {
      page: params.page,
      limit: params.limit ?? 10,
      label: activeLabel,
      search: activeSearch,
    },
  ];
};

/**
 * Automatically loads classified emails and dashboard statistics in the background
 * immediately after classification completes (or on navigation prefetch).
 * This ensures the user experiences instant zero-delay loading when visiting Classified Emails.
 */
export const prefetchClassifiedEmails = (
  queryClient: QueryClient,
  options?: { limit?: number; page?: number }
) => {
  const page = options?.page ?? 1;
  const limit = options?.limit ?? 15;

  // Invalidate any active history queries to ensure stale state is marked
  queryClient.invalidateQueries({ queryKey: ["history"] });
  queryClient.invalidateQueries({ queryKey: DASHBOARD_STATS_QUERY_KEY });

  // 1. Prefetch Classified Emails (default limit: 15 for history view)
  const p1 = queryClient.prefetchQuery({
    queryKey: ["history", { page, limit, label: undefined, search: undefined }],
    queryFn: () =>
      emailsApi.getEmails({
        page,
        limit,
      }),
    staleTime: 1000 * 60 * 5,
  });

  // 2. Prefetch Dashboard Home recent emails (limit: 8)
  const p2 = queryClient.prefetchQuery({
    queryKey: ["history", { page: 1, limit: 8, label: undefined, search: undefined }],
    queryFn: () =>
      emailsApi.getEmails({
        page: 1,
        limit: 8,
      }),
    staleTime: 1000 * 60 * 5,
  });

  // 3. Prefetch Dashboard Statistics
  const p3 = queryClient.prefetchQuery({
    queryKey: DASHBOARD_STATS_QUERY_KEY,
    queryFn: () => dashboardApi.getStats(),
    staleTime: 1000 * 60 * 5,
  });

  return Promise.allSettled([p1, p2, p3]);
};

export function usePredictiveHistory({
  page,
  limit = 10,
  label,
  search,
}: UsePredictiveHistoryOptions) {
  const queryClient = useQueryClient();

  const activeLabel = label && label !== "all" ? label : undefined;
  const activeSearch = search?.trim() ? search.trim() : undefined;

  const queryKey = ["history", { page, limit, label: activeLabel, search: activeSearch }];

  // 1. Primary Query for current page
  const query = useQuery<GetEmailsResponse, Error>({
    queryKey,
    queryFn: () =>
      emailsApi.getEmails({
        page,
        limit,
        label: activeLabel,
        search: activeSearch,
      }),
    staleTime: 1000 * 60 * 5, // 5 minutes fresh cache
    gcTime: 1000 * 60 * 15, // 15 minutes garbage collection
    placeholderData: (previousData) => previousData, // Smooth transition between pages
  });

  // 2. Automatically seed AI summary query cache for all emails in current page that already have summaries
  useEffect(() => {
    if (query.data?.emails && query.data.emails.length > 0) {
      query.data.emails.forEach((email) => {
        if (email.summary) {
          seedEmailSummaryQuery(queryClient, email);
        }
      });
    }
  }, [query.data?.emails, queryClient]);

  // 3. Predictive Idle Prefetching for Next Page
  useEffect(() => {
    if (!query.data || query.isFetching) return;

    const total = query.data.total_count ?? query.data.total ?? query.data.count ?? 0;
    const totalPages = Math.max(1, Math.ceil(total / limit));
    const nextPage = page + 1;

    if (nextPage <= totalPages) {
      const nextPageQueryKey = [
        "history",
        { page: nextPage, limit, label: activeLabel, search: activeSearch },
      ];

      // Schedule prefetch when main browser thread is idle
      const schedulePrefetch = () => {
        queryClient.prefetchQuery({
          queryKey: nextPageQueryKey,
          queryFn: () =>
            emailsApi.getEmails({
              page: nextPage,
              limit,
              label: activeLabel,
              search: activeSearch,
            }),
          staleTime: 1000 * 60 * 5,
        });
      };

      if (typeof window !== "undefined" && "requestIdleCallback" in window) {
        const win = window as unknown as {
          requestIdleCallback: (cb: () => void, opts?: { timeout: number }) => number;
          cancelIdleCallback: (id: number) => void;
        };
        const idleId = win.requestIdleCallback(schedulePrefetch, { timeout: 2000 });
        return () => {
          if ("cancelIdleCallback" in window) {
            win.cancelIdleCallback(idleId);
          }
        };
      } else {
        const timerId = setTimeout(schedulePrefetch, 200);
        return () => clearTimeout(timerId);
      }
    }
  }, [query.data, query.isFetching, page, limit, activeLabel, activeSearch, queryClient]);

  // Ensure latest emails are always listed first (descending by visible timestamp)
  const sortedEmails = useMemo(() => {
    const rawEmails = query.data?.emails ?? [];
    return [...rawEmails].sort((a, b) => {
      const getTimestamp = (item: {
        sent_at?: string | null;
        received_at?: string | null;
        classified_at?: string | null;
        fetch_time?: string | null;
      }) => {
        const dateCandidates = [
          item.sent_at,
          item.received_at,
          item.classified_at,
          item.fetch_time,
        ];
        for (const dateVal of dateCandidates) {
          if (!dateVal) continue;
          if (typeof dateVal === "number") return dateVal;
          const parsed = new Date(dateVal).getTime();
          if (!isNaN(parsed) && parsed > 0) return parsed;
        }
        return 0;
      };
      return getTimestamp(b) - getTimestamp(a); // Descending: Latest date (Today) first
    });
  }, [query.data?.emails]);

  return {
    emails: sortedEmails,
    totalCount: query.data?.total_count ?? query.data?.total ?? query.data?.count ?? 0,
    pageCount: Math.max(
      1,
      Math.ceil((query.data?.total_count ?? query.data?.total ?? query.data?.count ?? 0) / limit),
    ),
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isPlaceholderData: query.isPlaceholderData,
    error: query.error ? query.error.message : null,
    refetch: query.refetch,
  };
}
