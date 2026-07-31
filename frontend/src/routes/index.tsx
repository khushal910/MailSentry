import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  Sparkles,
  BarChart3,
  Lock,
  Brain,
  Check,
  PlayCircle,
  Star,
} from "lucide-react";
import { PublicLayout } from "@/layouts/PublicLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MailSentry — AI-powered spam & phishing protection" },
      {
        name: "description",
        content:
          "Detect spam emails instantly with machine learning. MailSentry gives your inbox enterprise-grade AI protection.",
      },
    ],
  }),
  component: LandingPage,
});

const features = [
  {
    icon: Brain,
    title: "ML Spam Detection",
    desc: "Trained on millions of samples with continuous learning.",
  },
  {
    icon: Zap,
    title: "Real-time Predictions",
    desc: "Sub-second inference so nothing slows your workflow.",
  },
  {
    icon: Lock,
    title: "Enterprise Security",
    desc: "SOC2-aligned architecture, encrypted end-to-end.",
  },
  {
    icon: BarChart3,
    title: "Rich Analytics",
    desc: "Track accuracy, threats blocked, and inbox health.",
  },
];

const steps = [
  {
    step: "01",
    title: "Paste your email",
    desc: "Drop in the subject and body — that's all we need.",
  },
  {
    step: "02",
    title: "AI analyzes signals",
    desc: "Our model scores hundreds of linguistic & behavioral cues.",
  },
  {
    step: "03",
    title: "Get a verdict",
    desc: "See confidence, reasoning, and next-step recommendations.",
  },
];

const testimonials = [
  {
    quote:
      "MailSentry caught a phishing attempt our Google filter missed. It paid for itself the first week.",
    name: "Priya Shah",
    role: "Head of IT, Northwind",
  },
  {
    quote:
      "Clean, fast, and the reasoning breakdown is gold for our SOC team.",
    name: "Marcus Lee",
    role: "Security Engineer, Vercel-scale startup",
  },
  {
    quote:
      "Deployed to 400 seats in an afternoon. Nothing else comes close.",
    name: "Elena Rossi",
    role: "CTO, Fintech",
  },
];

