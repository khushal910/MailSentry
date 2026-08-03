import apiClient from "./apiClient";
import type {
  ProductionModelInfo,
  ModelComparisonResult,
} from "@/types/model";

export const modelService = {
  /**
   * Fetch current production model details.
   * GET /api/v1/model/production
   */
  getProductionModel: async (): Promise<ProductionModelInfo> => {
    const res = await apiClient.get<
      | ProductionModelInfo
      | { data: ProductionModelInfo }
      | { success: boolean; data: ProductionModelInfo }
    >("/api/v1/model/production");

    const payload = res.data;
    if (payload && typeof payload === "object" && "data" in payload && payload.data) {
      return payload.data;
    }
    return payload as ProductionModelInfo;
  },

  /**
   * Fetch all production model versions (current + history).
   * GET /api/v1/model/history
   */
  getModelHistory: async (): Promise<ProductionModelInfo[]> => {
    const res = await apiClient.get<
      | { history: ProductionModelInfo[] }
      | { data: { history: ProductionModelInfo[] } }
    >("/api/v1/model/history");

    const payload = res.data;
    if (payload && "data" in payload && payload.data?.history) {
      return payload.data.history;
    }
    if (payload && "history" in payload && Array.isArray(payload.history)) {
      return payload.history;
    }
    return [];
  },

  /**
   * Fetch metadata for a specific model version.
   * GET /api/v1/model/version/{version}
   */
  getModelVersion: async (version: string): Promise<ProductionModelInfo> => {
    const res = await apiClient.get<
      | ProductionModelInfo
      | { data: ProductionModelInfo }
    >(`/api/v1/model/version/${encodeURIComponent(version)}`);

    const payload = res.data;
    if (payload && typeof payload === "object" && "data" in payload && payload.data) {
      return payload.data;
    }
    return payload as ProductionModelInfo;
  },

  /**
   * Compare two model versions side by side.
   * GET /api/v1/model/compare?v1=x&v2=y
   */
  compareModels: async (
    v1: string,
    v2: string
  ): Promise<ModelComparisonResult> => {
    const res = await apiClient.get<
      | ModelComparisonResult
      | { data: ModelComparisonResult }
    >("/api/v1/model/compare", {
      params: { v1, v2 },
    });

    const payload = res.data;
    if (payload && typeof payload === "object" && "data" in payload && payload.data) {
      return payload.data;
    }
    return payload as ModelComparisonResult;
  },
};
