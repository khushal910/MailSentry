import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { EmailSummaryPageView } from "@/components/EmailSummaryPageView";

export const Route = createFileRoute("/dashboard/email-summary/$emailId")({
  head: () => ({
    meta: [
      { title: "AI Email Summary — MailSentry" },
      {
        name: "description",
        content: "Lazy executive email summary generated via Google Gemini 2.5 Flash.",
      },
    ],
  }),
  component: DashboardEmailSummaryPage,
});

function DashboardEmailSummaryPage() {
  const { emailId } = Route.useParams();
  const navigate = useNavigate();

  return (
    <EmailSummaryPageView
      emailId={emailId}
      onBack={() => navigate({ to: "/dashboard/history" })}
    />
  );
}
