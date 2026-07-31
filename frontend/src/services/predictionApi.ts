import apiClient from "./apiClient";

export type PredictionLabel = "Spam" | "Ham";

export interface PredictionRequest {
  subject: string;
  message: string;
}

export interface PredictionResponse {
  prediction: PredictionLabel;
  confidence: number;
  reason: string;
}

export const predictionApi = {
  async predict(payload: PredictionRequest) {
    const { data } = await apiClient.post<PredictionResponse>("/api/v1/predict", payload);
    return data;
  },
};
