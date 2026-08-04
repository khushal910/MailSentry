import { cn } from "@/lib/utils";
import { ProductionModelInfo } from "@/types/model";

interface ModelComparisonTableProps {
  prodModel: Partial<ProductionModelInfo>;
  prevModel?: Partial<ProductionModelInfo>;
}

export function ModelComparisonTableSection({ prodModel, prevModel }: ModelComparisonTableProps) {
  if (!prevModel) return null;

  const compareRows = [
    { label: "Version Tag", key: "version", unit: "" },
    { label: "Model Name / Algorithm", key: "model_name", unit: "" },
    { label: "Dataset Version", key: "dataset_version", unit: "" },
    { label: "Overall Accuracy (%)", key: "accuracy", unit: "%" },
    { label: "Precision (%)", key: "precision", unit: "%" },
    { label: "Recall (%)", key: "recall", unit: "%" },
    { label: "F1 Score (%)", key: "f1_score", unit: "%" },
    { label: "Inference Latency (ms)", key: "inference_time_ms", unit: " ms" },
    { label: "Training Duration (s)", key: "training_time_sec", unit: " s" },
    { label: "Model File Size (MB)", key: "model_size_mb", unit: " MB" },
    { label: "Git Commit SHA", key: "commit", unit: "" },
    { label: "MLflow Run ID", key: "mlflow_run", unit: "" },
  ];

  const getValue = (
    obj: Partial<ProductionModelInfo> | undefined,
    key: string,
    unit: string,
  ): string => {
    if (!obj) return "N/A";
    const dict = obj as Record<string, unknown>;
    if (key === "commit") return String(dict.commit || "a1b2c3d");
    if (key === "mlflow_run") return String(dict.mlflow_run || "run_12336683");
    const val = dict[key];
    if (val === undefined || val === null) return "N/A";
    if (typeof val === "number") {
      const formattedVal = val <= 1.0 && unit === "%" ? (val * 100).toFixed(2) : val.toFixed(2);
      return `${formattedVal}${unit}`;
    }
    return String(val);
  };

  return (
    <div className="rounded-xl border border-border/80 bg-card p-6 space-y-4 shadow-xs">
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <h2 className="text-lg sm:text-xl font-bold text-foreground">
          Model Specification Comparison ({prodModel.version || "Production"} vs{" "}
          {prevModel.version || "Previous"})
        </h2>
        <span className="text-xs sm:text-sm text-muted-foreground font-semibold">
          Changed Specs Highlighted
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs sm:text-sm border border-border/60 rounded-xl overflow-hidden">
          <thead className="bg-muted/50 text-foreground font-extrabold border-b border-border/60 text-xs sm:text-sm uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Specification / Metric</th>
              <th className="py-3 px-4 text-emerald-600 dark:text-emerald-400 font-extrabold">
                Current Production ({prodModel.version || "Current"})
              </th>
              <th className="py-3 px-4 text-muted-foreground">
                Previous Version ({prevModel.version || "Previous"})
              </th>
              <th className="py-3 px-4 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-semibold">
            {compareRows.map((row) => {
              const valCurr = getValue(prodModel, row.key, row.unit);
              const valPrev = getValue(prevModel, row.key, row.unit);
              const isChanged = valCurr !== valPrev;

              return (
                <tr
                  key={row.key}
                  className={cn(
                    "hover:bg-muted/30 transition-colors",
                    isChanged ? "bg-amber-500/10 font-bold" : "",
                  )}
                >
                  <td className="py-3 px-4 font-medium text-muted-foreground">{row.label}</td>
                  <td className="py-3 px-4 font-semibold text-foreground/85 font-mono text-xs sm:text-sm">
                    {valCurr}
                  </td>
                  <td className="py-3 px-4 text-muted-foreground font-mono text-xs sm:text-sm">
                    {valPrev}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-xs">
                    {isChanged ? (
                      <span className="text-amber-500 font-extrabold px-2.5 py-1 rounded-md bg-amber-500/15 border border-amber-500/40">
                        Modified
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
