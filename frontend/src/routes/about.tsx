import { createFileRoute } from "@tanstack/react-router";
import { PublicLayout } from "@/layouts/PublicLayout";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — MailSentry" },
      {
        name: "description",
        content:
          "MailSentry is on a mission to make email safer for every team, everywhere.",
      },
    ],
  }),
  component: AboutPage,
});

const values = [
  { title: "Security first", desc: "Every decision starts with 'is this safe for our customers?'" },
  { title: "Explainability", desc: "AI you can trust is AI you can inspect." },
  { title: "Ship weekly", desc: "Iterative improvements beat quarterly rewrites." },
];

function AboutPage() {
  return (
    <PublicLayout>
      <section className="mx-auto max-w-4xl px-4 py-20 md:px-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">
          About
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">
          Making email safer, one inbox at a time.
        </h1>
        <p className="mt-6 text-lg text-muted-foreground">
          MailSentry was born out of a frustration: modern spam filters miss the
          most dangerous emails, and the ones they catch, we already knew about.
          We're building the AI layer email deserves.
        </p>

        <div className="mt-14 grid gap-4 md:grid-cols-3">
          {values.map((v) => (
            <div key={v.title} className="glass rounded-xl p-6">
              <h3 className="text-base font-semibold">{v.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{v.desc}</p>
            </div>
          ))}
        </div>

        <div className="glass-strong mt-14 rounded-2xl p-8">
          <h2 className="text-2xl font-bold">Our story</h2>
          <p className="mt-4 text-muted-foreground">
            Founded in 2025 by a team of security engineers and ML researchers,
            MailSentry started as a weekend project to detect phishing in a
            corporate inbox. Today, we protect thousands of inboxes across
            fintech, healthcare, and SaaS.
          </p>
        </div>
      </section>
    </PublicLayout>
  );
}
