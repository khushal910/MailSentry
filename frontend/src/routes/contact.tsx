import { createFileRoute } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Mail, MessageSquare, User } from "lucide-react";
import { PublicLayout } from "@/layouts/PublicLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";

export const Route = createFileRoute("/contact")({
  head: () => ({
    meta: [
      { title: "Contact — MailSentry" },
      {
        name: "description",
        content: "Get in touch with the MailSentry team. We'd love to hear from you.",
      },
    ],
  }),
  component: ContactPage,
});

interface FormValues {
  name: string;
  email: string;
  message: string;
}

function ContactPage() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>();

  const onSubmit = async (values: FormValues) => {
    await new Promise((r) => setTimeout(r, 800));
    toast.success("Message sent — we'll reply within 1 business day.");
    reset();
  };

  return (
    <PublicLayout>
      <section className="mx-auto grid max-w-5xl gap-10 px-4 py-20 md:grid-cols-2 md:px-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">
            Contact
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">
            Get in touch
          </h1>
          <p className="mt-4 text-muted-foreground">
            Questions, partnerships, security disclosures — we read everything.
          </p>
          <div className="mt-8 space-y-4 text-sm">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Mail className="h-4 w-4 text-brand" /> hello@mailsentry.ai
            </div>
            <div className="flex items-center gap-3 text-muted-foreground">
              <MessageSquare className="h-4 w-4 text-brand" /> Response within 24h
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="glass-strong space-y-5 rounded-2xl p-6 shadow-elegant"
        >
          <div className="space-y-2">
            <Label htmlFor="name">
              <User className="mr-1 inline h-3.5 w-3.5" />
              Name
            </Label>
            <Input
              id="name"
              placeholder="Jane Doe"
              {...register("name", { required: "Name is required", maxLength: 100 })}
            />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
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
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              rows={5}
              placeholder="How can we help?"
              {...register("message", {
                required: "Message is required",
                maxLength: 1000,
              })}
            />
            {errors.message && (
              <p className="text-xs text-destructive">{errors.message.message}</p>
            )}
          </div>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gradient-brand shadow-elegant"
          >
            {isSubmitting ? <Loader label="Sending…" /> : "Send message"}
          </Button>
        </form>
      </section>
    </PublicLayout>
  );
}
