import { useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Eye, EyeOff, KeyRound, Mail, ShieldCheck, ArrowLeft } from "lucide-react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";
import { authApi } from "@/services/authApi";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({
    meta: [
      { title: "Reset Password — MailSentry" },
      { name: "description", content: "Reset your MailSentry password using an OTP." },
    ],
  }),
  component: ForgotPasswordPage,
});

type Step = "email" | "otp" | "reset";

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [loading, setLoading] = useState(false);

  // Eye toggles for new password step
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Step 1: Email Form
  const emailForm = useForm<{ email: string }>();

  // Step 3: Reset Password Form
  const resetForm = useForm<{ password: string; confirm: string }>();
  const watchPassword = resetForm.watch("password");

  // Handler Step 1: Submit Email -> Request OTP
  const handleEmailSubmit = async (values: { email: string }) => {
    setLoading(true);
    try {
      await authApi.forgotPassword(values.email);
      setEmail(values.email);
      toast.success("OTP code sent to your email!");
      setStep("otp");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  // Handler Step 2: Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length < 6) {
      toast.error("Please enter the complete 6-digit OTP code");
      return;
    }
    setLoading(true);
    try {
      const res = await authApi.verifyResetOtp({ email, otp });
      if (res.data?.reset_token) {
        setResetToken(res.data.reset_token);
        toast.success("OTP verified successfully!");
        setStep("reset");
      } else {
        toast.error("Verification failed: Token missing");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Invalid or expired OTP");
    } finally {
      setLoading(false);
    }
  };

  // Handler Step 2 Resend OTP
  const handleResendOtp = async () => {
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      toast.success("A new OTP code has been sent to your email");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to resend OTP");
    } finally {
      setLoading(false);
    }
  };

  // Handler Step 3: Reset Password
  const handleResetSubmit = async (values: { password: string; confirm: string }) => {
    setLoading(true);
    try {
      await authApi.resetPassword({ token: resetToken, password: values.password });
      toast.success("Password reset successfully! Please log in.");
      navigate({ to: "/login" });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Password reset failed");
    } finally {
      setLoading(false);
    }
  };

  // Render Subtitles and Titles dynamically per Step
  const getLayoutProps = () => {
    switch (step) {
      case "email":
        return {
          title: "Forgot your password?",
          subtitle: "Enter your email address to receive a 6-digit verification code.",
        };
      case "otp":
        return {
          title: "Enter OTP Code",
          subtitle: `We sent a 6-digit code to ${email}.`,
        };
      case "reset":
        return {
          title: "Set new password",
          subtitle: "Choose a strong password of at least 8 characters.",
        };
    }
  };

  const layoutProps = getLayoutProps();

  return (
    <AuthLayout
      title={layoutProps.title}
      subtitle={layoutProps.subtitle}
      footer={
        <>
          Remember your password?{" "}
          <Link to="/login" className="text-brand hover:underline font-medium">
            Log in
          </Link>
        </>
      }
    >
      {/* ── STEP 1: Enter Email ────────────────────────────────────────────── */}
      {step === "email" && (
        <form onSubmit={emailForm.handleSubmit(handleEmailSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <div className="relative">
              <Input
                id="email"
                type="email"
                placeholder="you@company.com"
                className="pl-10"
                {...emailForm.register("email", {
                  required: "Email is required",
                  pattern: { value: /^\S+@\S+\.\S+$/, message: "Invalid email address" },
                })}
              />
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            </div>
            {emailForm.formState.errors.email && (
              <p className="text-xs text-destructive">
                {emailForm.formState.errors.email.message}
              </p>
            )}
          </div>
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-brand shadow-elegant font-medium"
          >
            {loading ? <Loader label="Sending OTP…" /> : "Send OTP Code"}
          </Button>
        </form>
      )}

      {/* ── STEP 2: Enter & Verify OTP ────────────────────────────────────── */}
      {step === "otp" && (
        <form onSubmit={handleVerifyOtp} className="space-y-6">
          <div className="flex flex-col items-center justify-center space-y-3">
            <Label className="text-center text-xs text-muted-foreground uppercase tracking-wider font-semibold">
              6-Digit Verification Code
            </Label>

            <InputOTP
              maxLength={6}
              value={otp}
              onChange={(v) => setOtp(v)}
            >
              <InputOTPGroup className="gap-2">
                <InputOTPSlot index={0} className="w-11 h-12 text-lg font-semibold border-brand/20" />
                <InputOTPSlot index={1} className="w-11 h-12 text-lg font-semibold border-brand/20" />
                <InputOTPSlot index={2} className="w-11 h-12 text-lg font-semibold border-brand/20" />
                <InputOTPSlot index={3} className="w-11 h-12 text-lg font-semibold border-brand/20" />
                <InputOTPSlot index={4} className="w-11 h-12 text-lg font-semibold border-brand/20" />
                <InputOTPSlot index={5} className="w-11 h-12 text-lg font-semibold border-brand/20" />
              </InputOTPGroup>
            </InputOTP>
          </div>

          <Button
            type="submit"
            disabled={loading || otp.length < 6}
            className="w-full bg-gradient-brand shadow-elegant font-medium"
          >
            {loading ? <Loader label="Verifying OTP…" /> : "Verify Code"}
          </Button>

          <div className="flex items-center justify-between text-xs pt-1 border-t border-border/40">
            <button
              type="button"
              onClick={() => setStep("email")}
              className="text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="h-3 w-3" /> Change email
            </button>
            <button
              type="button"
              onClick={handleResendOtp}
              disabled={loading}
              className="text-brand hover:underline font-medium"
            >
              Resend code
            </button>
          </div>
        </form>
      )}

      {/* ── STEP 3: Reset Password ────────────────────────────────────────── */}
      {step === "reset" && (
        <form onSubmit={resetForm.handleSubmit(handleResetSubmit)} className="space-y-4">
          {/* New Password */}
          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="pr-10"
                {...resetForm.register("password", {
                  required: "Password is required",
                  minLength: { value: Number(import.meta.env.VITE_PASSWORD_MIN_LENGTH), message: `Minimum ${import.meta.env.VITE_PASSWORD_MIN_LENGTH} characters` },
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
            {resetForm.formState.errors.password && (
              <p className="text-xs text-destructive">
                {resetForm.formState.errors.password.message}
              </p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm Password</Label>
            <div className="relative">
              <Input
                id="confirm"
                type={showConfirm ? "text" : "password"}
                placeholder="••••••••"
                className="pr-10"
                {...resetForm.register("confirm", {
                  required: "Please confirm your password",
                  validate: (v) => v === watchPassword || "Passwords do not match",
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
            {resetForm.formState.errors.confirm && (
              <p className="text-xs text-destructive">
                {resetForm.formState.errors.confirm.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-brand shadow-elegant font-medium"
          >
            {loading ? <Loader label="Updating password…" /> : "Update Password"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
