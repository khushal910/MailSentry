import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";

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

type LoginSearch = {
  oauth_error?: string;
  redirect?: string;
};

export const Route = createFileRoute("/login")({
  validateSearch: (search: Record<string, unknown>): LoginSearch => ({
    oauth_error: typeof search.oauth_error === "string" ? search.oauth_error : undefined,
    redirect: typeof search.redirect === "string" ? search.redirect : undefined,
  }),
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

import { useMaintenance } from "@/context/MaintenanceContext";

function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const { isMaintenance, adminBypass } = useMaintenance();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const { oauth_error: oauthError, redirect } = Route.useSearch();

  useEffect(() => {
    if (isMaintenance && !adminBypass) {
      navigate({ to: "/maintenance", replace: true });
      return;
    }

    if (oauthError) {
      toast.error(`Google sign-in failed: ${oauthError.replace(/_/g, " ")}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [isMaintenance, adminBypass, oauthError, navigate]);

  useEffect(() => {
    // If the user is already authenticated, send them to target page or dashboard smoothly
    if (!isLoading && isAuthenticated) {
      const target = redirect && redirect.startsWith("/") ? redirect : "/dashboard";
      navigate({ to: target, replace: true });
    }
  }, [isLoading, isAuthenticated, redirect, navigate]);


  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>();

  const onSubmit = async (values: FormValues) => {
    try {
      const res = await login(values.email, values.password);
      if (res.success) {
        const target = redirect && redirect.startsWith("/") ? redirect : "/dashboard";
        navigate({ to: target, replace: true });
      } else {
        toast.error(res.message);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Login failed");
    }
  };

  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleGoogleLogin = () => {
    setIsGoogleLoading(true);
    const rawBase =
      (typeof import.meta !== "undefined" &&
        (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL) ||
      "http://localhost:8000";
    // Normalise: must match the origin where the oauth_state cookie will be set
    const backendUrl = rawBase.replace("127.0.0.1", "localhost");
    window.location.href = `${backendUrl}/auth/google/login`;
  };

  // Show a loading screen while we're checking if the user is already logged in
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
          <Checkbox {...register("remember")} /> Remember me
        </label>

        <Button
          type="submit"
          disabled={isSubmitting || isGoogleLoading}
          className="w-full bg-gradient-brand shadow-elegant"
        >
          {isSubmitting ? <Loader label="Signing in…" /> : "Sign in"}
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
      </form>
    </AuthLayout>
  );
}
