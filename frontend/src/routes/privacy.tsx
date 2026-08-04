import { createFileRoute } from "@tanstack/react-router";
import { PublicLayout } from "@/layouts/PublicLayout";
import { motion } from "framer-motion";
import {
  Shield,
  Lock,
  Eye,
  CheckCircle2,
  FileText,
  ExternalLink,
  Mail,
  Key,
  Server,
  RefreshCw,
} from "lucide-react";

export const Route = createFileRoute("/privacy")({
  head: () => ({
    meta: [
      { title: "Privacy Policy — MailSentry" },
      {
        name: "description",
        content:
          "MailSentry Privacy Policy explaining how we protect your Google account data and comply with Google API Services User Data Policy.",
      },
    ],
  }),
  component: PrivacyPolicyPage,
});

const sections = [
  { id: "introduction", title: "1. Introduction & Overview" },
  { id: "who-we-are", title: "2. Who We Are" },
  { id: "information-collection", title: "3. Information We Collect" },
  { id: "gmail-data-access", title: "4. Gmail Data Access & Scopes" },
  { id: "google-limited-use", title: "5. Google Limited Use Compliance" },
  { id: "machine-learning", title: "6. Email Classification & ML Usage" },
  { id: "data-storage-security", title: "7. Data Storage, Encryption & Tokens" },
  { id: "third-party-services", title: "8. Third-Party Infrastructure" },
  { id: "user-rights-deletion", title: "9. User Rights & Data Deletion" },
  { id: "policy-changes-contact", title: "10. Policy Changes & Contact" },
];

