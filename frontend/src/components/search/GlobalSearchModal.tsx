import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Search, X, Loader2, SearchX, Command, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import { SearchResultItem } from "./SearchResultItem";
import { RecentSearches } from "./RecentSearches";
import type { useGlobalSearch } from "@/hooks/useGlobalSearch";

type GlobalSearchHook = ReturnType<typeof useGlobalSearch>;

export function GlobalSearchModal({
  isOpen,
  closeSearch,
  query,
  setQuery,
  suggestions,
  groups,
  flatItems,
  isLoading,
  selectedIndex,
  setSelectedIndex,
  recentSearches,
  clearRecentSearches,
  handleKeyDown,
  selectAndExecute,
}: GlobalSearchHook) {
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  let cumulativeIndex = 0;

  const modalContent = (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-[9999] flex items-start justify-center bg-black/75 backdrop-blur-md p-4 pt-12 md:pt-20 overflow-y-auto"
        onClick={(e) => {
          if (e.target === e.currentTarget) closeSearch();
        }}
        onKeyDown={handleKeyDown}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: -12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -12 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="relative w-full max-w-[700px] overflow-hidden rounded-3xl border border-border/70 bg-card/95 shadow-2xl backdrop-blur-2xl transition-colors duration-300"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Top Search Input Bar */}
          <div className="relative flex items-center border-b border-border/60 px-4 py-3.5">
            <Search className="h-5 w-5 shrink-0 text-muted-foreground mr-3" />
            <Input
              ref={inputRef}
              id="global-command-search-input"
              type="text"
              placeholder="Type a command or search emails, settings, actions…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-9 w-full border-0 bg-transparent text-sm md:text-base font-medium focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground/70"
              autoComplete="off"
            />
            {isLoading && (
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-brand mr-2" />
            )}
            {query && (
              <button
                onClick={() => setQuery("")}
                className="mr-2 rounded-lg p-1 text-muted-foreground hover:bg-accent/40 hover:text-foreground"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <kbd className="hidden sm:inline-flex items-center gap-1 rounded-md border border-border/60 bg-muted/40 px-2 py-0.5 text-[10px] font-semibold text-muted-foreground">
              ESC
            </kbd>
          </div>

          {/* Real-Time Search Suggestions Bar */}
          {suggestions && suggestions.length > 0 && (
            <div className="flex items-center gap-2 border-b border-border/40 bg-muted/20 px-4 py-2 text-xs overflow-x-auto scrollbar-none">
              <span className="flex items-center gap-1 font-semibold text-muted-foreground shrink-0 text-[10px] uppercase tracking-wider">
                <Sparkles className="h-3 w-3 text-brand" /> Suggestions:
              </span>
              <div className="flex items-center gap-1.5 shrink-0">
                {suggestions.map((s) => {
                  const cleanTerm = s.startsWith('Search "')
                    ? s.replace(/^Search "(.*)" in .*$/, "$1")
                    : s;
                  return (
                    <button
                      key={s}
                      onClick={() => setQuery(cleanTerm)}
                      className="rounded-lg border border-border/50 bg-background/60 px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-brand/15 hover:border-brand/40 hover:text-brand transition-all"
                    >
                      {s}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Body Content */}
          <div className="max-h-[60vh] overflow-y-auto p-2">
            {!query.trim() ? (
              <RecentSearches
                searches={recentSearches}
                onSelectSearch={(term) => setQuery(term)}
                onClear={clearRecentSearches}
              />
            ) : isLoading && groups.length === 0 ? (
              <div className="flex items-center justify-center gap-2 py-14 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin text-brand" />
                Searching emails and commands…
              </div>
            ) : groups.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 py-14 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted/40 text-muted-foreground">
                  <SearchX className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">No results found</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    No items match "<span className="font-medium text-foreground">{query}</span>"
                  </p>
                </div>
                <div className="mt-3 flex flex-wrap justify-center gap-1.5 text-xs text-muted-foreground">
                  <span className="font-medium">Suggestions:</span>
                  <button onClick={() => setQuery("Invoice")} className="text-brand hover:underline">
                    Subject
                  </button>
                  <span>·</span>
                  <button onClick={() => setQuery("Amazon")} className="text-brand hover:underline">
                    Sender
                  </button>
                  <span>·</span>
                  <button onClick={() => setQuery("Spam")} className="text-brand hover:underline">
                    Spam
                  </button>
                  <span>·</span>
                  <button onClick={() => setQuery("Settings")} className="text-brand hover:underline">
                    Settings
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4 py-2">
                {groups.map((group) => {
                  const groupStartIndex = cumulativeIndex;
                  cumulativeIndex += group.items.length;

                  return (
                    <div key={group.category} className="space-y-1">
                      <div className="px-3 text-[11px] font-bold uppercase tracking-wider text-muted-foreground/80">
                        {group.category}
                      </div>
                      {group.items.map((item, idx) => {
                        const globalIndex = groupStartIndex + idx;
                        const isSelected = globalIndex === selectedIndex;

                        return (
                          <SearchResultItem
                            key={item.id}
                            item={item}
                            isSelected={isSelected}
                            query={query}
                            onSelect={() => selectAndExecute(item)}
                            onMouseEnter={() => setSelectedIndex(globalIndex)}
                          />
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer Bar */}
          <div className="flex items-center justify-between border-t border-border/60 bg-muted/30 px-4 py-2.5 text-xs text-muted-foreground">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border/60 bg-background px-1.5 py-0.5 text-[10px]">↑</kbd>
                <kbd className="rounded border border-border/60 bg-background px-1.5 py-0.5 text-[10px]">↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border/60 bg-background px-1.5 py-0.5 text-[10px]">↵</kbd>
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border/60 bg-background px-1.5 py-0.5 text-[10px]">ESC</kbd>
                Close
              </span>
            </div>
            <div className="flex items-center gap-1 font-medium text-foreground text-[11px]">
              <Command className="h-3 w-3 text-brand" /> MailSentry Command Palette
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );

  return typeof document !== "undefined"
    ? createPortal(modalContent, document.body)
    : null;
}
