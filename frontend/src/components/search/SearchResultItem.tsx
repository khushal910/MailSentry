import React from "react";
import { CornerDownLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { HighlightText } from "@/components/HighlightText";
import type { SearchResultItem as SearchResultItemType } from "@/types/search";

interface SearchResultItemProps {
  item: SearchResultItemType;
  isSelected: boolean;
  query: string;
  onSelect: () => void;
  onMouseEnter: () => void;
}

export const SearchResultItem = React.memo(function SearchResultItem({
  item,
  isSelected,
  query,
  onSelect,
  onMouseEnter,
}: SearchResultItemProps) {
  const Icon = item.icon;

  return (
    <div
      onClick={onSelect}
      onMouseEnter={onMouseEnter}
      className={cn(
        "group relative flex cursor-pointer items-center justify-between rounded-xl px-3.5 py-2.5 transition-all duration-150 select-none",
        isSelected
          ? "bg-brand/15 text-foreground shadow-soft border border-brand/40 font-medium"
          : "hover:bg-accent/40 text-muted-foreground hover:text-foreground",
      )}
    >
      <div className="flex items-center gap-3 min-w-0 flex-1 pr-3">
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border transition-colors",
            isSelected
              ? "bg-brand text-white border-brand shadow-sm"
              : "bg-muted/40 text-muted-foreground border-border/50 group-hover:text-foreground",
          )}
        >
          <Icon className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold truncate text-foreground">
              <HighlightText text={item.title} query={query} />
            </span>
            {item.badge && (
              <Badge
                variant="outline"
                className={cn(
                  "text-[10px] font-medium px-1.5 py-0 uppercase shrink-0",
                  item.badge.toLowerCase() === "spam"
                    ? "border-rose-500/30 bg-rose-500/10 text-rose-500"
                    : "border-brand/30 bg-brand/10 text-brand",
                )}
              >
                {item.badge}
              </Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            <HighlightText text={item.description} query={query} />
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {isSelected && (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-brand">
            <CornerDownLeft className="h-3 w-3" />
            Enter
          </span>
        )}
      </div>
    </div>
  );
});
