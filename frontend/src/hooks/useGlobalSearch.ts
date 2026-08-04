import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useDebounce } from "@/hooks/useDebounce";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import type { SearchGroup, SearchResultItem } from "@/types/search";
import { executeGlobalSearch, getRealtimeSuggestions } from "@/services/globalSearch";

const RECENT_SEARCHES_KEY = "mailsentry_recent_searches";
const MAX_RECENT_SEARCHES = 10;

export function useGlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  const [groups, setGroups] = useState<SearchGroup[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) return parsed.slice(0, MAX_RECENT_SEARCHES);
        }
      } catch {
        // Fallback to defaults
      }
    }
    return ["Invoice", "Amazon", "Spam", "Settings", "Password"];
  });

  const navigate = useNavigate();
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  // Compute real-time suggestions based on current query
  const suggestions = useMemo(() => {
    return getRealtimeSuggestions(query);
  }, [query]);

  // Save recent searches to localStorage
  const saveRecentSearches = useCallback((searches: string[]) => {
    setRecentSearches(searches);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(searches));
      } catch {
        // ignore error
      }
    }
  }, []);

  const addRecentSearch = useCallback((term: string) => {
    const clean = term.trim();
    if (!clean) return;
    setRecentSearches((prev) => {
      const filtered = prev.filter((s) => s.toLowerCase() !== clean.toLowerCase());
      const updated = [clean, ...filtered].slice(0, MAX_RECENT_SEARCHES);
      if (typeof window !== "undefined") {
        try {
          localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
        } catch {
          // ignore
        }
      }
      return updated;
    });
  }, []);

  const clearRecentSearches = useCallback(() => {
    saveRecentSearches([]);
  }, [saveRecentSearches]);

  const openSearch = useCallback(() => {
    setIsOpen(true);
    setSelectedIndex(0);
  }, []);

  const closeSearch = useCallback(() => {
    setIsOpen(false);
    setQuery("");
    setGroups([]);
    setSelectedIndex(0);
  }, []);

  const toggleSearch = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  // Compute flat list for keyboard selection indexing
  const flatItems = useMemo(() => {
    const items: SearchResultItem[] = [];
    groups.forEach((g) => {
      items.push(...g.items);
    });
    return items;
  }, [groups]);

  // Execute Search
  useEffect(() => {
    let isMounted = true;

    if (!debouncedQuery.trim()) {
      queueMicrotask(() => {
        if (isMounted) {
          setGroups([]);
          setIsLoading(false);
          setSelectedIndex(0);
        }
      });
      return () => {
        isMounted = false;
      };
    }

    queueMicrotask(() => {
      if (!isMounted) return;
      setIsLoading(true);

      void executeGlobalSearch(debouncedQuery, {
        navigate,
        logout,
        theme,
        toggleTheme,
      })
        .then((resGroups) => {
          if (isMounted) {
            setGroups(resGroups);
            setSelectedIndex(0);
          }
        })
        .catch((err) => {
          console.error("Global search error:", err);
        })
        .finally(() => {
          if (isMounted) setIsLoading(false);
        });
    });

    return () => {
      isMounted = false;
    };
  }, [debouncedQuery, navigate, logout, theme, toggleTheme]);

  // Global Keyboard listener: Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Modal Keyboard Navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        closeSearch();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (flatItems.length === 0) return;
        setSelectedIndex((prev) => (prev + 1) % flatItems.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (flatItems.length === 0) return;
        setSelectedIndex((prev) => (prev - 1 + flatItems.length) % flatItems.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (flatItems.length > 0 && flatItems[selectedIndex]) {
          const selected = flatItems[selectedIndex];
          if (query.trim()) addRecentSearch(query);
          closeSearch();
          selected.action();
        }
      }
    },
    [isOpen, flatItems, selectedIndex, query, addRecentSearch, closeSearch],
  );

  const selectAndExecute = useCallback(
    (item: SearchResultItem) => {
      if (query.trim()) addRecentSearch(query);
      closeSearch();
      item.action();
    },
    [query, addRecentSearch, closeSearch],
  );

  return {
    isOpen,
    openSearch,
    closeSearch,
    toggleSearch,
    query,
    setQuery,
    suggestions,
    groups,
    flatItems,
    isLoading,
    selectedIndex,
    setSelectedIndex,
    recentSearches,
    addRecentSearch,
    clearRecentSearches,
    handleKeyDown,
    selectAndExecute,
  };
}
