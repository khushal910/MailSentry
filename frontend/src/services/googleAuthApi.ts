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

export type GoogleStatusResponse =
  | GoogleStatusConnectedResponse
  | GoogleStatusNotConnectedResponse;

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
   * POST /api/google/disconnect
   * Disconnects Google account for the authenticated user.
   */
  async disconnect(): Promise<{ success: boolean; message: string }> {
    const { data } = await apiClient.post<{ success: boolean; message: string }>(
      "/api/google/disconnect"
    );
    return data;
  },

  /**
   * Redirects browser to backend Google OAuth login flow.
   */
  initiateConnect() {
    const rawBase =
      (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL) ||
      "http://localhost:8000";
    const backendUrl = rawBase.replace("127.0.0.1", "localhost");
    window.location.href = `${backendUrl}/auth/google/login`;
  },
};