function PrivacyPolicyPage() {
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
              <Shield className="h-3.5 w-3.5" />
              <span>Google API Compliance Verified</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight md:text-5xl">
              MailSentry Privacy Policy
            </h1>
            <p className="mt-4 text-base text-muted-foreground">Last Updated: August 2, 2026</p>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              MailSentry is committed to protecting your privacy, securing your email data, and
              maintaining complete transparency regarding how Google user data is accessed,
              processed, and safeguarded.
            </p>
          </motion.div>

          {/* Google Limited Use Banner */}
          <div className="mt-10 overflow-hidden rounded-2xl border border-primary/30 bg-gradient-to-r from-primary/10 via-background to-primary/5 p-6 md:p-8 shadow-sm">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-5">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/20 text-primary">
                <Lock className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  Google API Services User Data Policy Compliance
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  MailSentry’s use and transfer of information received from Google APIs to any
                  other app will adhere to the{" "}
                  <a
                    href="https://developers.google.com/terms/api-services-user-data-policy"
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-primary underline underline-offset-4 hover:text-primary/80"
                  >
                    Google API Services User Data Policy
                  </a>
                  , including the <strong>Limited Use requirements</strong>. We never sell your
                  Gmail data or share it with third-party advertisers.
                </p>
              </div>
            </div>
          </div>

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
                id="introduction"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">1. Introduction & Overview</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    Welcome to MailSentry ("we," "our," or "us"). MailSentry is an artificial
                    intelligence-powered email classification and security application designed to
                    analyze email headers, snippets, and metadata to protect users against spam,
                    phishing attempts, and unwanted email clutter.
                  </p>
                  <p>
                    This Privacy Policy governs your use of our website (
                    <strong>https://mail-sentry-mu.vercel.app/</strong>) and our backend services.
                    It outlines what information we collect when you authenticate with Google, how
                    we use that data, how we store it securely, and your rights as a user.
                  </p>
                </div>
              </section>

              {/* Section 2 */}
              <section
                id="who-we-are"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Server className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">2. Who We Are</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    MailSentry is operated as a SaaS web application hosted on{" "}
                    <strong>Vercel</strong> (frontend) and <strong>Render</strong> (FastAPI
                    backend), utilizing <strong>MongoDB Atlas</strong> as its encrypted primary
                    database provider.
                  </p>
                  <p>
                    If you have questions about this policy or your personal data, you may reach our
                    privacy and engineering team at <strong>privacy@mailsentry.app</strong>.
                  </p>
                </div>
              </section>

              {/* Section 3 */}
              <section
                id="information-collection"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Eye className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">3. Information We Collect</h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-4">
                  <p>We collect information in two primary categories:</p>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-xl border border-border/50 bg-background/60 p-4">
                      <h4 className="font-semibold text-foreground">A. Account Information</h4>
                      <ul className="mt-2 space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                        <li>Your name and email address</li>
                        <li>Hashed password credentials (if signing up natively)</li>
                        <li>Google Profile ID and avatar URL (if signing in via Google)</li>
                      </ul>
                    </div>
                    <div className="rounded-xl border border-border/50 bg-background/60 p-4">
                      <h4 className="font-semibold text-foreground">B. Email & Metadata</h4>
                      <ul className="mt-2 space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                        <li>Gmail Message ID and Thread ID</li>
                        <li>Email subject lines and short text snippets</li>
                        <li>Timestamp headers (Sent/Received date)</li>
                        <li>AI-predicted category labels and confidence scores</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 4 */}
              <section
                id="gmail-data-access"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    4. Gmail Data Access & OAuth Scopes
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    MailSentry integrates with Google Identity Services and the official Gmail REST
                    API v1. We request access only after explicit authorization via Google's consent
                    screen.
                  </p>
                  <div className="rounded-xl border border-border/50 bg-background/60 p-4 space-y-2">
                    <h4 className="font-semibold text-foreground flex items-center gap-2">
                      <Key className="h-4 w-4 text-primary" /> Requested Google OAuth Scopes:
                    </h4>
                    <ul className="space-y-2 text-xs text-muted-foreground">
                      <li>
                        <strong className="text-foreground">
                          https://www.googleapis.com/auth/gmail.readonly:
                        </strong>{" "}
                        Allows MailSentry to inspect new incoming message headers, subjects, and
                        snippets for automated security classification.
                      </li>
                      <li>
                        <strong className="text-foreground">
                          https://www.googleapis.com/auth/userinfo.email & profile:
                        </strong>{" "}
                        Allows MailSentry to authenticate your account and associate your
                        classification history with your user account.
                      </li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* Section 5 */}
              <section
                id="google-limited-use"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    5. Google Limited Use Compliance & Restrictions
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-4">
                  <p>
                    MailSentry strictly adheres to Google's{" "}
                    <strong>Limited Use Requirements</strong>. Specifically:
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-foreground">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      <div>
                        <strong>No Data Sale:</strong> Gmail data is NEVER sold, leased, or
                        monetized under any circumstances.
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-foreground">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      <div>
                        <strong>No Advertising:</strong> Gmail data is NEVER used or transferred for
                        serving advertisements, retargeting, or personalized marketing.
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-foreground">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      <div>
                        <strong>No Human Inspection:</strong> No human employee reads your email
                        content unless you explicitly grant written support permission or it is
                        necessary for security investigation (e.g. debugging a critical error).
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-foreground">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      <div>
                        <strong>Sole Purpose Use:</strong> Gmail data is used strictly to provide
                        and improve user-facing features (spam prediction, classification, and
                        organization).
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 6 */}
              <section
                id="machine-learning"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <RefreshCw className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    6. Email Classification & Machine Learning Usage
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    MailSentry processes text snippets using pre-trained Machine Learning models
                    (Scikit-Learn TF-IDF vectorizers and classification pipelines).
                  </p>
                  <p>
                    Your personal email content is{" "}
                    <strong>NEVER used to train generalized AI models</strong> that are exposed to
                    other users or external third parties. All predictions execute in isolated
                    application memory.
                  </p>
                </div>
              </section>

              {/* Section 7 */}
              <section
                id="data-storage-security"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Lock className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    7. Data Storage, Encryption & Security Measures
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>Security is central to our engineering architecture:</p>
                  <ul className="space-y-2 text-xs text-muted-foreground list-disc list-inside">
                    <li>
                      <strong className="text-foreground">Encryption at Rest:</strong> Sensitive
                      Google OAuth refresh tokens are encrypted using cryptography-grade{" "}
                      <strong>Fernet AES-256 encryption</strong> before being stored in MongoDB
                      Atlas.
                    </li>
                    <li>
                      <strong className="text-foreground">Encryption in Transit:</strong> All HTTP
                      traffic between Vercel, Render, Google APIs, and MongoDB Atlas is enforced via{" "}
                      <strong>TLS 1.3 encryption</strong>.
                    </li>
                    <li>
                      <strong className="text-foreground">HttpOnly Cookies:</strong> JWT access
                      tokens are stored in <strong>SameSite=None; Secure; HttpOnly</strong> cookies
                      to prevent Cross-Site Scripting (XSS) attacks.
                    </li>
                  </ul>
                </div>
              </section>

              {/* Section 8 */}
              <section
                id="third-party-services"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <ExternalLink className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    8. Third-Party Infrastructure Providers
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>We rely on trusted cloud infrastructure providers to operate MailSentry:</p>
                  <div className="grid gap-3 md:grid-cols-2 text-xs">
                    <div className="rounded-xl border border-border/50 bg-background/60 p-3.5">
                      <strong className="text-foreground">Google Cloud Platform:</strong>{" "}
                      Authentication & Gmail API v1.
                    </div>
                    <div className="rounded-xl border border-border/50 bg-background/60 p-3.5">
                      <strong className="text-foreground">MongoDB Atlas:</strong> Managed encrypted
                      cloud database storage.
                    </div>
                    <div className="rounded-xl border border-border/50 bg-background/60 p-3.5">
                      <strong className="text-foreground">Render Services:</strong> Containerized
                      FastAPI backend server hosting.
                    </div>
                    <div className="rounded-xl border border-border/50 bg-background/60 p-3.5">
                      <strong className="text-foreground">Vercel Inc:</strong> Edge CDN & frontend
                      application hosting.
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 9 */}
              <section
                id="user-rights-deletion"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    9. User Rights, Access Revocation & Account Deletion
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-4">
                  <p>You maintain 100% control over your data:</p>
                  <div className="space-y-3">
                    <div className="rounded-xl border border-border/50 bg-background/60 p-4">
                      <h4 className="font-semibold text-foreground text-sm">
                        How to Revoke Google Account Access:
                      </h4>
                      <p className="mt-1 text-xs text-muted-foreground">
                        You can disconnect your Google account inside MailSentry under{" "}
                        <strong>Settings → Connected Accounts</strong> or directly via your{" "}
                        <a
                          href="https://myaccount.google.com/permissions"
                          target="_blank"
                          rel="noreferrer"
                          className="font-semibold text-primary underline underline-offset-4"
                        >
                          Google Account Security Permissions
                        </a>
                        .
                      </p>
                    </div>
                    <div className="rounded-xl border border-border/50 bg-background/60 p-4">
                      <h4 className="font-semibold text-foreground text-sm">
                        How to Request Full Data & Account Deletion:
                      </h4>
                      <p className="mt-1 text-xs text-muted-foreground">
                        You can delete your account and all stored email prediction records inside{" "}
                        <strong>Profile Settings → Danger Zone</strong> or by sending a deletion
                        request to <strong>privacy@mailsentry.app</strong>. Upon deletion, all
                        database records and encrypted tokens are purged immediately.
                      </p>
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 10 */}
              <section
                id="policy-changes-contact"
                className="scroll-mt-24 rounded-2xl border border-border/60 bg-card/40 p-6 md:p-8 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    10. Policy Updates & Contact Information
                  </h2>
                </div>
                <div className="mt-4 text-sm text-muted-foreground leading-relaxed space-y-3">
                  <p>
                    We may update this Privacy Policy periodically to reflect technological or legal
                    updates. Material updates will be communicated via our application interface or
                    email notification.
                  </p>
                  <p>For privacy inquiries or compliance requests:</p>
                  <div className="rounded-xl border border-border/50 bg-background/60 p-4 text-xs space-y-1">
                    <p>
                      <strong className="text-foreground">Email:</strong> privacy@mailsentry.app
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
