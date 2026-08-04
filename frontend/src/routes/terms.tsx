import { createFileRoute } from "@tanstack/react-router";
import { PublicLayout } from "@/layouts/PublicLayout";
import { motion } from "framer-motion";
import {
  FileText,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Scale,
  Ban,
  Server,
  UserCheck,
  HelpCircle,
} from "lucide-react";

export const Route = createFileRoute("/terms")({
  head: () => ({
    meta: [
      { title: "Terms of Service — MailSentry" },
      {
        name: "description",
        content:
          "MailSentry Terms of Service outlining acceptable use, account responsibilities, Google OAuth permissions, and legal terms.",
      },
    ],
  }),
  component: TermsOfServicePage,
});

const sections = [
  { id: "acceptance", title: "1. Acceptance of Terms" },
  { id: "eligibility", title: "2. Eligibility & Account Security" },
  { id: "google-authentication", title: "3. Google OAuth & Permissions" },
  { id: "acceptable-use", title: "4. Acceptable Use Policy" },
  { id: "prohibited-activities", title: "5. Prohibited Activities" },
  { id: "intellectual-property", title: "6. Intellectual Property" },
  { id: "disclaimers", title: "7. Disclaimer of Warranties" },
  { id: "limitation-liability", title: "8. Limitation of Liability" },
  { id: "termination", title: "9. Suspension & Termination" },
  { id: "governing-law-contact", title: "10. Governing Law & Contact" },
];

