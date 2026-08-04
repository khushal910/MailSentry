import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  predictionApi,
  type PredictionRequest,
  type PredictionResponse,
} from "../services/predictionApi";

interface PredictionContextValue {
  isPredicting: boolean;
  latest: PredictionResponse | null;
  error: string | null;
  predict: (payload: PredictionRequest) => Promise<PredictionResponse>;
  reset: () => void;
}

const PredictionContext = createContext<PredictionContextValue | undefined>(undefined);

export function PredictionProvider({ children }: { children: ReactNode }) {
  const [isPredicting, setPredicting] = useState(false);
  const [latest, setLatest] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const predict = useCallback(
    async (payload: PredictionRequest) => {
      setPredicting(true);
      setError(null);
      try {
        const res = await predictionApi.predict(payload);
        setLatest(res);
        queryClient.invalidateQueries({ queryKey: ["history"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard_stats"] });
        return res;
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Prediction failed";
        setError(msg);
        throw e;
      } finally {
        setPredicting(false);
      }
    },
    [queryClient],
  );

  const reset = useCallback(() => {
    setLatest(null);
    setError(null);
  }, []);

  const value = useMemo(
    () => ({ isPredicting, latest, error, predict, reset }),
    [isPredicting, latest, error, predict, reset],
  );

  return <PredictionContext.Provider value={value}>{children}</PredictionContext.Provider>;
}

export function usePrediction() {
  const ctx = useContext(PredictionContext);
  if (!ctx) throw new Error("usePrediction must be used inside <PredictionProvider>");
  return ctx;
}
