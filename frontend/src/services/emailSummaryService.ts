import apiClient from "./apiClient";

export interface EmailSummaryData {
  email_id: string;
  subject?: string;
  sender?: string;
  receiver?: string;
  predicted_label?: string;
  predicted_score?: number;
  sent_at?: string;
  body?: string;
  summary: string;
  summary_created_at?: string | null;
  summary_model?: string | null;
  cached: boolean;
  message_id?: string;
  thread_id?: string;
}

export interface EmailSummaryApiResponse {
  success?: boolean;
  status_code?: number;
  message?: string;
  data: EmailSummaryData;
}

// In-memory client cache for instantaneous 0ms repeat retrievals
const _clientCache = new Map<string, EmailSummaryData>();

export const emailSummaryService = {
  /**
   * GET /emails/{email_id}/summary
   * Fetches or lazily generates a concise AI summary for an email document.
   *
   * @param emailId - The unique _id or message_id of the target email document.
   * @param forceRefresh - If true, bypasses client memory cache and requests fresh generation.
   * @returns EmailSummaryData object containing summary, cached flag, and metadata.
   */
  async getEmailSummary(emailId: string, forceRefresh: boolean = false): Promise<EmailSummaryData> {
    if (!emailId || !emailId.trim()) {
      throw new Error("Invalid email ID provided.");
    }

    const cleanId = emailId.trim();

    // 0ms In-Memory Client Cache check
    if (!forceRefresh && _clientCache.has(cleanId)) {
      return _clientCache.get(cleanId)!;
    }

    // Call GET /emails/{email_id}/summary using Axios apiClient
    const response = await apiClient.get<EmailSummaryApiResponse | EmailSummaryData>(
      `/api/emails/${cleanId}/summary`
    );

    // Support both wrapped response { data: { summary: "..." } } and direct payload
    const payload = response.data;
    const summaryData = (("data" in payload && payload.data) ? payload.data : payload) as EmailSummaryData;

    // Cache locally for instantaneous sub-millisecond future hits
    this.seedCache(summaryData);
    if (cleanId) {
      _clientCache.set(cleanId, summaryData);
    }

    return summaryData;
  },

  /**
   * Seeds the in-memory cache directly with known email summary data.
   */
  seedCache(data: Partial<EmailSummaryData> & { summary: string }): void {
    if (!data || !data.summary || !data.summary.trim()) return;

    const fullData: EmailSummaryData = {
      email_id: data.email_id || data.message_id || "",
      subject: data.subject,
      sender: data.sender,
      receiver: data.receiver,
      predicted_label: data.predicted_label,
      predicted_score: data.predicted_score,
      sent_at: data.sent_at,
      body: data.body,
      summary: data.summary,
      summary_created_at: data.summary_created_at,
      summary_model: data.summary_model,
      cached: data.cached !== undefined ? data.cached : true,
      message_id: data.message_id,
      thread_id: data.thread_id,
    };

    if (fullData.email_id) _clientCache.set(fullData.email_id, fullData);
    if (fullData.message_id) _clientCache.set(fullData.message_id, fullData);
  },

  /**
   * Clears in-memory client cache for a specific email or all emails.
   */
  clearCache(emailId?: string): void {
    if (emailId) {
      const clean = emailId.trim();
      _clientCache.delete(clean);
    } else {
      _clientCache.clear();
    }
  },
};

export default emailSummaryService;
