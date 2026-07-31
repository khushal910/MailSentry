import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Pencil, Mail, ShieldCheck } from "lucide-react";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/dashboard/profile")({
  head: () => ({
    meta: [
      { title: "Profile — MailSentry" },
      { name: "description", content: "Manage your MailSentry profile." },
    ],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user, setUser } = useAuth();
  const [open, setOpen] = useState(false);

  const displayUser = user ?? {
    id: "demo",
    name: "Demo User",
    email: "demo@mailsentry.ai",
    role: "Owner",
    avatarUrl: undefined,
  };

  const initials = displayUser.name
    .split(" ")
    .map((s) => s[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<{ name: string; email: string }>({
    defaultValues: { name: displayUser.name, email: displayUser.email },
  });

  const onSubmit = async (values: { name: string; email: string }) => {
    await new Promise((r) => setTimeout(r, 500));
    setUser({ ...displayUser, ...values });
    toast.success("Profile updated");
    setOpen(false);
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your account details and role.
        </p>

        <div className="glass-strong mt-6 rounded-2xl p-6 shadow-soft">
          <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
            <Avatar className="h-20 w-20 border border-border/60">
              <AvatarImage src={displayUser.avatarUrl} />
              <AvatarFallback className="bg-brand/20 text-lg text-foreground">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <h2 className="text-xl font-semibold">{displayUser.name}</h2>
              <p className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="h-3.5 w-3.5" />
                {displayUser.email}
              </p>
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-2.5 py-1 text-xs font-medium text-brand">
                <ShieldCheck className="h-3.5 w-3.5" />
                {displayUser.role}
              </span>
            </div>
            <Button
              onClick={() => setOpen(true)}
              className="bg-gradient-brand shadow-elegant"
            >
              <Pencil className="mr-2 h-4 w-4" /> Edit profile
            </Button>
          </div>
        </div>

        <div className="glass mt-4 rounded-2xl p-6">
          <h3 className="text-base font-semibold">Account activity</h3>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                Member since
              </p>
              <p className="mt-1 text-sm">Jan 2026</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                Predictions
              </p>
              <p className="mt-1 text-sm">1,284</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                Plan
              </p>
              <p className="mt-1 text-sm">Pro</p>
            </div>
          </div>
        </div>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit profile</DialogTitle>
            <DialogDescription>
              Update your name and email — changes take effect immediately.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="p-name">Name</Label>
              <Input
                id="p-name"
                {...register("name", { required: "Name is required", maxLength: 80 })}
              />
              {errors.name && (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="p-email">Email</Label>
              <Input
                id="p-email"
                type="email"
                {...register("email", {
                  required: "Email is required",
                  pattern: { value: /^\S+@\S+\.\S+$/, message: "Invalid email" },
                })}
              />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-gradient-brand"
              >
                Save changes
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </PageTransition>
  );
}
