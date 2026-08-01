import apiClient from "./apiClient";

export interface ClassifiedEmail {
  message_id: string;
  thread_id?: string | null;
  subject: string;
  snippet?: string | null;
  predicted_label: string;
  predicted_score?: number | null;
  fetch_time?: string;
  classified_at?: string;
}

export interface GetEmailsResponse {
  emails: ClassifiedEmail[];
  page: number;
  limit: number;
  count: number;
}

export const emailsApi = {
  /**
   * POST /api/gmail/fetch
   * Triggers fetching of new emails from Gmail and stores them classified.
   */
  async fetchEmails(): Promise<void> {
    await apiClient.post("/api/gmail/fetch");
  },

  /**
   * GET /api/emails
   * Returns paginated list of classified emails for the authenticated user.
   */
  async getEmails(params?: { limit?: number; page?: number; label?: string }): Promise<GetEmailsResponse> {
    const { data } = await apiClient.get<{ data: GetEmailsResponse }>("/api/emails", {
      params: {
        limit: params?.limit ?? 20,
        page: params?.page ?? 1,
        ...(params?.label ? { label: params.label } : {}),
      },
    });
    return data.data;
  },
};
