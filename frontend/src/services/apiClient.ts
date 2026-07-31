import axios, { AxiosError, type AxiosInstance } from "axios";

const baseURL =
  (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL) ||
  "http://127.0.0.1:8000";

const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 20_000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (r) => r,
  (error: AxiosError<{ message?: string; detail?: string | { msg: string }[] }>) => {
    const data = error.response?.data as any;
    const message =
      data?.message ||
      (typeof data?.detail === "string" ? data.detail : null) ||
      (Array.isArray(data?.detail) ? data.detail.map((d: any) => d.msg).join(", ") : null) ||
      error.message ||
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  },
);

export default apiClient;
