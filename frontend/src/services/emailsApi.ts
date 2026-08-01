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
  received_at?: string | null;
  sent_at?: string | null;
}


export interface GetEmailsResponse {
  emails: ClassifiedEmail[];
  page: number;
  limit: number;
  count: number;
  total_count?: number;
  total?: number;
}

export interface FetchResult {
  fetched: number;
  classified: number;
  skipped: number;
  new_emails?: ClassifiedEmail[];
}


export const emailsApi = {
  /**
   * POST /api/gmail/fetch
   * Triggers fetching and classifying new emails from Gmail.
   * Returns structured summary: { fetched, classified, skipped }.
   * Throws on 403 (revoked) or 429 (rate limit / lock) — caller should handle.
   */
  async fetchEmails(): Promise<FetchResult> {
    const { data } = await apiClient.post<{ data: FetchResult }>("/api/gmail/fetch");
    return data.data ?? { fetched: 0, classified: 0, skipped: 0 };
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

