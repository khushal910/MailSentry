import { createFileRoute, Link } from "@tanstack/react-router";
import { Check } from "lucide-react";
import { PublicLayout } from "@/layouts/PublicLayout";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export const Route = createFileRoute("/pricing")({
  head: () => ({
    meta: [
      { title: "Pricing — MailSentry" },
      {
        name: "description",
        content:
          "Straightforward plans for individuals, teams, and enterprises. Start free, scale as you grow.",
      },
    ],
  }),
  component: PricingPage,
});

const tiers = [
  {
    name: "Starter",
    price: "$0",
    period: "forever",
    desc: "For hobbyists and evaluations.",
    features: ["100 predictions/mo", "Web dashboard", "Community support"],
  },
  {
    name: "Pro",
    price: "$29",
    period: "/ month",
    featured: true,
    desc: "For small teams shipping fast.",
    features: ["10,000 predictions/mo", "History & analytics", "API access", "Priority support"],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "For regulated & high-volume orgs.",
    features: [
      "Unlimited predictions",
      "SSO / SAML",
      "SLA & DPA",
      "Dedicated CSM",
      "Custom data residency",
    ],
  },
];

function PricingPage() {
  return (
    <PublicLayout>
      <section className="mx-auto max-w-7xl px-4 py-20 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">Pricing</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-muted-foreground">
            Start free. Upgrade when it matters. Cancel any time.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {tiers.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.08 }}
              className={`glass glow-card-hover rounded-2xl p-6 flex flex-col justify-between ${
                t.featured
                  ? "border-brand/50 bg-brand/5 shadow-elegant relative overflow-hidden"
                  : "border-border/60"
              }`}
            >
              {t.featured && (
                <div className="absolute -top-12 -right-12 h-32 w-32 bg-gradient-brand opacity-20 blur-2xl pointer-events-none" />
              )}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold">{t.name}</h3>
                  {t.featured && (
                    <span className="rounded-full bg-brand/15 border border-brand/30 px-2.5 py-0.5 text-xs font-semibold text-brand">
                      Popular
                    </span>
                  )}
                </div>
                <p className="mt-1.5 text-sm text-muted-foreground">{t.desc}</p>
                <div className="mt-6 flex items-baseline gap-1">
                  <span className="text-4xl font-bold tracking-tight">{t.price}</span>
                  <span className="text-sm text-muted-foreground">{t.period}</span>
                </div>
                <ul className="mt-6 space-y-2.5 text-sm">
                  {t.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-muted-foreground">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <Button
                asChild
                className={`mt-8 w-full ${t.featured ? "bg-gradient-brand shadow-elegant btn-gradient-glow" : "glass"}`}
                variant={t.featured ? "default" : "outline"}
              >
                <Link to="/signup">Get {t.name}</Link>
              </Button>
            </motion.div>
          ))}
        </div>

        <div className="mx-auto mt-14 max-w-2xl text-center text-sm text-muted-foreground">
          Need something custom?{" "}
          <Link to="/contact" className="text-brand font-medium hover:underline">
            Talk to sales
          </Link>
          .
        </div>
      </section>
    </PublicLayout>
  );
}