const tiers = [
  {
    name: "Starter",
    price: "$0",
    period: "forever",
    features: ["100 predictions/mo", "Web dashboard", "Community support"],
  },
  {
    name: "Pro",
    price: "$29",
    period: "/ month",
    featured: true,
    features: [
      "10,000 predictions/mo",
      "History & analytics",
      "Priority support",
      "API access",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    features: ["Unlimited predictions", "SSO / SAML", "SLA & DPA", "Dedicated CSM"],
  },
];

const faqs = [
  {
    q: "How accurate is MailSentry?",
    a: "Our model consistently benchmarks above 98% F1 on real-world corpora and improves weekly.",
  },
  {
    q: "Do you store my emails?",
    a: "By default we do not persist message content. Predictions can be stored anonymously for analytics.",
  },
  {
    q: "Is there an API?",
    a: "Yes — Pro and Enterprise plans include a REST API with typed SDKs coming soon.",
  },
  {
    q: "What's coming next?",
    a: "Email ranking, AI summaries, and calendar scheduling are on the roadmap.",
  },
];

function LandingPage() {
  return (
    <PublicLayout>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-hero">
        <div className="grid-pattern absolute inset-0 opacity-40" />
        <div className="relative mx-auto grid max-w-7xl gap-12 px-4 py-24 md:grid-cols-2 md:px-6 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col justify-center"
          >
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-border/60 bg-muted/40 px-3 py-1 text-xs text-muted-foreground backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-brand" />
              Powered by Machine Learning
            </div>
            <h1 className="mt-6 text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl">
              Protect your inbox with{" "}
              <span className="gradient-text">AI</span>
            </h1>
            <p className="mt-5 max-w-lg text-base text-muted-foreground md:text-lg">
              Detect spam emails instantly using Machine Learning. MailSentry
              scores every message with confidence & reasoning — before it
              reaches your team.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button
                asChild
                size="lg"
                className="bg-gradient-brand text-primary-foreground shadow-elegant hover:opacity-95"
              >
                <Link to="/signup">
                  Get Started <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="glass">
                <Link to="/dashboard/classifier">
                  <PlayCircle className="mr-2 h-4 w-4" />
                  View Demo
                </Link>
              </Button>
            </div>
            <div className="mt-10 flex items-center gap-6 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-success" /> No credit card
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-success" /> 99.9% uptime
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-success" /> SOC2-aligned
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="relative"
          >
            <div className="glass-strong relative rounded-2xl p-6 shadow-elegant">
              <div className="mb-4 flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-warning/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-success/60" />
                <span className="ml-3 text-xs text-muted-foreground">
                  mailsentry / classifier
                </span>
              </div>
              <div className="space-y-3">
                <div className="rounded-lg border border-border/60 bg-background/40 p-3">
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">
                    Subject
                  </p>
                  <p className="mt-1 text-sm text-foreground">
                    URGENT: Your account has been compromised — verify now
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 bg-background/40 p-3">
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">
                    Message
                  </p>
                  <p className="mt-1 line-clamp-3 text-sm text-muted-foreground">
                    Click here immediately to secure your account and claim your
                    reward before it expires…
                  </p>
                </div>
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.4 }}
                  className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/10 p-3"
                >
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-destructive" />
                    <span className="text-sm font-medium text-destructive">
                      Spam detected
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    98.34% confidence
                  </span>
                </motion.div>
              </div>
            </div>
            <div className="absolute -inset-8 -z-10 rounded-3xl bg-gradient-glow blur-3xl" />
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-7xl px-4 py-24 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">
            Features
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
            Everything you need to defend your inbox
          </h2>
          <p className="mt-3 text-muted-foreground">
            Built for teams that treat email as critical infrastructure.
          </p>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
            >
              <Card className="glass h-full rounded-xl border-border/60 p-5 transition-transform hover:-translate-y-0.5">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold">{f.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-border/60 bg-muted/10">
        <div className="mx-auto max-w-7xl px-4 py-24 md:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand">
              How it works
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
              Three steps to a safer inbox
            </h2>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="glass rounded-xl p-6"
              >
                <span className="text-sm font-semibold text-brand">{s.step}</span>
                <h3 className="mt-3 text-lg font-semibold">{s.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Why MailSentry */}
      <section className="mx-auto max-w-7xl px-4 py-24 md:px-6">
        <div className="grid gap-10 md:grid-cols-2 md:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-brand">
              Why MailSentry
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
              Built by people who ship security software.
            </h2>
            <p className="mt-4 text-muted-foreground">
              MailSentry combines classical ML with modern LLM signals to catch
              the phishing attempts your provider misses — without the noise of
              overzealous filters.
            </p>
            <ul className="mt-6 space-y-3 text-sm">
              {[
                "Explainable predictions — see exactly why",
                "Model updated continuously, no version pinning",
                "Runs on your infrastructure or ours",
              ].map((x) => (
                <li key={x} className="flex items-start gap-2">
                  <Check className="mt-0.5 h-4 w-4 text-success" />
                  <span>{x}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-strong rounded-2xl p-8 shadow-elegant">
            <div className="grid grid-cols-2 gap-4">
              {[
                { k: "Accuracy", v: "98.4%" },
                { k: "Emails scanned", v: "12M+" },
                { k: "Avg. latency", v: "180ms" },
                { k: "Uptime", v: "99.99%" },
              ].map((m) => (
                <div key={m.k} className="rounded-lg border border-border/60 p-4">
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    {m.k}
                  </p>
                  <p className="mt-2 text-2xl font-semibold gradient-text">{m.v}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="border-y border-border/60 bg-muted/10">
        <div className="mx-auto max-w-7xl px-4 py-24 md:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand">
              Loved by teams
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
              Trusted across industries
            </h2>
          </div>
          <div className="mt-12 grid gap-4 md:grid-cols-3">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="glass rounded-xl p-6"
              >
                <div className="flex gap-0.5 text-warning">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} className="h-3.5 w-3.5 fill-current" />
                  ))}
                </div>
                <p className="mt-4 text-sm text-foreground">"{t.quote}"</p>
                <div className="mt-4 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">{t.name}</span> ·{" "}
                  {t.role}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="mx-auto max-w-7xl px-4 py-24 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">
            Pricing
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
            Simple, honest pricing
          </h2>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {tiers.map((t) => (
            <div
              key={t.name}
              className={`glass rounded-2xl p-6 ${
                t.featured ? "border-brand/40 shadow-elegant" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{t.name}</h3>
                {t.featured && (
                  <span className="rounded-full bg-brand/10 px-2 py-0.5 text-xs text-brand">
                    Popular
                  </span>
                )}
              </div>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-bold tracking-tight">{t.price}</span>
                <span className="text-sm text-muted-foreground">{t.period}</span>
              </div>
              <ul className="mt-6 space-y-2 text-sm">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-muted-foreground">
                    <Check className="mt-0.5 h-4 w-4 text-success" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Button
                asChild
                className={`mt-6 w-full ${
                  t.featured ? "bg-gradient-brand" : ""
                }`}
                variant={t.featured ? "default" : "outline"}
              >
                <Link to="/pricing">Choose {t.name}</Link>
              </Button>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-3xl px-4 pb-24 md:px-6">
        <div className="text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">
            FAQ
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
            Frequently asked questions
          </h2>
        </div>
        <Accordion type="single" collapsible className="mt-10">
          {faqs.map((f) => (
            <AccordionItem
              key={f.q}
              value={f.q}
              className="glass mb-2 rounded-lg px-4"
            >
              <AccordionTrigger className="text-left text-sm hover:no-underline">
                {f.q}
              </AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground">
                {f.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>
    </PublicLayout>
  );
}
