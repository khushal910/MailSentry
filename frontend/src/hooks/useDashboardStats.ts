import { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi, type DashboardStats } from "@/services/dashboardApi";

export const DASHBOARD_STATS_QUERY_KEY = ["dashboard", "stats"];

/**
 * Custom hook to fetch and manage dashboard statistics for the active user.
 * Supports React Query caching while also exposing clean loading/error/refetch states.
 */
export function useDashboardStats() {
  const query = useQuery({
    queryKey: DASHBOARD_STATS_QUERY_KEY,
    queryFn: () => dashboardApi.getStats(),
    staleTime: 30_000,
    retry: 2,
  });

  return {
    stats: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error ? (query.error as Error).message : null,
    refetch: query.refetch,
  };
}
