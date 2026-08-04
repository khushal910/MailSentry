import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Code2, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HyperparametersModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelName: string;
  version: string;
  hyperparameters: Record<string, unknown>;
}

export function HyperparametersModal({
  isOpen,
  onClose,
  modelName,
  version,
  hyperparameters,
}: HyperparametersModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const jsonString = JSON.stringify(hyperparameters || {}, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-md p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0"
        />

        {/* Modal Container */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="glass-strong relative z-10 w-full max-w-xl rounded-3xl border border-border/70 p-6 shadow-2xl overflow-hidden space-y-4 font-sans"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border/40 pb-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
                <Code2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-foreground tracking-tight">
                  Hyperparameters & Configuration
                </h3>
                <p className="text-xs text-muted-foreground font-medium">
                  {modelName} ({version}) training parameters
                </p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="rounded-full hover:bg-accent/50"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* JSON Viewer */}
          <div className="relative rounded-2xl bg-muted/30 border border-border/40 p-4 font-mono text-xs max-h-80 overflow-y-auto custom-scrollbar">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="absolute top-3 right-3 h-7 px-2.5 text-[11px] font-semibold border-border/60 bg-background/80 hover:bg-accent rounded-xl shadow-sm"
            >
              {copied ? (
                <>
                  <Check className="mr-1 h-3 w-3 text-emerald-500" /> Copied
                </>
              ) : (
                <>
                  <Copy className="mr-1 h-3 w-3 text-muted-foreground" /> Copy JSON
                </>
              )}
            </Button>
            <pre className="text-foreground/90 whitespace-pre-wrap pr-16 leading-relaxed">
              {jsonString}
            </pre>
          </div>

          {/* Footer */}
          <div className="flex justify-end pt-2">
            <Button
              variant="outline"
              onClick={onClose}
              className="rounded-xl font-semibold text-xs px-5"
            >
              Close
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
