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
const envMeta =
  typeof import.meta !== "undefined"
    ? (import.meta as unknown as { env?: { VITE_API_URL?: string; VITE_API_TIMEOUT?: string; VITE_AXIOS_TIMEOUT?: string } }).env
    : undefined;

const rawBase = envMeta?.VITE_API_URL || "http://localhost:8000";

// Normalise: replace 127.0.0.1 with localhost so cookies are never split across origins
const baseURL = rawBase.replace("127.0.0.1", "localhost");

const parsedTimeout = Number(envMeta?.VITE_API_TIMEOUT || envMeta?.VITE_AXIOS_TIMEOUT);
const timeout = !isNaN(parsedTimeout) && parsedTimeout > 0 ? parsedTimeout : 60_000;

const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

type SessionExpiredHandler = (expiredUrl: string) => void;
let onSessionExpiredHandler: SessionExpiredHandler | null = null;

export function setSessionExpiredHandler(handler: SessionExpiredHandler | null) {
  onSessionExpiredHandler = handler;
}

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  (error: AxiosError<{ message?: string; detail?: string | Array<{ msg?: string }> }>) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || "";
      const isAuthCheck = requestUrl.includes("/auth/me") || requestUrl.includes("/auth/login");
      if (!isAuthCheck && typeof window !== "undefined") {
        const currentPath = window.location.pathname + window.location.search;
        if (onSessionExpiredHandler) {
          onSessionExpiredHandler(currentPath);
        }
      }
    }

    const data = error.response?.data as
      | { message?: string; detail?: string | Array<{ msg?: string }> }
      | undefined;
    const message =
      data?.message ||
      (typeof data?.detail === "string" ? data.detail : null) ||
      (Array.isArray(data?.detail)
        ? data.detail
            .map((d) => d.msg || "")
            .filter(Boolean)
            .join(", ")
        : null) ||
      error.message ||
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  },
);

export default apiClient;
