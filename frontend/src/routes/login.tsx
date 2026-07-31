import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader } from "@/components/Loader";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Login — MailSentry" },
      { name: "description", content: "Log in to your MailSentry dashboard." },
    ],
  }),
  component: LoginPage,
});

interface FormValues {
  email: string;
  password: string;
  remember: boolean;
}

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>();

  const onSubmit = async (values: FormValues) => {
    try {
      const res = await login(values.email, values.password);
      if (res.success) {
        toast.success(res.message);
        navigate({ to: "/dashboard" });
      } else {
        toast.error(res.message);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Login failed");
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to continue to MailSentry."
      footer={
        <>
          Don't have an account?{" "}
          <Link to="/signup" className="text-brand hover:underline">
            Sign up
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            {...register("email", {
              required: "Email is required",
              pattern: { value: /^\S+@\S+\.\S+$/, message: "Invalid email" },
            })}
          />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              to="/forgot-password"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              autoComplete="current-password"
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
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <Checkbox {...(register("remember") as any)} /> Remember me
        </label>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gradient-brand shadow-elegant"
        >
          {isSubmitting ? <Loader label="Signing in…" /> : "Sign in"}
        </Button>

        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border/60" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-transparent px-2 text-muted-foreground">or continue with</span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={() => toast.info("Google login is coming soon.")}
        >
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
            <path
              fill="#EA4335"
              d="M12 10.2v3.9h5.5c-.24 1.4-1.66 4.1-5.5 4.1-3.3 0-6-2.72-6-6.1s2.7-6.1 6-6.1c1.9 0 3.16.8 3.88 1.5l2.66-2.55C16.9 3.5 14.66 2.5 12 2.5 6.98 2.5 3 6.5 3 12s3.98 9.5 9 9.5c5.2 0 8.65-3.66 8.65-8.8 0-.6-.06-1.05-.15-1.5H12z"
            />
          </svg>
          Continue with Google
        </Button>
      </form>
    </AuthLayout>
  );
}
