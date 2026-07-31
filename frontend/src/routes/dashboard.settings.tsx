import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Moon, Sun, Bell, Lock, Trash2 } from "lucide-react";
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
  const [dark, setDark] = useState(true);
  const [email, setEmailNotif] = useState(true);
  const [push, setPushNotif] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

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
            description="MailSentry is optimized for dark. Light mode is coming soon."
            right={
              <div className="flex items-center gap-2">
                <Switch
                  checked={dark}
                  onCheckedChange={(v) => {
                    setDark(v);
                    toast.info(v ? "Dark mode enabled" : "Light mode coming soon");
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
            right={<Switch checked={email} onCheckedChange={setEmailNotif} />}
          />
          <SettingsRow
            title="Push notifications"
            description="Real-time browser alerts for high-risk predictions."
            right={<Switch checked={push} onCheckedChange={setPushNotif} />}
          />
        </section>

        {/* Security */}
        <section className="glass rounded-2xl p-6">
          <div className="mb-4 flex items-center gap-2">
            <Lock className="h-4 w-4 text-brand" />
            <h2 className="text-base font-semibold">Security</h2>
          </div>
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              toast.success("Password updated");
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="cur">Current password</Label>
              <Input id="cur" type="password" placeholder="••••••••" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new">New password</Label>
              <Input id="new" type="password" placeholder="••••••••" />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit" className="bg-gradient-brand shadow-elegant">
                Update password
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
                      This is permanent. All predictions, history, and settings
                      will be erased.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      onClick={() => {
                        logout();
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
