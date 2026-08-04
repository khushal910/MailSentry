import { createFileRoute } from "@tanstack/react-router";
import { PublicLayout } from "@/layouts/PublicLayout";
import { motion } from "framer-motion";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — MailSentry" },
      {
        name: "description",
        content: "MailSentry is on a mission to make email safer for every team, everywhere.",
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
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">About</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">
            Making email safer, one inbox at a time.
          </h1>
          <p className="mt-6 text-lg text-muted-foreground leading-relaxed">
            MailSentry was born out of a frustration: modern spam filters miss the most dangerous
            emails, and the ones they catch, we already knew about. We're building the AI layer
            email deserves.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {values.map((v, i) => (
            <motion.div
              key={v.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.08 }}
              className="glass glow-card-hover rounded-2xl p-6 border border-border/60"
            >
              <h3 className="text-base font-bold">{v.title}</h3>
              <p className="mt-2.5 text-sm text-muted-foreground leading-relaxed">{v.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="glass-strong mt-14 rounded-3xl p-8 md:p-10 shadow-elegant border border-border/60"
        >
          <h2 className="text-2xl font-bold">Our story</h2>
          <p className="mt-4 text-muted-foreground leading-relaxed">
            Founded by a team of security engineers and ML researchers, MailSentry started as a
            project to detect phishing in enterprise inboxes. Today, we protect thousands of inboxes
            across fintech, healthcare, and SaaS.
          </p>
        </motion.div>
      </section>
    </PublicLayout>
  );
}
