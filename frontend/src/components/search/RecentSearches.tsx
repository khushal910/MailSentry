import { Clock, Trash2, Search, Wand2, Mail, Settings, Sparkles, User, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RecentSearchesProps {
  searches: string[];
  onSelectSearch: (term: string) => void;
  onClear: () => void;
}

export function RecentSearches({ searches, onSelectSearch, onClear }: RecentSearchesProps) {
  const suggestions = [
    {
      label: "Search Subject",
      term: "Invoice",
      icon: Mail,
      subtitle: 'Find emails with subject "Invoice"',
    },
    { label: "Search Sender", term: "Amazon", icon: Search, subtitle: 'Find emails from "Amazon"' },
    { label: "Filter Spam", term: "Spam", icon: Wand2, subtitle: "Filter spam predicted emails" },
    {
      label: "Security & Passwords",
      term: "Password",
      icon: Shield,
      subtitle: "Change password or security",
    },
    {
      label: "User Settings",
      term: "Settings",
      icon: Settings,
      subtitle: "Appearance & dark mode",
    },
    { label: "User Profile", term: "Profile", icon: User, subtitle: "Account info & avatar" },
  ];

  return (
    <div className="p-4 space-y-5">
      {searches.length > 0 && (
        <div>
          <div className="flex items-center justify-between px-2 pb-2">
            <span className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              <Clock className="h-3.5 w-3.5 text-brand" />
              Recent Searches
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClear}
              className="h-6 px-2 text-[11px] text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="mr-1 h-3 w-3" />
              Clear
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 px-1">
            {searches.map((s) => (
              <button
                key={s}
                onClick={() => onSelectSearch(s)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border/60 bg-background/60 px-3 py-1.5 text-xs font-medium text-foreground hover:bg-brand/15 hover:border-brand/40 hover:text-brand transition-all shadow-sm"
              >
                <Search className="h-3 w-3 text-muted-foreground" />
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center gap-1.5 px-2 pb-2">
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
            Search Suggestions
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 px-1">
          {suggestions.map((item) => (
            <button
              key={item.label}
              onClick={() => onSelectSearch(item.term)}
              className="group flex items-center gap-3 rounded-2xl border border-border/50 bg-card/60 p-3 text-left transition-all hover:bg-brand/10 hover:border-brand/40 hover:shadow-sm"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand group-hover:bg-brand group-hover:text-white transition-colors">
                <item.icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-foreground group-hover:text-brand transition-colors">
                  {item.label}
                </p>
                <p className="text-[11px] text-muted-foreground truncate">{item.subtitle}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
