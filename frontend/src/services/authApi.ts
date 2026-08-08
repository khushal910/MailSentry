import axios from "axios";
import apiClient from "./apiClient";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
  is_admin?: boolean;
  avatarUrl?: string;
}


export interface BackendResponse {
  success: boolean;
  status_code: number;
  message: string;
}

/**
 * Tries an API call that returns a BackendResponse.
 * If the server responds with a non-2xx status but the body still carries
 * {success, message} (e.g. 400 "username already exists"), we return that
 * body as a normal result instead of throwing.
 * Any other error (network, 500, etc.) is re-thrown.
 */
async function safePost(url: string, payload?: object): Promise<BackendResponse> {
  try {
    const { data } = await apiClient.post<BackendResponse>(url, payload);
    return data;
  } catch (err) {
    if (axios.isAxiosError(err) && err.response) {
      const body = err.response.data as {
        message?: string;
        detail?: string | Array<{ msg?: string }>;
      };
      // Backend returned a structured error body — treat it as a failed BackendResponse
      const message =
        body?.message ||
        (typeof body?.detail === "string" ? body.detail : null) ||
        (Array.isArray(body?.detail)
          ? body.detail
              .map((d) => d.msg || "")
              .filter(Boolean)
              .join(", ")
          : null) ||
        "Something went wrong. Please try again.";
      return {
        success: false,
        status_code: err.response.status,
        message,
      };
    }
    throw err; // network errors etc.
  }
}

export const authApi = {
  async register(payload: { name: string; email: string; password: string }) {
    return safePost("/auth/register", {
      username: payload.name,
      email: payload.email,
      password: payload.password,
    });
  },

  async login(payload: { email: string; password: string }) {
    return safePost("/auth/login", payload);
  },

  async logout() {
    return safePost("/auth/logout");
  },

  async me() {
    const { data } = await apiClient.get<AuthUser>("/auth/me");
    return data;
  },

  async forgotPassword(email: string) {
    const res = await safePost("/auth/forgot-password", { email });
    if (!res.success) {
      throw new Error(res.message);
    }
    return res;
  },

  async verifyResetOtp(payload: { email: string; otp: string }) {
    const res = await safePost("/auth/verify-reset-otp", payload);
    if (!res.success) {
      throw new Error(res.message);
    }
    return res as BackendResponse & { data?: { reset_token: string } };
  },

  async resetPassword(payload: { token: string; password: string }) {
    const res = await safePost("/auth/reset-password", {
      reset_token: payload.token,
      new_password: payload.password,
    });
    if (!res.success) {
      throw new Error(res.message);
    }
    return res;
  },
};
