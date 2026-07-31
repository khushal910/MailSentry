import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";
import { authApi } from "@/services/authApi";

export const Route = createFileRoute("/reset-password")({
  head: () => ({
    meta: [
      { title: "Reset password — MailSentry" },
      { name: "description", content: "Choose a new password for your MailSentry account." },
    ],
  }),
  component: ResetPasswordPage,
});

interface FormValues {
  password: string;
  confirm: string;
}

function ResetPasswordPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>();
  const password = watch("password");

  const onSubmit = async (values: FormValues) => {
    try {
      const params = new URLSearchParams(
        typeof window !== "undefined" ? window.location.search : "",
      );
      const token = params.get("token") || "";
      await authApi.resetPassword({ token, password: values.password });
      toast.success("Password updated. You can log in now.");
      navigate({ to: "/login" });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Reset failed");
    }
  };

  return (
    <AuthLayout
      title="Set a new password"
      subtitle="Use at least 8 characters."
      footer={
        <Link to="/login" className="text-brand hover:underline">
          Back to login
        </Link>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="password">New password</Label>
          <Input
            id="password"
            type="password"
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Minimum 8 characters" },
            })}
          />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm">Confirm password</Label>
          <Input
            id="confirm"
            type="password"
            {...register("confirm", {
              required: "Please confirm your password",
              validate: (v) => v === password || "Passwords must match",
            })}
          />
          {errors.confirm && (
            <p className="text-xs text-destructive">{errors.confirm.message}</p>
          )}
        </div>
        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gradient-brand shadow-elegant"
        >
          {isSubmitting ? <Loader label="Updating…" /> : "Update password"}
        </Button>
      </form>
    </AuthLayout>
  );
}
