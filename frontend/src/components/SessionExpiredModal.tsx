import { ShieldAlert, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SessionExpiredModalProps {
  isOpen: boolean;
  redirectUrl?: string;
  onConfirm: () => void;
}

export function SessionExpiredModal({ isOpen, redirectUrl, onConfirm }: SessionExpiredModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-border/80 bg-card p-6 shadow-2xl transition-all">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive ring-8 ring-destructive/5">
            <ShieldAlert className="h-7 w-7" />
          </div>

          <h3 className="mt-4 text-xl font-semibold tracking-tight text-foreground">
            Session Expired
          </h3>

          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            Your login session has expired or your security token is no longer valid. Please sign in
            again to continue using MailSentry.
          </p>

          {redirectUrl && (
            <div className="mt-3 rounded-lg border border-border/60 bg-muted/40 px-3 py-1.5 text-xs text-muted-foreground">
              Returning to: <span className="font-medium text-foreground">{redirectUrl}</span>
            </div>
          )}

          <div className="mt-6 flex w-full flex-col gap-2">
            <Button
              onClick={onConfirm}
              className="bg-gradient-brand shadow-elegant w-full font-semibold"
              size="lg"
            >
              <LogIn className="mr-2 h-4 w-4" />
              Sign In Again
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
