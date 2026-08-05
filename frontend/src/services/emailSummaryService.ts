import apiClient from "./apiClient";

export interface EmailSummaryData {
  email_id: string;
  summary: string;
  summary_created_at?: string | null;
  summary_model?: string | null;
  cached: boolean;
}

export interface EmailSummaryApiResponse {
  success?: boolean;
  status_code?: number;
  message?: string;
  data: EmailSummaryData;
}

export const emailSummaryService = {
  /**
   * GET /emails/{email_id}/summary
   * Fetches or lazily generates a concise AI summary for an email document.
   *
   * @param emailId - The unique _id or message_id of the target email document.
   * @returns EmailSummaryData object containing summary, cached flag, and metadata.
   */
  async getEmailSummary(emailId: string): Promise<EmailSummaryData> {
    if (!emailId || !emailId.trim()) {
      throw new Error("Invalid email ID provided.");
    }

    const cleanId = emailId.trim();

    // Call GET /emails/{email_id}/summary using Axios apiClient
    const response = await apiClient.get<EmailSummaryApiResponse | EmailSummaryData>(
      `/api/emails/${cleanId}/summary`
    );

    // Support both wrapped response { data: { summary: "..." } } and direct payload
    const payload = response.data;
    if ("data" in payload && payload.data) {
      return payload.data;
    }

    return payload as EmailSummaryData;
  },
};

export default emailSummaryService;
