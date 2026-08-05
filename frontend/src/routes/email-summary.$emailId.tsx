import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { EmailSummaryPageView } from "@/components/EmailSummaryPageView";

export const Route = createFileRoute("/email-summary/$emailId")({
  head: () => ({
    meta: [
      { title: "AI Email Summary — MailSentry" },
      {
        name: "description",
        content: "Lazy executive email summary generated via Google Gemini 2.5 Flash.",
      },
    ],
  }),
  component: StandaloneEmailSummaryPage,
});

function StandaloneEmailSummaryPage() {
  const { emailId } = Route.useParams();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <EmailSummaryPageView
        emailId={emailId}
        onBack={() => navigate({ to: "/dashboard/history" })}
      />
    </div>
  );
}
