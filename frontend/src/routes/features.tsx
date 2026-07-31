import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Brain,
  Zap,
  Lock,
  BarChart3,
  Sparkles,
  Globe,
  GitBranch,
  Bell,
} from "lucide-react";
import { PublicLayout } from "@/layouts/PublicLayout";

export const Route = createFileRoute("/features")({
  head: () => ({
    meta: [
      { title: "Features — MailSentry" },
      {
        name: "description",
        content:
          "Explore every MailSentry capability: ML spam detection, analytics, real-time API, and more.",
      },
    ],
  }),
  component: FeaturesPage,
});

const features = [
  { icon: Brain, title: "ML Spam Detection", desc: "State-of-the-art models trained on billions of samples." },
  { icon: Zap, title: "Real-time API", desc: "Sub-second inference with global edge deployment." },
  { icon: Lock, title: "Zero-trust Security", desc: "End-to-end encryption, SOC2-aligned processes." },
  { icon: BarChart3, title: "Deep Analytics", desc: "Dashboards for accuracy, threats, and inbox health." },
  { icon: Sparkles, title: "Explainable AI", desc: "See the reasoning behind every prediction." },
  { icon: Globe, title: "Multi-region", desc: "Data residency in US, EU, and APAC on demand." },
  { icon: GitBranch, title: "Webhooks", desc: "Trigger workflows on any classification event." },
  { icon: Bell, title: "Alerting", desc: "Route incidents to Slack, PagerDuty, or email." },
];

function FeaturesPage() {
  return (
    <PublicLayout>
      <section className="mx-auto max-w-7xl px-4 py-20 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">
            Features
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">
            Every tool your team needs
          </h1>
          <p className="mt-4 text-muted-foreground">
            MailSentry ships with the depth of an enterprise product and the
            ergonomics of a modern developer tool.
          </p>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.04 }}
              className="glass rounded-xl p-5 transition-transform hover:-translate-y-0.5"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="glass-strong mt-16 rounded-2xl p-8 shadow-elegant">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">
            Roadmap
          </p>
          <h2 className="mt-2 text-2xl font-bold">Coming soon</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              { title: "Email Ranking", desc: "Prioritize the inbox using AI signals." },
              { title: "AI Email Summary", desc: "One-line summaries of long threads." },
              { title: "Meeting Scheduling", desc: "Detect intent and propose slots." },
            ].map((r) => (
              <div key={r.title} className="rounded-xl border border-border/60 p-4">
                <p className="text-sm font-semibold">{r.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
