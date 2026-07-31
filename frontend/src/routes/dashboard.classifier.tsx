import { createFileRoute } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { Wand2, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Loader } from "@/components/Loader";
import { ResultCard } from "@/components/ResultCard";
import { usePrediction } from "@/context/PredictionContext";

export const Route = createFileRoute("/dashboard/classifier")({
  head: () => ({
    meta: [
      { title: "Email Classifier — MailSentry" },
      { name: "description", content: "Run an email through the MailSentry AI classifier." },
    ],
  }),
  component: ClassifierPage,
});

interface FormValues {
  subject: string;
  message: string;
}

function ClassifierPage() {
  const { predict, isPredicting, latest, reset } = usePrediction();
  const {
    register,
    handleSubmit,
    reset: resetForm,
    formState: { errors },
  } = useForm<FormValues>();

  const onSubmit = async (values: FormValues) => {
    try {
      await predict(values);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Prediction failed");
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-4xl">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Email Classifier</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Paste an email and let MailSentry analyze it in real time.
          </p>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-5">
          <motion.form
            onSubmit={handleSubmit(onSubmit)}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-strong space-y-5 rounded-2xl p-6 shadow-soft lg:col-span-3"
          >
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                placeholder="e.g. Urgent: verify your account"
                {...register("subject", {
                  required: "Subject is required",
                  maxLength: { value: 200, message: "Max 200 characters" },
                })}
              />
              {errors.subject && (
                <p className="text-xs text-destructive">{errors.subject.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="message">Message</Label>
              <Textarea
                id="message"
                rows={10}
                placeholder="Paste the email body here…"
                {...register("message", {
                  required: "Message is required",
                  maxLength: { value: 5000, message: "Max 5000 characters" },
                })}
              />
              {errors.message && (
                <p className="text-xs text-destructive">{errors.message.message}</p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="submit"
                disabled={isPredicting}
                className="bg-gradient-brand shadow-elegant"
              >
                {isPredicting ? (
                  <Loader label="Analyzing…" />
                ) : (
                  <>
                    <Wand2 className="mr-2 h-4 w-4" /> Predict
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  resetForm();
                  reset();
                }}
              >
                <RotateCcw className="mr-2 h-4 w-4" /> Reset
              </Button>
            </div>
          </motion.form>

          <div className="lg:col-span-2">
            {latest ? (
              <ResultCard result={latest} />
            ) : (
              <div className="glass flex h-full min-h-[280px] flex-col items-center justify-center rounded-2xl p-6 text-center">
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <Wand2 className="h-5 w-5" />
                </div>
                <p className="text-sm font-medium">No prediction yet</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Submit an email to see the result here.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
