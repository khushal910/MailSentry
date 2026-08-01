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
  { icon: Brain, title: "ML Spam Detection", desc: "State-of-the-art models trained on billions of samples.", gradient: "gradient-indigo-cyan" },
  { icon: Zap, title: "Real-time API", desc: "Sub-second inference with global edge deployment.", gradient: "gradient-purple-pink" },
  { icon: Lock, title: "Zero-trust Security", desc: "End-to-end encryption, SOC2-aligned processes.", gradient: "gradient-blue-purple" },
  { icon: BarChart3, title: "Deep Analytics", desc: "Dashboards for accuracy, threats, and inbox health.", gradient: "gradient-emerald-cyan" },
  { icon: Sparkles, title: "Explainable AI", desc: "See the reasoning behind every prediction.", gradient: "gradient-cyan-blue" },
  { icon: Globe, title: "Multi-region", desc: "Data residency in US, EU, and APAC on demand.", gradient: "gradient-indigo-cyan" },
  { icon: GitBranch, title: "Webhooks", desc: "Trigger workflows on any classification event.", gradient: "gradient-purple-pink" },
  { icon: Bell, title: "Alerting", desc: "Route incidents to Slack, PagerDuty, or email.", gradient: "gradient-blue-purple" },
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

        <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.04 }}
              className="glass glow-card-hover rounded-2xl p-6 border border-border/60 flex flex-col justify-between"
            >
              <div>
                <div className={`flex h-11 w-11 items-center justify-center rounded-xl text-white shadow-soft ${f.gradient}`}>
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-base font-bold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="glass-strong mt-16 rounded-3xl p-8 md:p-10 shadow-elegant border border-border/60"
        >
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
              <div key={r.title} className="rounded-xl border border-border/50 bg-card/40 p-5 glow-card-hover">
                <p className="text-sm font-semibold">{r.title}</p>
                <p className="mt-1.5 text-xs text-muted-foreground">{r.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>
    </PublicLayout>
  );
}
