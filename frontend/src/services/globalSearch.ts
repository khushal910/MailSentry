import {
  LayoutDashboard,
  Wand2,
  MailSearch,
  History,
  UserCircle,
  Settings as SettingsIcon,
  LogOut,
  Sun,
  Moon,
  Shield,
  Bell,
  Mail,
  BarChart3,
  CheckCircle2,
  Sparkles,
  Search,
} from "lucide-react";
import type { SearchResultItem, SearchGroup } from "@/types/search";
import { emailsApi } from "@/services/emailsApi";

export interface GlobalSearchContext {
  navigate: (opts: { to: string }) => void;
  logout: () => Promise<void>;
  toggleTheme: () => void;
  theme: "light" | "dark";
}

/**
 * Returns real-time search suggestions based on the user's current query input.
 */
export function getRealtimeSuggestions(query: string): string[] {
  const q = query.toLowerCase().trim();
  const dictionary = [
    "Invoice",
    "Amazon",
    "Spam",
    "Safe Emails",
    "Settings",
    "Password",
    "Theme Mode",
    "Auto Classifier",
    "Prediction History",
    "Email Classifier",
    "User Profile",
    "Notifications",
    "Threat Statistics",
    "Security",
  ];

  if (!q) {
    return ["Invoice", "Amazon", "Spam", "Password", "Settings"];
  }

  const matches = dictionary.filter(
    (item) => item.toLowerCase().includes(q) && item.toLowerCase() !== q,
  );

  if (matches.length > 0) {
    return matches.slice(0, 5);
  }

  return [
    `Search "${query}" in Emails`,
    `Search "${query}" in Settings`,
    `Search "${query}" in History`,
  ];
}

/**
 * Global Search Service — Modular architecture supporting keyword, category & future AI search.
 */
