import axios, { AxiosError, type AxiosInstance } from "axios";

/**
 * Axios instance pre-configured with the backend base URL and credentials.
 *
 * WHY we always default to http://localhost:8000 (not http://127.0.0.1:8000):
 * Browsers treat 127.0.0.1 and localhost as distinct origins for cookie purposes.
 * If the Set-Cookie response comes from 127.0.0.1:8000 but the next fetch goes to
 * localhost:8000, the browser silently drops the cookie. All API requests must use
 * the same host as the one that issued the cookie. The VITE_API_URL env var (set in
 * .env) is the authoritative source; localhost:8000 is only the local dev fallback.
 */
const rawBase =
  (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL) ||
  "http://localhost:8000";

// Normalise: replace 127.0.0.1 with localhost so cookies are never split across origins
const baseURL = rawBase.replace("127.0.0.1", "localhost");


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
