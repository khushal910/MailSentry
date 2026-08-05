import apiClient from "./apiClient";

export interface ClassifiedEmail {
  message_id: string;
  thread_id?: string | null;
  subject: string;
  snippet?: string | null;
  sender?: string | null;
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

export interface UnclassifiedEmail {
  message_id: string;
  gmail_message_id?: string;
  thread_id?: string | null;
  subject: string;
  snippet?: string | null;
  received_at?: string | null;
  sent_at?: string | null;
}

export interface FetchUnclassifiedResult {
  fetched: number;
  unclassified_emails: UnclassifiedEmail[];
}

export interface ClassifyBatchResult {
  classified: number;
  skipped: number;
  classified_emails: ClassifiedEmail[];
}

export interface JobStatusResponse {
  job_id: string;
  status: "started" | "running" | "completed" | "failed";
  total: number;
  processed: number;
  classified: number;
  skipped: number;
  current_subject?: string | null;
  result?: ClassifyBatchResult | null;
  error?: string | null;
}

export const emailsApi = {
  /**
   * POST /api/gmail/fetch-unclassified
   * Fetches unclassified raw emails from Gmail (emails not yet in MongoDB).
   */
  async fetchUnclassifiedEmails(): Promise<FetchUnclassifiedResult> {
    const { data } = await apiClient.post<{ data: FetchUnclassifiedResult }>(
      "/api/gmail/fetch-unclassified",
    );
    return data.data ?? { fetched: 0, unclassified_emails: [] };
  },

  /**
   * POST /api/gmail/classify-job
   * Starts an asynchronous background classification job and returns immediately with job_id.
   */
  async startClassifyJob(emails: UnclassifiedEmail[]): Promise<JobStatusResponse> {
    const { data } = await apiClient.post<{ data: JobStatusResponse }>("/api/gmail/classify-job", {
      emails,
    });
    return data.data;
  },

  /**
   * GET /api/gmail/jobs/:job_id
   * Polls progress of an active background classification job.
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const { data } = await apiClient.get<{ data: JobStatusResponse }>(`/api/gmail/jobs/${jobId}`);
    return data.data;
  },

  /**
   * POST /api/gmail/classify
   * Classifies specified unclassified emails using ML model, saves predictions to MongoDB, and returns classified records.
   */
  async classifyEmails(emails: UnclassifiedEmail[]): Promise<ClassifyBatchResult> {
    const { data } = await apiClient.post<{ data: ClassifyBatchResult }>("/api/gmail/classify", {
      emails,
    });
    return data.data ?? { classified: 0, skipped: 0, classified_emails: [] };
  },

  /**
   * POST /api/gmail/fetch
   * Triggers fetching and classifying new emails from Gmail.
   */
  async fetchEmails(): Promise<FetchResult> {
    const { data } = await apiClient.post<{ data: FetchResult }>("/api/gmail/fetch");
    return data.data ?? { fetched: 0, classified: 0, skipped: 0 };
  },

  /**
   * GET /api/emails
   * Returns paginated list of classified emails for the authenticated user with optional search query.
   */
  async getEmails(params?: {
    limit?: number;
    page?: number;
    label?: string;
    search?: string;
  }): Promise<GetEmailsResponse> {
    const { data } = await apiClient.get<{ data: GetEmailsResponse }>("/api/emails", {
      params: {
        limit: params?.limit ?? 20,
        page: params?.page ?? 1,
        ...(params?.label ? { label: params.label } : {}),
        ...(params?.search ? { search: params.search } : {}),
      },
    });
    return data.data;
  },

  /**
   * GET /emails/{email_id}/summary
   * Returns AI summary for specified email_id using Gemini API.
   */
  async getEmailSummary(emailId: string) {
    const { emailSummaryService } = await import("./emailSummaryService");
    return emailSummaryService.getEmailSummary(emailId);
  },
};
