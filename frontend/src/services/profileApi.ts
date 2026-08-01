import apiClient from "./apiClient";

export interface UserProfile {
  id: string;
  username: string;
  email: string;

  role: string;
  providers: string[];
  is_active: boolean;
  google_connected: boolean;
  google_email?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  notice?: string | null;
}

export interface ProfileResponseEnvelope {
  success: boolean;
  status_code: number;
  message: string;
  data: UserProfile;
}

export interface UpdateUsernameResponseEnvelope {
  success: boolean;
  status_code: number;
  message: string;
  data: {
    profile: UserProfile;
    token: string;
  };
}

export interface RequestEmailChangeResponseEnvelope {
  success: boolean;
  status_code: number;
  message: string;
  data: {
    message: string;
    pending_email: string;
    expires_in_seconds: number;
  };
}

export interface VerifyEmailOtpResponseEnvelope {
  success: boolean;
  status_code: number;
  message: string;
  data: {
    profile: UserProfile;
    token: string;
  };
}

export const profileApi = {
  /**
   * GET /api/profile
   * Returns current user profile information including role, providers, creation date,
   * and linked Google account status.
   */
  async getProfile(): Promise<UserProfile> {
    const { data } = await apiClient.get<ProfileResponseEnvelope>("/api/profile");
    return data.data;
  },

  /**
   * PATCH /api/profile/username
   * Updates username, regenerates JWT access token, and updates HttpOnly cookie.
   */
  async updateUsername(username: string): Promise<UserProfile> {
    const { data } = await apiClient.patch<UpdateUsernameResponseEnvelope>("/api/profile/username", { username });
    return data.data.profile;
  },

  /**
   * POST /api/profile/request-email-change
   * Triggers 6-digit OTP verification email for new email address.
   */
  async requestEmailChange(new_email: string) {
    const { data } = await apiClient.post<RequestEmailChangeResponseEnvelope>("/api/profile/request-email-change", { new_email });
    return data.data;
  },

  /**
   * POST /api/profile/verify-email-otp
   * Verifies 6-digit OTP, completes email change, and updates HttpOnly token cookie.
   */
  async verifyEmailOtp(otp: string): Promise<{ profile: UserProfile; message: string }> {
    const { data } = await apiClient.post<VerifyEmailOtpResponseEnvelope>("/api/profile/verify-email-otp", { otp });
    return { profile: data.data.profile, message: data.message };
  },

  /**
   * POST /api/profile/password
   * Changes password for local accounts.
   */
  async changePassword(payload: { current_password: string; new_password: string; confirm_password: string }) {

    const { data } = await apiClient.post<{ message: string }>("/api/profile/password", payload);
    return data;
  },
};
