import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Moon, Sun, Bell, Lock, Trash2, Eye, EyeOff } from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { profileApi } from "@/services/profileApi";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/dashboard/settings")({
  head: () => ({
    meta: [
      { title: "Settings — MailSentry" },
      { name: "description", content: "Configure your MailSentry preferences." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [emailNotif, setEmailNotif] = useState(true);
  const [pushNotif, setPushNotif] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  // Password visibility states
  const [showCurPass, setShowCurPass] = useState(false);
  const [showNewPass, setShowNewPass] = useState(false);
  const [showConfirmPass, setShowConfirmPass] = useState(false);

  // Form input states
  const [curPass, setCurPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    const cur = curPass.trim();
    const newP = newPass.trim();
    const confP = confirmPass.trim();

    if (!cur) {
      toast.error("Current password is required");
      return;
    }
    if (!newP) {
      toast.error("New password is required");
      return;
    }
    if (newP.length < 8) {
      toast.error("New password must be at least 8 characters long");
      return;
    }
    if (newP !== confP) {
      toast.error("New password and confirm password do not match");
      return;
    }

    try {
      setIsUpdatingPassword(true);
      const res = await profileApi.changePassword({
        current_password: cur,
        new_password: newP,
        confirm_password: confP,
      });
      toast.success(res.message || "Password updated successfully");
      setCurPass("");
      setNewPass("");
      setConfirmPass("");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update password";
      toast.error(msg);
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl space-y-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage appearance, notifications, and account security.
          </p>
        </div>

        {/* Theme */}
        <section className="glass rounded-2xl p-6">
          <div className="mb-4 flex items-center gap-2">
            <Sun className="h-4 w-4 text-brand" />
            <h2 className="text-base font-semibold">Appearance</h2>
          </div>
          <SettingsRow
            title="Dark mode"
            description="Toggle between Light and Dark themes across MailSentry."
            right={
              <div className="flex items-center gap-2">
                <Switch
                  checked={theme === "dark"}
                  onCheckedChange={(v) => {
                    setTheme(v ? "dark" : "light");
                    toast.success(v ? "Dark mode enabled" : "Light mode enabled");
                  }}
                />
                <Moon className="h-4 w-4 text-muted-foreground" />
              </div>
            }
          />
        </section>

        {/* Notifications */}
        <section className="glass rounded-2xl p-6">
          <div className="mb-4 flex items-center gap-2">
            <Bell className="h-4 w-4 text-brand" />
            <h2 className="text-base font-semibold">Notifications</h2>
          </div>
          <SettingsRow
            title="Email notifications"
            description="Get an email when suspicious activity is detected."
            right={<Switch checked={emailNotif} onCheckedChange={setEmailNotif} />}
          />
          <SettingsRow
            title="Push notifications"
            description="Real-time browser alerts for high-risk predictions."
            right={<Switch checked={pushNotif} onCheckedChange={setPushNotif} />}
          />
        </section>

        {/* Security */}
        <section className="glass rounded-2xl p-6">
          <div className="mb-4 flex items-center gap-2">
            <Lock className="h-4 w-4 text-brand" />
            <h2 className="text-base font-semibold">Security</h2>
          </div>
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={handlePasswordUpdate}>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="cur">Current password</Label>
              <div className="relative">
                <Input
                  id="cur"
                  type={showCurPass ? "text" : "password"}
                  placeholder="••••••••"
                  value={curPass}
                  onChange={(e) => setCurPass(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowCurPass(!showCurPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showCurPass ? "Hide current password" : "Show current password"}
                >
                  {showCurPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="new">New password</Label>
              <div className="relative">
                <Input
                  id="new"
                  type={showNewPass ? "text" : "password"}
                  placeholder="••••••••"
                  value={newPass}
                  onChange={(e) => setNewPass(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPass(!showNewPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showNewPass ? "Hide new password" : "Show new password"}
                >
                  {showNewPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm">Confirm new password</Label>
              <div className="relative">
                <Input
                  id="confirm"
                  type={showConfirmPass ? "text" : "password"}
                  placeholder="••••••••"
                  value={confirmPass}
                  onChange={(e) => setConfirmPass(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPass(!showConfirmPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showConfirmPass ? "Hide confirm password" : "Show confirm password"}
                >
                  {showConfirmPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="sm:col-span-2 pt-1">
              <Button
                type="submit"
                disabled={isUpdatingPassword}
                className="bg-gradient-brand shadow-elegant"
              >
                {isUpdatingPassword ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Updating…
                  </>
                ) : (
                  "Update password"
                )}
              </Button>
            </div>
          </form>
        </section>

        {/* Delete Account */}
        <section className="glass rounded-2xl border border-destructive/30 p-6">
          <div className="mb-4 flex items-center gap-2">
            <Trash2 className="h-4 w-4 text-destructive" />
            <h2 className="text-base font-semibold">Danger zone</h2>
          </div>
          <SettingsRow
            title="Delete account"
            description="Permanently remove your account, history, and API keys. This cannot be undone."
            right={
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive">Delete account</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete your account?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This is permanent. All predictions, history, and settings will be erased.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      onClick={async () => {
                        await logout();
                        toast.success("Account deleted");
                        navigate({ to: "/" });
                      }}
                    >
                      Yes, delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            }
          />
        </section>
      </div>
    </PageTransition>
  );
}

function SettingsRow({
  title,
  description,
  right,
}: {
  title: string;
  description: string;
  right: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-t border-border/40 py-4 first:border-t-0 first:pt-0">
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="shrink-0">{right}</div>
    </div>
  );
}
