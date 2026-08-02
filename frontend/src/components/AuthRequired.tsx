import { Lock, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AuthRequiredProps {
  title?: string;
  message?: string;
  onSignIn?: () => void;
}

export function AuthRequired({
  title = "Authentication Required",
  message = "Please sign in to access this feature in MailSentry.",
  onSignIn,
}: AuthRequiredProps) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center rounded-2xl border border-border/60 bg-card/40 p-8 text-center backdrop-blur-sm">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary ring-8 ring-primary/5">
        <Lock className="h-8 w-8" />
      </div>
      <h3 className="mt-4 text-xl font-semibold tracking-tight text-foreground">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground leading-relaxed">{message}</p>
      {onSignIn && (
        <Button onClick={onSignIn} className="bg-gradient-brand shadow-elegant mt-6 font-semibold">
          <LogIn className="mr-2 h-4 w-4" />
          Sign In Now
        </Button>
      )}
    </div>
  );
}
