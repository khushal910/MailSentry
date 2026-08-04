import apiClient from "./apiClient";

export interface GoogleStatusConnectedResponse {
  connected: true;
  google_email: string;
  connected_at: string;
  last_updated: string;
}

export interface GoogleStatusNotConnectedResponse {
  connected: false;
}

export type GoogleStatusResponse = GoogleStatusConnectedResponse | GoogleStatusNotConnectedResponse;

export const googleAuthApi = {
  /**
   * GET /api/google/status
   * Retrieves Gmail connection status for the authenticated user.
   */
  async getStatus(): Promise<GoogleStatusResponse> {
    const { data } = await apiClient.get<GoogleStatusResponse>("/api/google/status");
    return data;
  },

  /**
   * GET /api/google/connect
   * Generates Google OAuth connect URL with access_type=offline & prompt=consent.
   */
  async getConnectUrl(): Promise<string> {
    const { data } = await apiClient.get<{
      success?: boolean;
      data?: { url?: string };
      url?: string;
    }>("/api/google/connect?format=json");

    const url = data?.data?.url || data?.url;
    if (!url) {
      throw new Error("Failed to generate Google connection URL.");
    }
    return url;
  },

  /**
   * Initiates Google OAuth connection by calling GET /api/google/connect and redirecting user.
   */
  async initiateConnect(): Promise<void> {
    const url = await this.getConnectUrl();
    window.location.href = url;
  },

  /**
   * POST /api/google/disconnect
   * Disconnects Google account for the authenticated user.
   */
  async disconnect(): Promise<{ success: boolean; message: string }> {
    const { data } = await apiClient.post<{ success: boolean; message: string }>(
      "/api/google/disconnect",
    );
    return data;
  },
};
