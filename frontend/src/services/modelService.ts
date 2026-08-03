import apiClient from "./apiClient";
import type { ProductionModelInfo } from "@/types/model";

export const modelService = {
  /**
   * Fetch currently deployed production model details.
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
};
