import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";
import { authApi } from "@/services/authApi";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({
    meta: [
      { title: "Forgot password — MailSentry" },
      { name: "description", content: "Reset your MailSentry password." },
    ],
  }),
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [isSent, setIsSent] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<{ email: string }>();

  const onSubmit = async (values: { email: string }) => {
    try {
      await authApi.forgotPassword(values.email);
      toast.success("If an account exists, we've sent reset instructions.");
      setIsSent(true);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Something went wrong");
    }
  };

  return (
    <AuthLayout
      title="Forgot your password?"
      subtitle="We'll email you a secure link to reset it."
      footer={
        <>
          Remember it?{" "}
          <Link to="/login" className="text-brand hover:underline">
            Back to login
          </Link>
        </>
      }
    >
      {isSent ? (
        <div className="rounded-lg border border-success/30 bg-success/10 p-4 text-sm text-success">
          Check your inbox for a reset link. It may take a minute to arrive.
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@company.com"
              {...register("email", {
                required: "Email is required",
                pattern: { value: /^\S+@\S+\.\S+$/, message: "Invalid email" },
              })}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gradient-brand shadow-elegant"
          >
            {isSubmitting ? <Loader label="Sending…" /> : "Send reset link"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
