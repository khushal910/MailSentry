import apiClient from "./apiClient";

export interface DashboardStats {
  total_predictions: number;
  spam_emails: number;
  safe_emails: number;
  accuracy?: number | null;
  average_confidence: number;
  today_predictions: number;
  last_week_predictions: number;
  this_week_predictions: number;
  spam_percentage: number;
  safe_percentage: number;
  growth_percentage?: number | null;
}

export const dashboardApi = {
  /**
   * GET /api/dashboard/stats
   * Fetches real aggregated statistics for the currently logged-in user.
   */
  async getStats(): Promise<DashboardStats> {
    const { data } = await apiClient.get<DashboardStats | { data: DashboardStats }>(
      "/api/dashboard/stats",
    );
    // Handle standard return_response envelope { success, status_code, message, data }
    const statsData: DashboardStats =
      "data" in data && data.data ? data.data : (data as DashboardStats);
    return statsData;
  },
};