function TermsOfServicePage() {
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <PublicLayout>
      <div className="bg-background text-foreground py-12 md:py-20">
        <div className="mx-auto max-w-7xl px-4 md:px-6">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-center max-w-3xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3.5 py-1 text-xs font-semibold text-primary mb-4">
              <Scale className="h-3.5 w-3.5" />
              <span>Legal Terms & Conditions</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight md:text-5xl">
              MailSentry Terms of Service
            </h1>
            <p className="mt-4 text-base text-muted-foreground">Last Updated: August 2, 2026</p>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              Please read these Terms of Service ("Terms") carefully before using the MailSentry
              SaaS web application, API, and associated services.
            </p>
          </motion.div>

          <div className="mt-12 grid gap-10 lg:grid-cols-4">
            {/* Sticky Table of Contents */}
            <div className="hidden lg:block lg:col-span-1">
              <div className="sticky top-24 rounded-2xl border border-border/60 bg-card/50 p-5 backdrop-blur-sm shadow-sm">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">
                  Table of Contents
                </h4>
                <nav className="space-y-1">
                  {sections.map((sec) => (
                    <button
                      key={sec.id}
                      onClick={() => scrollToSection(sec.id)}
                      className="block w-full text-left text-xs font-medium text-muted-foreground hover:text-foreground transition-colors py-1.5 px-2 rounded-lg hover:bg-muted/50 truncate"
                    >
                      {sec.title}
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 space-y-12">
              {/* Section 1 */}
              <section
                id="acceptance"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">1. Acceptance of Terms</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    By creating an account, authenticating via Google OAuth 2.0, or using any
                    portion of MailSentry (<strong>https://mail-sentry-mu.vercel.app/</strong>), you
                    agree to be bound by these Terms of Service and our Privacy Policy.
                  </p>
                  <p>
                    If you do not agree to these Terms, you may not access or use the application.
                  </p>
                </div>
              </section>

              {/* Section 2 */}
              <section
                id="eligibility"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <UserCheck className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    2. Eligibility & Account Security
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    You must be at least 18 years old or the legal age of majority in your
                    jurisdiction to use MailSentry. By accessing the service, you represent and
                    warrant that you have the legal authority to enter into this agreement.
                  </p>
                  <p>
                    You are responsible for maintaining the confidentiality of your login
                    credentials and for all activities conducted through your account.
                  </p>
                </div>
              </section>

              {/* Section 3 */}
              <section
                id="google-authentication"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    3. Google OAuth & Gmail Permissions
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    MailSentry enables seamless authentication via Google Identity Services and
                    connects to the Gmail API v1 to fetch unclassified email metadata.
                  </p>
                  <div className="rounded-xl border border-border/50 bg-background/60 p-4 space-y-2 text-xs">
                    <p className="font-semibold text-foreground">
                      By connecting your Google Account, you agree that:
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>
                        You grant MailSentry read-only permission to retrieve message headers and
                        snippets.
                      </li>
                      <li>
                        You may disconnect MailSentry at any time via Settings or Google Security
                        settings.
                      </li>
                      <li>
                        MailSentry complies strictly with Google's API Services User Data Policy
                        (Limited Use).
                      </li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* Section 4 */}
              <section
                id="acceptable-use"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">4. Acceptable Use Policy</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    You agree to use MailSentry only for lawful purposes related to managing,
                    classifying, and protecting your personal or authorized business email accounts.
                  </p>
                </div>
              </section>

              {/* Section 5 */}
              <section
                id="prohibited-activities"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Ban className="h-5 w-5 text-destructive" />
                  <h2 className="text-xl font-bold tracking-tight">5. Prohibited Activities</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>You agree NOT to engage in any of the following prohibited behaviors:</p>
                  <ul className="grid gap-2 md:grid-cols-2 text-xs">
                    <li className="rounded-lg border border-border/50 bg-background/60 p-3">
                      <strong>Unauthorized Access:</strong> Attempting to access accounts or Gmail
                      data belonging to another individual without explicit consent.
                    </li>
                    <li className="rounded-lg border border-border/50 bg-background/60 p-3">
                      <strong>Reverse Engineering:</strong> Decompiling, reverse engineering, or
                      exploiting security vulnerabilities in MailSentry APIs or ML models.
                    </li>
                    <li className="rounded-lg border border-border/50 bg-background/60 p-3">
                      <strong>Abusive Automation:</strong> Overloading backend infrastructure
                      through denial-of-service (DoS) or unauthorized scraping scripts.
                    </li>
                    <li className="rounded-lg border border-border/50 bg-background/60 p-3">
                      <strong>Malicious Content:</strong> Transmitting malware, viruses, or illegal
                      material through our platform interfaces.
                    </li>
                  </ul>
                </div>
              </section>

              {/* Section 6 */}
              <section
                id="intellectual-property"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Server className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    6. Intellectual Property Rights
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    The MailSentry application, Machine Learning classification models, brand
                    assets, logos, design system, and codebases are the exclusive intellectual
                    property of MailSentry and its licensors.
                  </p>
                </div>
              </section>

              {/* Section 7 */}
              <section
                id="disclaimers"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                  <h2 className="text-xl font-bold tracking-tight">7. Disclaimer of Warranties</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    MailSentry is provided on an <strong>"AS IS"</strong> and{" "}
                    <strong>"AS AVAILABLE"</strong> basis without warranties of any kind, whether
                    express or implied.
                  </p>
                  <p>
                    While our AI classification models maintain high confidence scores, we do not
                    guarantee 100% accuracy in detecting every spam or phishing attempt. Users are
                    encouraged to review critical email classifications manually.
                  </p>
                </div>
              </section>

              {/* Section 8 */}
              <section
                id="limitation-liability"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Scale className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">8. Limitation of Liability</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    To the maximum extent permitted by applicable law, MailSentry shall not be
                    liable for any indirect, incidental, special, consequential, or punitive damages
                    resulting from your use or inability to use the service.
                  </p>
                </div>
              </section>

              {/* Section 9 */}
              <section
                id="termination"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Ban className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    9. Account Suspension & Deletion
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    We reserve the right to suspend or terminate account access if a user violates
                    these Terms or engages in fraudulent activity.
                  </p>
                  <p>
                    You may terminate your account at any time via Profile Settings. Upon
                    termination, all stored email predictions and tokens are deleted.
                  </p>
                </div>
              </section>

              {/* Section 10 */}
              <section
                id="governing-law-contact"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <HelpCircle className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    10. Governing Law & Contact Information
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    These Terms are governed by and construed in accordance with applicable laws
                    without regard to conflict of law principles.
                  </p>
                  <div className="rounded-xl border border-border/50 bg-background/60 p-4 text-xs space-y-1">
                    <p>
                      <strong className="text-foreground">Support Email:</strong>{" "}
                      support@mailsentry.app
                    </p>
                    <p>
                      <strong className="text-foreground">Website:</strong>{" "}
                      https://mail-sentry-mu.vercel.app/
                    </p>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
