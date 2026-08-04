import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import {
  Pencil,
  Mail,
  ShieldCheck,
  Calendar,
  Lock,
  CheckCircle2,
  XCircle,
  KeyRound,
  Loader2,
  RefreshCw,
} from "lucide-react";

import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";

import { useAuth } from "@/context/AuthContext";
import { GmailStatusCard } from "@/components/GmailStatusCard";
import { profileApi, type UserProfile } from "@/services/profileApi";
import { formatDate } from "@/utils/format";

export const Route = createFileRoute("/dashboard/profile")({
  head: () => ({
    meta: [
      { title: "User Profile — MailSentry" },
      {
        name: "description",
        content: "Manage your MailSentry account profile, security, and Gmail integrations.",
      },
    ],
  }),
  component: ProfilePage,
});

interface EditProfileForm {
  username: string;
  email: string;
}

interface ChangePasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

function ProfilePage() {
  const { refresh: refreshAuthContext } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Dialog states
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isPasswordOpen, setIsPasswordOpen] = useState(false);
  const [isOtpOpen, setIsOtpOpen] = useState(false);

  // Pending email state for OTP flow
  const [pendingEmail, setPendingEmail] = useState("");
  const [otpInput, setOtpInput] = useState("");
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true);
    setProfileError(null);
    try {
      const data = await profileApi.getProfile();
      setProfile(data);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Failed to load profile.");
    } finally {
      setIsLoadingProfile(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  // Edit Profile Form
  const {
    register: registerEdit,
    handleSubmit: handleSubmitEdit,
    reset: resetEdit,
    formState: { errors: editErrors, isSubmitting: isSubmittingEdit },
  } = useForm<EditProfileForm>();

  // Change Password Form
  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    reset: resetPassword,
    watch: watchPassword,
    formState: { errors: passwordErrors, isSubmitting: isSubmittingPassword },
  } = useForm<ChangePasswordForm>();

  const newPasswordValue = watchPassword("new_password");

  const openEditModal = () => {
    if (profile) {
      resetEdit({
        username: profile.username,
        email: profile.email,
      });
    }
    setIsEditOpen(true);
  };

  const openPasswordModal = () => {
    resetPassword({
      current_password: "",
      new_password: "",
      confirm_password: "",
    });
    setIsPasswordOpen(true);
  };

  // Submit Edit Profile Form
  const onSaveProfile = async (values: EditProfileForm) => {
    if (!profile) return;

    const trimmedUsername = values.username.trim();
    const trimmedEmail = values.email.trim().toLowerCase();

    const usernameChanged = trimmedUsername !== profile.username;
    const emailChanged = trimmedEmail !== profile.email.toLowerCase();

    if (!usernameChanged && !emailChanged) {
      toast.info("No changes detected.");
      setIsEditOpen(false);
      return;
    }

    try {
      // Step 1: Handle Username Change first if updated
      if (usernameChanged) {
        await profileApi.updateUsername(trimmedUsername);
        toast.success("Username updated successfully.");
      }

      // Step 2: Handle Email Change via OTP if updated
      if (emailChanged) {
        const res = await profileApi.requestEmailChange(trimmedEmail);
        setPendingEmail(trimmedEmail);
        setIsEditOpen(false);
        setIsOtpOpen(true);
        setOtpInput("");
        toast.info(res.message || "OTP sent to your new email address.");
        return;
      }

      // If only username changed
      await loadProfile();
      await refreshAuthContext();
      setIsEditOpen(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update profile.");
    }
  };

  // Submit OTP Verification
  const onVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpInput || otpInput.trim().length !== 6) {
      toast.error("Please enter a valid 6-digit OTP code.");
      return;
    }

    setIsVerifyingOtp(true);
    try {
      const res = await profileApi.verifyEmailOtp(otpInput.trim());
      toast.success(res.message || "Email address updated successfully.");
      setIsOtpOpen(false);
      await loadProfile();
      await refreshAuthContext();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "OTP verification failed.");
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  // Resend OTP for Email Change
  const handleResendEmailOtp = async () => {
    if (!pendingEmail) return;
    try {
      const res = await profileApi.requestEmailChange(pendingEmail);
      toast.success(res.message || "A new OTP code has been sent to your email.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to resend OTP.");
    }
  };

  // Submit Change Password Form

  const onChangePassword = async (values: ChangePasswordForm) => {
    try {
      const res = await profileApi.changePassword({
        current_password: values.current_password,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      });
      toast.success(res.message || "Password changed successfully.");
      setIsPasswordOpen(false);
      resetPassword();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to change password.");
    }
  };

  if (isLoadingProfile) {
    return (
      <PageTransition>
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand" />
          <p className="text-sm text-muted-foreground">Loading your profile details…</p>
        </div>
      </PageTransition>
    );
  }

  if (profileError || !profile) {
    return (
      <PageTransition>
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
          <XCircle className="h-10 w-10 text-destructive" />
          <h2 className="text-lg font-semibold">Failed to load profile</h2>
          <p className="text-sm text-muted-foreground max-w-sm">
            {profileError || "Profile information is unavailable."}
          </p>
          <Button variant="outline" onClick={loadProfile}>
            <RefreshCw className="mr-2 h-4 w-4" /> Try Again
          </Button>
        </div>
      </PageTransition>
    );
  }

  const safeProviders = Array.isArray(profile.providers)
    ? profile.providers.filter((p): p is string => typeof p === "string")
    : ["local"];

  const isLocalUser = safeProviders.includes("local");
  const usernameStr = typeof profile.username === "string" ? profile.username : "";
  const emailStr = typeof profile.email === "string" ? profile.email : "";
  const googleEmailStr = typeof profile.google_email === "string" ? profile.google_email : "";
  const displayGoogleEmail = googleEmailStr.trim() || emailStr;
  const roleStr = typeof profile.role === "string" ? profile.role : "USER";

  const initials = (usernameStr || emailStr).slice(0, 2).toUpperCase();

  const providerLabel = safeProviders
    .map((p) => (p === "google" ? "Google OAuth" : "Email + Password"))
    .join(" & ");

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Account Profile</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your personal profile, security credentials, and Gmail integrations.
          </p>
        </div>

        {/* User Card */}
        <div className="glass-strong rounded-2xl p-6 shadow-soft">
          <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
            <Avatar className="h-20 w-20 border border-border/60">
              <AvatarFallback className="bg-brand/20 text-lg font-bold text-foreground">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1 space-y-1">
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-semibold">{usernameStr}</h2>
                <span className="inline-flex items-center gap-1 rounded-full border border-brand/30 bg-brand/10 px-2.5 py-0.5 text-xs font-medium text-brand">
                  <ShieldCheck className="h-3 w-3" />
                  {roleStr.toUpperCase()}
                </span>
              </div>
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="h-3.5 w-3.5" />
                {emailStr}
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-1">
                <span className="flex items-center gap-1">
                  <Lock className="h-3 w-3" />
                  Provider: <strong className="text-foreground font-medium">{providerLabel}</strong>
                </span>
                {profile.created_at && typeof profile.created_at === "string" && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Joined:{" "}
                    <strong className="text-foreground font-medium">
                      {formatDate(profile.created_at)}
                    </strong>
                  </span>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-2 shrink-0 w-full sm:w-auto">
              <Button onClick={openEditModal} className="bg-gradient-brand shadow-elegant">
                <Pencil className="mr-2 h-4 w-4" /> Edit Profile
              </Button>
              {isLocalUser && (
                <Button variant="outline" onClick={openPasswordModal}>
                  <KeyRound className="mr-2 h-4 w-4" /> Change Password
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Gmail Integration Section */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
            Email Integrations & Status
          </h3>
          <GmailStatusCard />
        </div>

        {/* Detailed Metadata Glass Card */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-base font-semibold">Account Information</h3>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 text-sm">
            <div className="rounded-xl border border-border/40 p-3.5 bg-muted/10">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Authentication Status
              </p>
              <p className="mt-1 font-medium flex items-center gap-1.5">
                {profile.is_active ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Account Active
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-destructive" /> Inactive
                  </>
                )}
              </p>
            </div>
            <div className="rounded-xl border border-border/40 p-3.5 bg-muted/10">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Google Connection Status
              </p>
              <p className="mt-1 font-medium flex items-center gap-1.5">
                {profile.google_connected ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Connected (
                    {displayGoogleEmail})
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-muted-foreground" /> Not Connected
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Edit Profile Modal ── */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
            <DialogDescription>
              Update your username or email address. Changing email requires 6-digit OTP
              verification.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitEdit(onSaveProfile)} className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="edit-username">Username</Label>
              <Input
                id="edit-username"
                {...registerEdit("username", {
                  required: "Username is required",
                  minLength: { value: 3, message: "Username must be at least 3 characters" },
                  maxLength: { value: 50, message: "Username cannot exceed 50 characters" },
                })}
              />
              {editErrors.username && (
                <p className="text-xs text-destructive">{editErrors.username.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-email">Email Address</Label>
              <Input
                id="edit-email"
                type="email"
                {...registerEdit("email", {
                  required: "Email is required",
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: "Enter a valid email address",
                  },
                })}
              />
              {editErrors.email && (
                <p className="text-xs text-destructive">{editErrors.email.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Changing your email address will send a 6-digit verification code to the new
                address.
              </p>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmittingEdit}
                className="bg-gradient-brand shadow-elegant"
              >
                {isSubmittingEdit ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving…
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── OTP Verification Modal ── */}
      <Dialog open={isOtpOpen} onOpenChange={setIsOtpOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Enter OTP Code</DialogTitle>
            <DialogDescription>
              We sent a 6-digit code to <strong className="text-foreground">{pendingEmail}</strong>.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={onVerifyOtp} className="space-y-6 py-2">
            <div className="flex flex-col items-center justify-center space-y-3">
              <Label className="text-center text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                6-Digit Verification Code
              </Label>

              <InputOTP maxLength={6} value={otpInput} onChange={(v) => setOtpInput(v)}>
                <InputOTPGroup className="gap-2">
                  <InputOTPSlot
                    index={0}
                    className="w-11 h-12 text-lg font-semibold border-brand/20"
                  />
                  <InputOTPSlot
                    index={1}
                    className="w-11 h-12 text-lg font-semibold border-brand/20"
                  />
                  <InputOTPSlot
                    index={2}
                    className="w-11 h-12 text-lg font-semibold border-brand/20"
                  />
                  <InputOTPSlot
                    index={3}
                    className="w-11 h-12 text-lg font-semibold border-brand/20"
                  />
                  <InputOTPSlot
                    index={4}
                    className="w-11 h-12 text-lg font-semibold border-brand/20"
                  />
                  <InputOTPSlot
                    index={5}
                    className="w-11 h-12 text-lg font-semibold border-brand/20"
                  />
                </InputOTPGroup>
              </InputOTP>
            </div>

            <div className="flex items-center justify-between text-xs pt-1 border-t border-border/40">
              <span className="text-muted-foreground">Didn't receive the code?</span>
              <button
                type="button"
                onClick={handleResendEmailOtp}
                className="text-brand hover:underline font-medium"
              >
                Resend OTP
              </button>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsOtpOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isVerifyingOtp || otpInput.length < 6}
                className="bg-gradient-brand shadow-elegant font-medium"
              >
                {isVerifyingOtp ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Verifying…
                  </>
                ) : (
                  "Verify & Update Email"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── Change Password Modal ── */}
      <Dialog open={isPasswordOpen} onOpenChange={setIsPasswordOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and a new secure password.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitPassword(onChangePassword)} className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="current-pw">Current Password</Label>
              <Input
                id="current-pw"
                type="password"
                {...registerPassword("current_password", {
                  required: "Current password is required",
                })}
              />
              {passwordErrors.current_password && (
                <p className="text-xs text-destructive">
                  {passwordErrors.current_password.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-pw">New Password</Label>
              <Input
                id="new-pw"
                type="password"
                {...registerPassword("new_password", {
                  required: "New password is required",
                  minLength: { value: 8, message: "Password must be at least 8 characters" },
                })}
              />
              {passwordErrors.new_password && (
                <p className="text-xs text-destructive">{passwordErrors.new_password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-pw">Confirm New Password</Label>
              <Input
                id="confirm-pw"
                type="password"
                {...registerPassword("confirm_password", {
                  required: "Please confirm your new password",
                  validate: (v) => v === newPasswordValue || "Passwords do not match",
                })}
              />
              {passwordErrors.confirm_password && (
                <p className="text-xs text-destructive">
                  {passwordErrors.confirm_password.message}
                </p>
              )}
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsPasswordOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmittingPassword}
                className="bg-gradient-brand shadow-elegant"
              >
                {isSubmittingPassword ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Updating…
                  </>
                ) : (
                  "Update Password"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </PageTransition>
  );
}
