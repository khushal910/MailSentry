import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { emailsApi, type GetEmailsResponse } from "@/services/emailsApi";

export interface UsePredictiveHistoryOptions {
  page: number;
  limit?: number;
  label?: string;
  search?: string;
}

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

  // 2. Predictive Idle Prefetching for Next Page
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
        const idleId = (window as any).requestIdleCallback(schedulePrefetch, { timeout: 2000 });
        return () => {
          if ("cancelIdleCallback" in window) {
            (window as any).cancelIdleCallback(idleId);
          }
        };
      } else {
        const timerId = setTimeout(schedulePrefetch, 200);
        return () => clearTimeout(timerId);
      }
    }
  }, [query.data, query.isFetching, page, limit, activeLabel, activeSearch, queryClient]);

  return {
    emails: query.data?.emails ?? [],
    totalCount: query.data?.total_count ?? query.data?.total ?? query.data?.count ?? 0,
    pageCount: Math.max(
      1,
      Math.ceil((query.data?.total_count ?? query.data?.total ?? query.data?.count ?? 0) / limit)
    ),
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isPlaceholderData: query.isPlaceholderData,
    error: query.error ? query.error.message : null,
    refetch: query.refetch,
  };
}
