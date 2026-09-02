import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { emailsApi, type UnclassifiedEmail } from "@/services/emailsApi";
import { UNCLASSIFIED_EMAILS_QUERY_KEY } from "@/hooks/useUnclassifiedQueue";

export interface JobProgress {
  processed: number;
  total: number;
  status: "started" | "running" | "completed" | "failed";
  current_subject?: string | null;
  startTime: number;
  estRemainingSec: number;
}

interface ClassificationContextType {
  isClassifying: boolean;
  activeJobId: string | null;
  jobProgress: JobProgress | null;
  error: string | null;
  startClassification: (emails: UnclassifiedEmail[]) => Promise<void>;
  cancelTracking: () => void;
}

const ClassificationContext = createContext<ClassificationContextType | undefined>(undefined);

export function ClassificationProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [isClassifying, setIsClassifying] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isJobActiveRef = useRef(false);
  const activeJobIdRef = useRef<string | null>(null);
  const snapshotTotalRef = useRef<number>(0);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancelTracking = useCallback(() => {
    isJobActiveRef.current = false;
    activeJobIdRef.current = null;
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    setIsClassifying(false);
    setActiveJobId(null);
    setJobProgress(null);
  }, []);

  /**
   * Internal polling engine that continues running across all route changes.
   */
  const pollJobStatus = useCallback(
    async (jobId: string, totalCount: number, startMs: number) => {
      isJobActiveRef.current = true;
      activeJobIdRef.current = jobId;
      snapshotTotalRef.current = totalCount;
      setActiveJobId(jobId);
      setIsClassifying(true);
      setError(null);

      let consecutiveFailures = 0;

      const runPoll = async () => {
        if (!isJobActiveRef.current || activeJobIdRef.current !== jobId) {
          return;
        }

        try {
          const statusRes = await emailsApi.getJobStatus(jobId);
          consecutiveFailures = 0;

          if (!isJobActiveRef.current || activeJobIdRef.current !== jobId) {
            return;
          }

          const nowMs = Date.now();
          const total = statusRes.total || snapshotTotalRef.current || totalCount;
          const processed = statusRes.processed;
          const elapsedSec = (nowMs - startMs) / 1000;
          const avgItemSec = processed > 0 ? elapsedSec / processed : 0;
          const estRemainingSec =
            processed > 0 && processed < total
              ? Math.max(1, Math.ceil((total - processed) * avgItemSec))
              : 0;

          if (statusRes.status === "completed") {
            // Animate to 100% completion
            setJobProgress({
              processed: total,
              total,
              status: "completed",
              current_subject: statusRes.current_subject,
              startTime: startMs,
              estRemainingSec: 0,
            });

            // Smooth delay for visual completion
            await new Promise((resolve) => setTimeout(resolve, 650));

            // Sync all relevant queries
            void queryClient.invalidateQueries({ queryKey: UNCLASSIFIED_EMAILS_QUERY_KEY });
            void queryClient.invalidateQueries({ queryKey: ["classified-emails"] });
            void queryClient.invalidateQueries({ queryKey: ["email-summary"] });
            void queryClient.invalidateQueries({ queryKey: ["predictive-history"] });
            void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });

            // Toast notification that appears regardless of active page
            const classifiedCount = statusRes.classified ?? total;
            toast.success(
              `Classification complete! Classified ${classifiedCount} email(s).`,
              {
                description: "Predictions have been saved to your history and database.",
                duration: 5000,
              },
            );

            isJobActiveRef.current = false;
            activeJobIdRef.current = null;
            setIsClassifying(false);
            setActiveJobId(null);
            setJobProgress(null);
            return;
          }

          if (statusRes.status === "failed") {
            const errMsg = statusRes.error || "Background classification job failed.";
            setError(errMsg);
            toast.error(errMsg, { duration: 5000 });
            isJobActiveRef.current = false;
            activeJobIdRef.current = null;
            setIsClassifying(false);
            setActiveJobId(null);
            setJobProgress(null);
            return;
          }

          // Active running / started state
          setJobProgress({
            processed,
            total,
            status: statusRes.status as "started" | "running",
            current_subject: statusRes.current_subject,
            startTime: startMs,
            estRemainingSec,
          });

          // Schedule next poll step
          pollTimerRef.current = setTimeout(runPoll, 400);
        } catch (pollErr) {
          consecutiveFailures += 1;
          if (consecutiveFailures > 5) {
            const errMsg = pollErr instanceof Error ? pollErr.message : "Polling connection lost";
            setError(errMsg);
            isJobActiveRef.current = false;
            activeJobIdRef.current = null;
            setIsClassifying(false);
            setActiveJobId(null);
            setJobProgress(null);
            return;
          }
          // Exponential backoff retry on transient errors
          pollTimerRef.current = setTimeout(runPoll, 1000);
        }
      };

      await runPoll();
    },
    [queryClient],
  );

  /**
   * Start a new classification job (or resume if already in progress on the server)
   */
  const startClassification = useCallback(
    async (emails: UnclassifiedEmail[]) => {
      if (emails.length === 0 || isClassifying) return;
      setError(null);
      const startMs = Date.now();
      const snapshotTotal = emails.length;

      try {
        const job = await emailsApi.startClassifyJob(emails);
        const jobId = job.job_id;
        const initialTotal = job.total || snapshotTotal;

        setJobProgress({
          processed: job.processed,
          total: initialTotal,
          status: job.status,
          current_subject: job.current_subject,
          startTime: startMs,
          estRemainingSec: 0,
        });

        await pollJobStatus(jobId, initialTotal, startMs);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to start classification job.";
        setError(msg);
        toast.error(msg, { duration: 5000 });
        setIsClassifying(false);
        setActiveJobId(null);
        setJobProgress(null);
      }
    },
    [isClassifying, pollJobStatus],
  );

  /**
   * On initial mount of the dashboard layout, check if a classification job is already running on the server
   * (e.g. if the user navigated away, or refreshed the browser window).
   */
  useEffect(() => {
    let isCancelled = false;

    async function checkActiveJob() {
      try {
        const active = await emailsApi.getActiveJob();
        if (isCancelled || !active || active.status === "completed" || active.status === "failed") {
          return;
        }

        // Active job found on server: attach global polling seamlessly
        const total = active.total || 1;
        void pollJobStatus(active.job_id, total, Date.now());
      } catch {
        // Silently skip if no active job exists
      }
    }

    void checkActiveJob();

    return () => {
      isCancelled = true;
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
      }
    };
  }, [pollJobStatus]);

  return (
    <ClassificationContext.Provider
      value={{
        isClassifying,
        activeJobId,
        jobProgress,
        error,
        startClassification,
        cancelTracking,
      }}
    >
      {children}
    </ClassificationContext.Provider>
  );
}

export function useClassification() {
  const context = useContext(ClassificationContext);
  if (!context) {
    throw new Error("useClassification must be used within a ClassificationProvider");
  }
  return context;
}
