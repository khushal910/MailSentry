import { useState } from "react";
import { ChevronDown, ChevronUp, FileCode, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductionModelInfo } from "@/types/model";

interface ArtifactIntegrityAccordionProps {
  model: Partial<ProductionModelInfo>;
}

export function ArtifactIntegrityAccordionSection({ model }: ArtifactIntegrityAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const hashes = [
    { label: "Model Checkpoint SHA-256", key: "model_hash", value: model.model_hash || "N/A" },
    {
      label: "Preprocessor Pipeline SHA-256",
      key: "prep_hash",
      value: model.preprocessing_hash || "N/A",
    },
    { label: "Label Encoder SHA-256", key: "enc_hash", value: model.label_encoder_hash || "N/A" },
    {
      label: "Dataset Version Tag",
      key: "dataset_version",
      value: model.dataset_version || "v1.0.0",
    },
    { label: "Serving Task", key: "task", value: model.task || "Spam Email Classification" },
    {
      label: "Registry Storage Path",
      key: "registry_uri",
      value: "backend/models/production/metadata.json",
    },
  ];

  const handleCopy = (key: string, val: string) => {
    navigator.clipboard.writeText(val);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="rounded-xl border border-border/80 bg-card shadow-xs overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-muted/40 transition-all duration-150 border-b border-border/40"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand font-bold">
            <FileCode className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-foreground">
              Artifact Integrity & Checkpoints
            </h3>
            <p className="text-xs sm:text-sm text-muted-foreground font-medium">
              Cryptographic SHA-256 checksums, dataset hashes, and registry storage URI
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs sm:text-sm font-mono text-muted-foreground font-semibold">
            {hashes.length} Checksums
          </span>
          {isOpen ? (
            <ChevronUp className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          )}
        </div>
      </button>

      {isOpen && (
        <div className="p-6 space-y-4 bg-muted/10">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs sm:text-sm">
            {hashes.map((h) => (
              <div
                key={h.key}
                className="p-4 rounded-xl border border-border/60 bg-muted/30 space-y-2"
              >
                <div className="flex items-center justify-between font-sans">
                  <span className="text-xs sm:text-sm font-bold text-muted-foreground">
                    {h.label}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopy(h.key, h.value)}
                    className="h-7 px-2.5 text-xs font-bold hover:bg-muted/60"
                  >
                    {copiedKey === h.key ? (
                      <>
                        <Check className="mr-1.5 h-3.5 w-3.5 text-emerald-500" /> Copied
                      </>
                    ) : (
                      <>
                        <Copy className="mr-1.5 h-3.5 w-3.5 text-muted-foreground" /> Copy
                      </>
                    )}
                  </Button>
                </div>
                <span className="block text-xs sm:text-sm text-foreground/80 font-medium truncate bg-background p-2.5 rounded-lg border border-border/40">
                  {h.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
