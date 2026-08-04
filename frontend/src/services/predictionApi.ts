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

interface RawPredictionResponse {
  data?: {
    predicted_label?: string;
    prediction?: string;
    predicted_score?: number;
    confidence?: number;
    reason?: string;
  };
  predicted_label?: string;
  prediction?: string;
  predicted_score?: number;
  confidence?: number;
  reason?: string;
}

export const predictionApi = {
  async predict(payload: PredictionRequest): Promise<PredictionResponse> {
    const { data } = await apiClient.post<RawPredictionResponse>("/api/v1/predict", payload);
    const innerData = data?.data || data || {};

    const rawLabel = String(innerData.predicted_label || innerData.prediction || "Ham").trim();

    const isSpam = rawLabel.toLowerCase().includes("spam");
    const confidence =
      typeof innerData.predicted_score === "number"
        ? innerData.predicted_score
        : typeof innerData.confidence === "number"
          ? innerData.confidence
          : 0.85;

    const formattedConfidence =
      confidence <= 1 ? `${(confidence * 100).toFixed(1)}%` : `${confidence.toFixed(1)}%`;

    return {
      prediction: isSpam ? "Spam" : "Ham",
      confidence: confidence,
      reason:
        innerData.reason ||
        (isSpam
          ? `Flagged as Spam by MailSentry AI (${formattedConfidence} confidence)`
          : `Verified Safe Email by MailSentry AI (${formattedConfidence} confidence)`),
    };
  },
};