export async function executeGlobalSearch(
  query: string,
  ctx: GlobalSearchContext,
): Promise<SearchGroup[]> {
  const q = query.toLowerCase().trim();
  const results: SearchResultItem[] = [];

  // 1. Suggestions Category (Always top priority)
  if (q) {
    const matchingSuggestions = getRealtimeSuggestions(q);
    matchingSuggestions.forEach((sugg, i) => {
      const clean = sugg.startsWith('Search "')
        ? sugg.replace(/^Search "(.*)" in .*$/, "$1")
        : sugg;

      results.push({
        id: `sugg-${i}-${clean}`,
        title: `Search for "${clean}"`,
        description: `Filter emails, subjects & settings for "${clean}"`,
        category: "Suggestions",
        icon: Sparkles,
        badge: "SUGGESTION",
        action: () => ctx.navigate({ to: "/dashboard/history" }),
        score: 200 - i * 10,
      });
    });
  }

  // 2. Quick Actions & Keywords
  const quickActions: SearchResultItem[] = [
    {
      id: "qa-auto-classifier",
      title: "Open Auto Classifier",
      description: "Queue of unclassified incoming emails waiting to be processed",
      category: "Quick Actions",
      icon: MailSearch,
      action: () => ctx.navigate({ to: "/dashboard/auto-classifier" }),
      score: getScore("open auto classifier refresh gmail queue unclassified new", q, 100),
    },
    {
      id: "qa-history",
      title: "View Prediction History",
      description: "Search and filter all classified emails in MongoDB",
      category: "Quick Actions",
      icon: History,
      action: () => ctx.navigate({ to: "/dashboard/history" }),
      score: getScore("view prediction history emails classified stored", q, 90),
    },
    {
      id: "qa-classifier",
      title: "Open Email Classifier",
      description: "Run instant ML prediction on single subject and body text",
      category: "Quick Actions",
      icon: Wand2,
      action: () => ctx.navigate({ to: "/dashboard/classifier" }),
      score: getScore("open email classifier single test predict ml", q, 85),
    },
    {
      id: "qa-settings",
      title: "Open Settings",
      description: "Manage appearance, dark mode, notifications & security",
      category: "Quick Actions",
      icon: SettingsIcon,
      action: () => ctx.navigate({ to: "/dashboard/settings" }),
      score: getScore("open settings password theme notifications dark mode", q, 80),
    },
    {
      id: "qa-profile",
      title: "Open Profile",
      description: "View account details and personal preferences",
      category: "Quick Actions",
      icon: UserCircle,
      action: () => ctx.navigate({ to: "/dashboard/profile" }),
      score: getScore("open profile account user details edit", q, 75),
    },
    {
      id: "qa-theme",
      title: `Toggle ${ctx.theme === "dark" ? "Light" : "Dark"} Mode`,
      description: "Switch application theme mode",
      category: "Quick Actions",
      icon: ctx.theme === "dark" ? Sun : Moon,
      action: () => ctx.toggleTheme(),
      score: getScore("toggle theme dark mode light mode appearance", q, 70),
    },
    {
      id: "qa-logout",
      title: "Logout",
      description: "Sign out of your MailSentry account",
      category: "Quick Actions",
      icon: LogOut,
      action: async () => {
        await ctx.logout();
        ctx.navigate({ to: "/login" });
      },
      score: getScore("logout sign out exit log off", q, 65),
    },
  ];

  results.push(...quickActions.filter((item) => (item.score || 0) > 0));

  // 3. Navigation items
  const navItems: SearchResultItem[] = [
    {
      id: "nav-dashboard",
      title: "Dashboard Overview",
      description: "Main metrics, threat count, live aggregation statistics",
      category: "Navigation",
      icon: LayoutDashboard,
      action: () => ctx.navigate({ to: "/dashboard" }),
      score: getScore("dashboard main overview stats analytics", q, 90),
    },
    {
      id: "nav-auto-classifier",
      title: "Auto Classifier Queue",
      description: "Process new incoming Gmail messages",
      category: "Navigation",
      icon: MailSearch,
      action: () => ctx.navigate({ to: "/dashboard/auto-classifier" }),
      score: getScore("auto classifier queue unclassified gmail new", q, 85),
    },
    {
      id: "nav-history",
      title: "Prediction History",
      description: "All saved email predictions & classifications",
      category: "Navigation",
      icon: History,
      action: () => ctx.navigate({ to: "/dashboard/history" }),
      score: getScore("prediction history classified emails search filter", q, 85),
    },
    {
      id: "nav-classifier",
      title: "Email Classifier",
      description: "Manual prediction tool for text content",
      category: "Navigation",
      icon: Wand2,
      action: () => ctx.navigate({ to: "/dashboard/classifier" }),
      score: getScore("email classifier manual predict ml score", q, 80),
    },
    {
      id: "nav-profile",
      title: "User Profile",
      description: "Account settings & information",
      category: "Navigation",
      icon: UserCircle,
      action: () => ctx.navigate({ to: "/dashboard/profile" }),
      score: getScore("user profile account information avatar", q, 75),
    },
    {
      id: "nav-settings",
      title: "Settings & Security",
      description: "Application preferences and password change",
      category: "Navigation",
      icon: SettingsIcon,
      action: () => ctx.navigate({ to: "/dashboard/settings" }),
      score: getScore("settings security password theme notifications", q, 75),
    },
  ];

  results.push(...navItems.filter((item) => (item.score || 0) > 0));

  // 4. Settings & Security sub-actions
  const settingsSubItems: SearchResultItem[] = [
    {
      id: "set-password",
      title: "Change Password",
      description: "Update current password under Settings > Security",
      category: "Settings",
      icon: Shield,
      action: () => ctx.navigate({ to: "/dashboard/settings" }),
      score: getScore("change update password security current new confirm", q, 95),
    },
    {
      id: "set-appearance",
      title: "Appearance & Theme",
      description: "Switch between Light and Dark mode",
      category: "Settings",
      icon: Sun,
      action: () => ctx.navigate({ to: "/dashboard/settings" }),
      score: getScore("appearance theme dark mode light mode colors", q, 90),
    },
    {
      id: "set-notif",
      title: "Email & Push Notifications",
      description: "Configure suspicious activity alerts",
      category: "Settings",
      icon: Bell,
      action: () => ctx.navigate({ to: "/dashboard/settings" }),
      score: getScore("notifications email alerts push notifications security", q, 85),
    },
  ];

  results.push(...settingsSubItems.filter((item) => (item.score || 0) > 0));

  // 5. Dashboard Stats sub-items
  const dashboardItems: SearchResultItem[] = [
    {
      id: "dash-spam-stats",
      title: "Spam Threat Statistics",
      description: "View total detected spam emails and spam percentage",
      category: "Dashboard",
      icon: BarChart3,
      action: () => ctx.navigate({ to: "/dashboard" }),
      score: getScore("spam threat statistics percentage total spam detected", q, 90),
    },
    {
      id: "dash-safe-stats",
      title: "Safe Emails & Inbox Health",
      description: "View legitimate email count and protection metrics",
      category: "Dashboard",
      icon: CheckCircle2,
      action: () => ctx.navigate({ to: "/dashboard" }),
      score: getScore("safe emails inbox ham legitimate health percentage", q, 90),
    },
  ];

  results.push(...dashboardItems.filter((item) => (item.score || 0) > 0));

  // 6. Backend Search for Classified Emails (MongoDB)
  if (q) {
    try {
      const emailRes = await emailsApi.getEmails({
        search: q,
        limit: 6,
      });
      if (emailRes.emails && emailRes.emails.length > 0) {
        emailRes.emails.forEach((email) => {
          const subject = email.subject || "(no subject)";
          const snippet = email.snippet || "";
          const label = email.predicted_label || "inbox";

          let score = 110;
          if (subject.toLowerCase() === q)
            score = 150; // Exact subject match
          else if (subject.toLowerCase().includes(q))
            score = 130; // Partial subject match
          else if ((email.sender || "").toLowerCase().includes(q)) score = 120;

          results.push({
            id: `email-${email.message_id}`,
            title: subject,
            description: snippet || `Prediction: ${label}`,
            category: "Emails",
            icon: Mail,
            badge: label.toUpperCase(),
            action: () => ctx.navigate({ to: "/dashboard/history" }),
            score: score,
            snippet: snippet,
          });
        });
      }
    } catch (err) {
      console.error("Global search API error:", err);
    }
  }

  // Sort by score descending
  results.sort((a, b) => (b.score || 0) - (a.score || 0));

  // Group by Category preserving priority order
  const categoryOrder: SearchGroup["category"][] = [
    "Suggestions",
    "Emails",
    "Auto Classifier",
    "Dashboard",
    "Predictions",
    "Settings",
    "Profile",
    "Quick Actions",
    "Navigation",
  ];

  const groupedMap = new Map<SearchGroup["category"], SearchResultItem[]>();
  results.forEach((item) => {
    if (!groupedMap.has(item.category)) {
      groupedMap.set(item.category, []);
    }
    groupedMap.get(item.category)!.push(item);
  });

  const grouped: SearchGroup[] = [];
  categoryOrder.forEach((cat) => {
    const items = groupedMap.get(cat);
    if (items && items.length > 0) {
      grouped.push({ category: cat, items });
    }
  });

  return grouped;
}

function getScore(text: string, query: string, baseScore: number): number {
  if (!query) return baseScore;
  const t = text.toLowerCase();
  if (t === query) return baseScore + 40;
  if (t.includes(query)) return baseScore + 20;

  // Partial word matching
  const words = query.split(" ");
  const matches = words.filter((w) => w.length > 0 && t.includes(w));
  if (matches.length > 0) {
    return baseScore + matches.length * 5;
  }
  return 0;
}
