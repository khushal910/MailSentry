import { createFileRoute, Link } from "@tanstack/react-router";
import { MailCheck } from "lucide-react";
import { toast } from "sonner";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/verify-email")({
  head: () => ({
    meta: [
      { title: "Verify your email — MailSentry" },
      { name: "description", content: "Confirm your email to activate MailSentry." },
    ],
  }),
  component: VerifyEmailPage,
});

function VerifyEmailPage() {
  return (
    <AuthLayout
      title="Check your inbox"
      subtitle="We sent you a confirmation link. Click it to activate your account."
      footer={
        <>
          Wrong email?{" "}
          <Link to="/signup" className="text-brand hover:underline">
            Sign up again
          </Link>
        </>
      }
    >
      <div className="flex flex-col items-center gap-4 py-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <MailCheck className="h-7 w-7" />
        </div>
        <p className="text-sm text-muted-foreground">
          Didn't get the email? Check your spam folder or resend below.
        </p>
        <div className="flex w-full gap-2">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => toast.success("Verification email resent.")}
          >
            Resend email
          </Button>
          <Button asChild className="flex-1 bg-gradient-brand">
            <Link to="/login">Go to login</Link>
          </Button>
        </div>
      </div>
    </AuthLayout>
  );
}
