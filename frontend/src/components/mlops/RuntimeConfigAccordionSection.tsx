import { useState } from "react";
import { ChevronDown, ChevronUp, Terminal } from "lucide-react";

interface RuntimeConfigAccordionProps {
  model: any;
}

export function RuntimeConfigAccordionSection({ model }: RuntimeConfigAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-xl border border-border/80 bg-card shadow-xs overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-muted/40 transition-all duration-150 border-b border-border/40"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand font-bold">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-foreground">Runtime & Model Configuration</h3>
            <p className="text-xs sm:text-sm text-muted-foreground font-medium">Read-only technical specs, hyperparameters, input/output signature, and docker environment</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs sm:text-sm font-mono text-muted-foreground font-semibold">Read-Only</span>
          {isOpen ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-6 space-y-5 bg-muted/10 font-mono text-xs sm:text-sm">
          {/* Row 1: Hyperparameters & Model Signature */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-border/60 bg-muted/40 space-y-2">
              <span className="block text-xs font-sans font-semibold text-muted-foreground uppercase tracking-wider">
                Hyperparameters JSON
              </span>
              <pre className="text-foreground/80 font-mono font-normal whitespace-pre-wrap max-h-56 overflow-y-auto custom-scrollbar text-xs sm:text-sm">
                {JSON.stringify(model.hyperparameters || { C: 1.0, penalty: "l2", max_iter: 1000 }, null, 2)}
              </pre>
            </div>

            <div className="p-4 rounded-xl border border-border/60 bg-muted/40 space-y-3">
              <span className="block text-xs font-sans font-semibold text-muted-foreground uppercase tracking-wider">
                Model Signature & Schemas
              </span>
              <div className="space-y-2 text-xs sm:text-sm">
                <div>
                  <span className="text-muted-foreground font-sans font-medium">Input Type:</span>
                  <span className="block text-brand/90 truncate font-mono font-medium bg-background p-2 rounded-lg border border-border/40 mt-1">
                    {model.input_type || "tfidf"} ({model.preprocessor || "tfidf_vectorizer"})
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground font-sans font-medium">Output Type & Framework:</span>
                  <span className="block text-emerald-500/90 truncate font-mono font-medium bg-background p-2 rounded-lg border border-border/40 mt-1">
                    {model.output_type || "probability"} ({model.framework || "sklearn"} / {model.serialization || "joblib"})
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Row 2: Environment Specs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-sans text-xs sm:text-sm">
            <div className="p-3 rounded-xl border border-border/60 bg-muted/30">
              <span className="block text-xs text-muted-foreground font-medium uppercase">Docker Image</span>
              <span className="font-mono text-xs sm:text-sm font-medium text-foreground/80 truncate block mt-0.5">{model.docker_image || "mailsentry/ml-service:v2.0"}</span>
            </div>
            <div className="p-3 rounded-xl border border-border/60 bg-muted/30">
              <span className="block text-xs text-muted-foreground font-medium uppercase">Python Runtime</span>
              <span className="font-mono text-xs sm:text-sm font-medium text-foreground/80 truncate block mt-0.5">{model.python_version || "Python 3.13.1"}</span>
            </div>
            <div className="p-3 rounded-xl border border-border/60 bg-muted/30">
              <span className="block text-xs text-muted-foreground font-medium uppercase">Framework</span>
              <span className="font-mono text-xs sm:text-sm font-medium text-foreground/80 truncate block mt-0.5">{model.framework || "sklearn"} 1.6.1</span>
            </div>
            <div className="p-3 rounded-xl border border-border/60 bg-muted/30">
              <span className="block text-xs text-muted-foreground font-medium uppercase">Inference Config</span>
              <span className="font-mono text-xs sm:text-sm font-medium text-foreground/80 truncate block mt-0.5">workers=4, timeout=30s</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
