import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";
import { useAuth } from "@/context/AuthContext";
import { useMaintenance } from "@/context/MaintenanceContext";

type SignupSearch = {
  oauth_error?: string;
};

export const Route = createFileRoute("/signup")({
  validateSearch: (search: Record<string, unknown>): SignupSearch => ({
    oauth_error: typeof search.oauth_error === "string" ? search.oauth_error : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Sign up — MailSentry" },
      {
        name: "description",
        content: "Create your MailSentry account. Free forever plan available.",
      },
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
  const { signup, isAuthenticated, isLoading } = useAuth();
  const { isMaintenance } = useMaintenance();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  useEffect(() => {
    if (isMaintenance) {
      navigate({ to: "/maintenance", replace: true });
    }
  }, [isMaintenance, navigate]);

  const { oauth_error: oauthError } = Route.useSearch();

  useEffect(() => {
    // Show OAuth error toast if redirected back from a failed Google OAuth attempt
    if (oauthError) {
      toast.error(`Google sign-in failed: ${oauthError.replace(/_/g, " ")}`);
      // Clean the URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [oauthError]);

  useEffect(() => {
    // If user is already authenticated, send them to dashboard
    if (!isLoading && isAuthenticated) {
      navigate({ to: "/dashboard" });
    }
  }, [isLoading, isAuthenticated, navigate]);

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
        navigate({ to: "/dashboard", replace: true });
      } else {
        toast.error(res.message);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Sign up failed");
    }
  };

  const handleGoogleLogin = () => {
    setIsGoogleLoading(true);
    const rawBase =
      (typeof import.meta !== "undefined" &&
        (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL) ||
      "http://localhost:8000";
    const backendUrl = rawBase.replace("127.0.0.1", "localhost");
    window.location.href = `${backendUrl}/auth/google/login`;
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="relative h-12 w-12">
          <div className="absolute inset-0 rounded-full border-4 border-muted" />
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-brand" />
        </div>
      </div>
    );
  }

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
          disabled={isSubmitting || isGoogleLoading}
          className="w-full bg-gradient-brand shadow-elegant"
        >
          {isSubmitting ? <Loader label="Creating account…" /> : "Create account"}
        </Button>

        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border/60" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-background px-2 text-muted-foreground">or continue with</span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          className="w-full h-10 font-medium border-border/80 hover:bg-accent/50"
          onClick={handleGoogleLogin}
          disabled={isGoogleLoading || isSubmitting}
        >
          {isGoogleLoading ? (
            <Loader label="Connecting to Google…" />
          ) : (
            <>
              <svg className="mr-2 h-4 w-4 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.11 0-5.74-2.1-6.68-4.93H1.36v3.15C3.34 21.32 7.37 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.32 14.27c-.24-.72-.38-1.49-.38-2.27s.14-1.55.38-2.27V6.58H1.36C.49 8.31 0 10.1 0 12s.49 3.69 1.36 5.42l3.96-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.37 0 3.34 2.68 1.36 6.58l3.96 3.15c.94-2.83 3.57-4.98 6.68-4.98z"
                />
              </svg>
              Continue with Google
            </>
          )}
        </Button>

        <p className="text-center text-xs text-muted-foreground pt-1">
          By continuing you agree to our Terms and Privacy Policy.
        </p>
      </form>
    </AuthLayout>
  );
}
