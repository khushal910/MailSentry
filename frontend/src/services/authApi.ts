import apiClient, { setAuthToken } from "./apiClient";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarUrl?: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export const authApi = {
  async login(payload: { email: string; password: string }) {
    const { data } = await apiClient.post<AuthResponse>("/api/v1/auth/login", payload);
    setAuthToken(data.token);
    return data;
  },
  async signup(payload: { name: string; email: string; password: string }) {
    const { data } = await apiClient.post<AuthResponse>("/api/v1/auth/signup", payload);
    setAuthToken(data.token);
    return data;
  },
  async forgotPassword(email: string) {
    const { data } = await apiClient.post<{ message: string }>(
      "/api/v1/auth/forgot-password",
      { email },
    );
    return data;
  },
  async resetPassword(payload: { token: string; password: string }) {
    const { data } = await apiClient.post<{ message: string }>(
      "/api/v1/auth/reset-password",
      payload,
    );
    return data;
  },
  async verifyEmail(token: string) {
    const { data } = await apiClient.post<{ message: string }>(
      "/api/v1/auth/verify-email",
      { token },
    );
    return data;
  },
  async me() {
    const { data } = await apiClient.get<AuthUser>("/api/v1/auth/me");
    return data;
  },
  logout() {
    setAuthToken(null);
  },
};
