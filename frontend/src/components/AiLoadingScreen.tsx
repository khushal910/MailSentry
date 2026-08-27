import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, Brain, Sparkles, Cpu, Zap, Lock } from "lucide-react";

interface AiLoadingScreenProps {
  title?: string;
  subtitle?: string;
  className?: string;
}

const AI_CUES = [
  {
    icon: ShieldCheck,
    title: "Verifying Cryptographic Credentials",
    detail: "Validating multi-factor authentication tokens...",
  },
  {
    icon: Brain,
    title: "Activating Neural Threat Matrix",
    detail: "Loading Transformer & Bayesian spam detection layers...",
  },
  {
    icon: Zap,
    title: "Calibrating NLP Intelligence",
    detail: "Evaluating real-time semantic heuristics & phishing vectors...",
  },
  {
    icon: Lock,
    title: "Securing Inbox Guardian Stream",
    detail: "Establishing TLS 1.3 encrypted telemetry channel...",
  },
  {
    icon: Cpu,
    title: "Synchronizing Defense Protocols",
    detail: "Calibrating machine learning inference engine...",
  },
  {
    icon: Sparkles,
    title: "Launching MailSentry Command Center",
    detail: "Preparing your personalized security overview...",
  },
];

const SECURITY_TIPS = [
  "MailSentry analyzes email semantics in under 15ms using optimized NLP models.",
  "Automated domain reputation and SPF/DKIM verification protect against spoofing.",
  "Real-time ML feature extraction stops zero-day phishing before it reaches your team.",
  "Continuous learning algorithms adapt to novel evasion techniques dynamically.",
];

export function AiLoadingScreen({
  title = "Authenticating Secure Session",
  subtitle = "MailSentry AI engine is preparing your protected workspace...",
  className = "",
}: AiLoadingScreenProps) {
  const [cueIndex, setCueIndex] = useState(0);
  const [tipIndex, setTipIndex] = useState(0);
  const [progress, setProgress] = useState(15);

  useEffect(() => {
    const cueInterval = setInterval(() => {
      setCueIndex((prev) => (prev + 1) % AI_CUES.length);
    }, 1800);

    const tipInterval = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % SECURITY_TIPS.length);
    }, 3600);

    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) return 95;
        return prev + Math.floor(Math.random() * 12) + 6;
      });
    }, 300);

    return () => {
      clearInterval(cueInterval);
      clearInterval(tipInterval);
      clearInterval(progressInterval);
    };
  }, []);

  const CurrentIcon = AI_CUES[cueIndex].icon;

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/95 backdrop-blur-2xl px-4 select-none ${className}`}
    >
      {/* Background ambient glow effect */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[500px] rounded-full bg-brand/15 blur-[120px] animate-pulse" />
      <div className="pointer-events-none absolute -bottom-40 left-1/2 -translate-x-1/2 h-[450px] w-[450px] rounded-full bg-primary/10 blur-[130px]" />

      <div className="relative z-10 flex w-full max-w-md flex-col items-center text-center">
        {/* Animated AI Core / Neural Shield */}
        <div className="relative mb-8 flex items-center justify-center">
          {/* Outer Pulsing Rings */}
          <motion.div
            animate={{ rotate: 360, scale: [1, 1.06, 1] }}
            transition={{ rotate: { duration: 10, repeat: Infinity, ease: "linear" }, scale: { duration: 3, repeat: Infinity, ease: "easeInOut" } }}
            className="absolute h-32 w-32 rounded-full border border-dashed border-brand/40"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
            className="absolute h-40 w-40 rounded-full border border-dotted border-primary/30"
          />

          {/* Glowing Orb */}
          <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-tr from-brand/20 via-primary/20 to-purple-500/20 p-0.5 shadow-glow shadow-brand/30 border border-brand/40 backdrop-blur-md">
            <div className="flex h-full w-full items-center justify-center rounded-[22px] bg-background/90">
              <AnimatePresence mode="wait">
                <motion.div
                  key={cueIndex}
                  initial={{ opacity: 0, scale: 0.6, rotate: -15 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  exit={{ opacity: 0, scale: 0.6, rotate: 15 }}
                  transition={{ duration: 0.3 }}
                >
                  <CurrentIcon className="h-10 w-10 text-brand drop-shadow-[0_0_12px_rgba(59,130,246,0.6)]" />
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          {/* Floating Sparkle Dots */}
          <motion.span
            animate={{ y: [-4, 4, -4], opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute -top-2 right-2 h-2.5 w-2.5 rounded-full bg-brand shadow-[0_0_8px_#3b82f6]"
          />
          <motion.span
            animate={{ y: [4, -4, 4], opacity: [0.3, 0.9, 0.3] }}
            transition={{ duration: 2.5, repeat: Infinity }}
            className="absolute -bottom-1 left-2 h-2 w-2 rounded-full bg-purple-400 shadow-[0_0_8px_#a855f7]"
          />
        </div>

        {/* Header Title & Subtitle */}
        <h2 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
          {title}
        </h2>
        <p className="mt-1.5 text-xs text-muted-foreground max-w-sm">
          {subtitle}
        </p>

        {/* Dynamic AI Queue Card */}
        <div className="mt-6 w-full rounded-2xl border border-border/70 bg-card/60 p-4 backdrop-blur-xl shadow-soft">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand border border-brand/20">
              <Sparkles className="h-4 w-4 animate-spin" style={{ animationDuration: "3s" }} />
            </div>
            <div className="min-w-0 flex-1 text-left">
              <AnimatePresence mode="wait">
                <motion.div
                  key={cueIndex}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.25 }}
                >
                  <p className="text-xs font-semibold text-foreground truncate">
                    {AI_CUES[cueIndex].title}
                  </p>
                  <p className="text-[11px] text-muted-foreground truncate">
                    {AI_CUES[cueIndex].detail}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          {/* Neural Progress Bar */}
          <div className="mt-3.5">
            <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-1">
              <span className="flex items-center gap-1 text-brand">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-brand animate-ping" />
                AI Inference Running
              </span>
              <span>{progress}%</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/60">
              <motion.div
                className="h-full bg-gradient-to-r from-brand via-primary to-purple-500 rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ ease: "easeOut", duration: 0.3 }}
              />
            </div>
          </div>
        </div>

        {/* Security / AI Tip Footer */}
        <div className="mt-6 flex items-center justify-center gap-2 text-center">
          <AnimatePresence mode="wait">
            <motion.p
              key={tipIndex}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="text-[11px] text-muted-foreground/80 italic max-w-xs"
            >
              💡 {SECURITY_TIPS[tipIndex]}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
