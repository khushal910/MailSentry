import apiClient from "./apiClient";
import type { PredictionLabel } from "./predictionApi";

export interface HistoryItem {
  id: string;
  date: string;
  subject: string;
  prediction: PredictionLabel;
  confidence: number;
  reason?: string;
}

export interface HistoryQuery {
  page?: number;
  pageSize?: number;
  search?: string;
  filter?: "all" | "spam" | "ham";
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  pageSize: number;
}

export const historyApi = {
  async list(query: HistoryQuery = {}) {
    const { data } = await apiClient.get<HistoryResponse>("/api/v1/history", {
      params: query,
    });
    return data;
  },
  async remove(id: string) {
    await apiClient.delete(`/api/v1/history/${id}`);
  },
};
