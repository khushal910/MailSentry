import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authApi, type AuthUser } from "../services/authApi";
import { setSessionExpiredHandler } from "../services/apiClient";
import { SessionExpiredModal } from "@/components/SessionExpiredModal";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isSessionExpired: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; message: string }>;
  signup: (
    name: string,
    email: string,
    password: string,
  ) => Promise<{ success: boolean; message: string }>;
  logout: () => Promise<void>;
  refresh: (showLoading?: boolean) => Promise<AuthUser | null>;
  setUser: (user: AuthUser | null) => void;
  triggerSessionExpired: (redirectUrl?: string) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setLoading] = useState(() => {
    if (typeof window !== "undefined") {
      return Boolean(localStorage.getItem("token"));
    }
    return false;
  });
  const [isSessionExpired, setIsSessionExpired] = useState(false);
  const [redirectUrl, setRedirectUrl] = useState<string>("");
  const queryClient = useQueryClient();

  const triggerSessionExpired = useCallback(
    (expiredUrl?: string) => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
      }
      queryClient.clear();
      setUser(null);
      if (expiredUrl && !expiredUrl.includes("/login")) {
        setRedirectUrl(expiredUrl);
      }
      setIsSessionExpired(true);
    },
    [queryClient],
  );

  useEffect(() => {
    setSessionExpiredHandler((expiredPath) => {
      triggerSessionExpired(expiredPath);
    });

    return () => {
      setSessionExpiredHandler(null);
    };
  }, [triggerSessionExpired]);

  const refresh = useCallback(async (showLoading = false): Promise<AuthUser | null> => {
    const hasToken = typeof window !== "undefined" && Boolean(localStorage.getItem("token"));
    if (!hasToken) {
      setUser(null);
      if (showLoading) setLoading(false);
      return null;
    }

    if (showLoading) setLoading(true);
    try {
      const me = await authApi.me();
      setUser(me);
      setIsSessionExpired(false);
      return me;
    } catch {
      setUser(null);
      return null;
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    void (async () => {
      if (isMounted) {
        await refresh(true);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await authApi.login({ email, password });
      if (res.success) {
        if ((res as unknown as { data?: { access_token?: string } }).data?.access_token) {
          localStorage.setItem(
            "token",
            (res as unknown as { data: { access_token: string } }).data.access_token,
          );
        }
        setIsSessionExpired(false);
        await refresh();
      }
      return { success: res.success, message: res.message };
    },
    [refresh],
  );

  const signup = useCallback(
    async (name: string, email: string, password: string) => {
      const res = await authApi.register({ name, email, password });
      if (res.success) {
        if ((res as unknown as { data?: { access_token?: string } }).data?.access_token) {
          localStorage.setItem(
            "token",
            (res as unknown as { data: { access_token: string } }).data.access_token,
          );
        }
        setIsSessionExpired(false);
        await refresh();
      }
      return { success: res.success, message: res.message };
    },
    [refresh],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
      }
      queryClient.clear();
      setUser(null);
      setIsSessionExpired(false);
    }
  }, [queryClient]);

  const handleConfirmSessionExpired = useCallback(() => {
    setIsSessionExpired(false);
    if (typeof window !== "undefined") {
      const target = redirectUrl ? `/login?redirect=${encodeURIComponent(redirectUrl)}` : "/login";
      window.location.href = target;
    }
  }, [redirectUrl]);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      isSessionExpired,
      login,
      signup,
      logout,
      refresh,
      setUser,
      triggerSessionExpired,
    }),
    [user, isLoading, isSessionExpired, login, signup, logout, refresh, triggerSessionExpired],
  );

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="relative h-12 w-12">
            <div className="absolute inset-0 rounded-full border-4 border-muted" />
            <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-brand" />
          </div>
          <p className="text-xs font-medium text-muted-foreground animate-pulse">
            Verifying session…
          </p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
      <SessionExpiredModal
        isOpen={isSessionExpired}
        redirectUrl={redirectUrl}
        onConfirm={handleConfirmSessionExpired}
      />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
