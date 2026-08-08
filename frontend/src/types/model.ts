export interface ProductionModelInfo {
  version: string;
  model_name: string;
  algorithm: string;
  algorithm_type: string;
  framework: string;
  serialization: string;
  task: string;
  deployment_date: string;
  training_date: string;
  trained_at?: string;
  mlflow_run_id?: string;
  deployment_status: string;
  status: string;
  model_hash: string;
  preprocessing_hash: string;
  label_encoder_hash: string;
  dataset_version: string;
  dataset_size: number;
  hyperparameters: Record<string, unknown>;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  training_time_sec: number;
  inference_time_ms: number;
  model_size_mb: number;
  primary_metric: string;
  primary_score: number;
  description: string;
  is_active: boolean;
  input_type?: string;
  preprocessor?: string;
  output_type?: string;
  docker_image?: string;
  python_version?: string;
  commit?: string;
  mlflow_run?: string;
  deployed_by?: string;
  experiment_name?: string;
  provider?: string;
  device?: string;
  base_model?: string;
  adapter?: string;
}


export interface MetricDiffItem {
  label: string;
  unit: string;
  v1_value: number;
  v2_value: number;
  diff: number;
  percentage_change: number;
  status: "improved" | "decreased" | "no_change";
  indicator: "↑" | "↓" | "→";
}

export interface ModelComparisonResult {
  v1: {
    version: string;
    model_name: string;
    algorithm: string;
    deployment_date: string;
    dataset_version: string;
    hyperparameters: Record<string, unknown>;
  };
  v2: {
    version: string;
    model_name: string;
    algorithm: string;
    deployment_date: string;
    dataset_version: string;
    hyperparameters: Record<string, unknown>;
  };
  comparison: Record<string, MetricDiffItem>;
}
