export interface ProductionModelInfo {
  model_name: string;
  version: string;
  status: string;
  task: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  training_date: string;
  dataset_size: number;
  algorithm_type: string;
  description: string;
  is_active: boolean;
}
