import { Clock, Trash2, Search, Wand2, Mail, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RecentSearchesProps {
  searches: string[];
  onSelectSearch: (term: string) => void;
  onClear: () => void;
}

export function RecentSearches({
  searches,
  onSelectSearch,
  onClear,
}: RecentSearchesProps) {
  const suggestions = [
    { label: "Search Subject", term: "Invoice", icon: Mail },
    { label: "Search Sender", term: "Amazon", icon: Search },
    { label: "Search Spam", term: "Spam", icon: Wand2 },
    { label: "Search Settings", term: "Password", icon: Settings },
  ];

  return (
    <div className="p-4 space-y-4">
      {searches.length > 0 && (
        <div>
          <div className="flex items-center justify-between px-2 pb-2">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
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
          <div className="flex flex-wrap gap-1.5 px-1">
            {searches.map((s) => (
              <button
                key={s}
                onClick={() => onSelectSearch(s)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border/50 bg-background/50 px-3 py-1.5 text-xs font-medium text-foreground hover:bg-brand/10 hover:border-brand/40 hover:text-brand transition-all"
              >
                <Search className="h-3 w-3 text-muted-foreground" />
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <span className="block px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Quick Suggestions
        </span>
        <div className="grid grid-cols-2 gap-2 px-1">
          {suggestions.map((item) => (
            <button
              key={item.label}
              onClick={() => onSelectSearch(item.term)}
              className="flex items-center gap-2.5 rounded-xl border border-border/40 bg-card/40 p-2.5 text-left text-xs font-medium transition-all hover:bg-brand/10 hover:border-brand/30 hover:text-brand"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand/10 text-brand">
                <item.icon className="h-3.5 w-3.5" />
              </div>
              <div>
                <p className="font-semibold text-foreground">{item.label}</p>
                <p className="text-[11px] text-muted-foreground">e.g. "{item.term}"</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
