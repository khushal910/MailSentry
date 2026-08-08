import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import apiClient from "../services/apiClient";

export interface MaintenanceStatus {
  isMaintenance: boolean;
  maintenanceEnd: string | null;
  adminBypass: boolean;
  message: string;
  isChecking: boolean;
  checkStatus: () => Promise<void>;
}

const MaintenanceContext = createContext<MaintenanceStatus | undefined>(undefined);

type MaintenanceHandler = (data?: { maintenance_end?: string | null; message?: string }) => void;
let onMaintenanceTriggered: MaintenanceHandler | null = null;

export function registerMaintenanceInterceptor(handler: MaintenanceHandler | null) {
  onMaintenanceTriggered = handler;
}

export function triggerMaintenanceMode(data?: { maintenance_end?: string | null; message?: string }) {
  if (onMaintenanceTriggered) {
    onMaintenanceTriggered(data);
  }
}

export function MaintenanceProvider({ children }: { children: ReactNode }) {
  const [isMaintenance, setIsMaintenance] = useState<boolean>(false);
  const [maintenanceEnd, setMaintenanceEnd] = useState<string | null>(null);
  const [adminBypass, setAdminBypass] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("Server is currently under scheduled maintenance.");
  const [isChecking, setIsChecking] = useState<boolean>(true);

  const checkStatus = useCallback(async () => {
    setIsChecking(true);
    try {
      const response = await apiClient.get("/api/maintenance/status", {
        headers: { "Cache-Control": "no-cache" },
      });
      const data = response.data;
      if (data && typeof data.maintenance === "boolean") {
        setIsMaintenance(data.maintenance);
        setMaintenanceEnd(data.maintenance_end || null);
        setAdminBypass(Boolean(data.admin_bypass));
        if (data.message) setMessage(data.message);
      }
    } catch {
      // If endpoint fails, keep existing state
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    void checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    registerMaintenanceInterceptor((data) => {
      setIsMaintenance(true);
      if (data?.maintenance_end !== undefined) {
        setMaintenanceEnd(data.maintenance_end || null);
      }
      if (data?.message) {
        setMessage(data.message);
      }
    });

    return () => {
      registerMaintenanceInterceptor(null);
    };
  }, []);

  const value = useMemo(
    () => ({
      isMaintenance,
      maintenanceEnd,
      adminBypass,
      message,
      isChecking,
      checkStatus,
    }),
    [isMaintenance, maintenanceEnd, adminBypass, message, isChecking, checkStatus]
  );

  return (
    <MaintenanceContext.Provider value={value}>
      {children}
    </MaintenanceContext.Provider>
  );
}

export function useMaintenance() {
  const ctx = useContext(MaintenanceContext);
  if (!ctx) {
    throw new Error("useMaintenance must be used within a MaintenanceProvider");
  }
  return ctx;
}
