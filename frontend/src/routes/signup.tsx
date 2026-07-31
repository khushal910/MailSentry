import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [
      { title: "Sign up — MailSentry" },
      { name: "description", content: "Create your MailSentry account. Free forever plan available." },
    ],
  }),
  component: SignupPage,
});

interface FormValues {
  name: string;
  email: string;
  password: string;
  confirm: string;
}

function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>();
  const password = watch("password");

  const onSubmit = async (values: FormValues) => {
    try {
      const res = await signup(values.name, values.email, values.password);
      if (res.success) {
        toast.success(res.message);
        navigate({ to: "/dashboard" });
      } else {
        toast.error(res.message);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Sign up failed");
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start protecting your inbox in under a minute."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-brand hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Full name</Label>
          <Input
            id="name"
            placeholder="Jane Doe"
            {...register("name", {
              required: "Name is required",
              maxLength: { value: 80, message: "Too long" },
            })}
          />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="jane@company.com"
            {...register("email", {
              required: "Email is required",
              pattern: { value: /^\S+@\S+\.\S+$/, message: "Invalid email" },
            })}
          />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              className="pr-10"
              {...register("password", {
                required: "Password is required",
                minLength: {
                  value: Number(import.meta.env.VITE_PASSWORD_MIN_LENGTH),
                  message: `Minimum ${import.meta.env.VITE_PASSWORD_MIN_LENGTH} characters`,
                },
              })}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm">Confirm password</Label>
          <div className="relative">
            <Input
              id="confirm"
              type={showConfirm ? "text" : "password"}
              placeholder="••••••••"
              className="pr-10"
              {...register("confirm", {
                required: "Please confirm your password",
                validate: (v) => v === password || "Passwords must match",
              })}
            />
            <button
              type="button"
              onClick={() => setShowConfirm((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
            >
              {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirm && <p className="text-xs text-destructive">{errors.confirm.message}</p>}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gradient-brand shadow-elegant"
        >
          {isSubmitting ? <Loader label="Creating account…" /> : "Create account"}
        </Button>

        <p className="text-center text-xs text-muted-foreground">
          By continuing you agree to our Terms and Privacy Policy.
        </p>
      </form>
    </AuthLayout>
  );
}
