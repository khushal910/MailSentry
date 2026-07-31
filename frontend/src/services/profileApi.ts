import apiClient from "./apiClient";
import type { AuthUser } from "./authApi";

export interface UpdateProfileInput {
  name?: string;
  email?: string;
  avatarUrl?: string;
}

export const profileApi = {
  async get() {
    const { data } = await apiClient.get<AuthUser>("/api/v1/profile");
    return data;
  },
  async update(payload: UpdateProfileInput) {
    const { data } = await apiClient.patch<AuthUser>("/api/v1/profile", payload);
    return data;
  },
  async changePassword(payload: { currentPassword: string; newPassword: string }) {
    await apiClient.post("/api/v1/profile/password", payload);
  },
  async deleteAccount() {
    await apiClient.delete("/api/v1/profile");
  },
};
