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
  refresh: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
  triggerSessionExpired: (redirectUrl?: string) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setLoading] = useState(true);
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

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const me = await authApi.me();
      setUser(me);
      setIsSessionExpired(false);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    void (async () => {
      if (isMounted) {
        await refresh();
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
