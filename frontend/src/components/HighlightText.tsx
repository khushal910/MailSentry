import React from "react";

interface HighlightTextProps {
  text?: string | null;
  query?: string;
  className?: string;
}

export function HighlightText({ text, query, className }: HighlightTextProps) {
  if (!text) return null;
  if (!query || !query.trim()) return <span className={className}>{text}</span>;

  const trimmedQuery = query.trim();
  const escapedQuery = trimmedQuery.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`(${escapedQuery})`, "gi");
  const parts = text.split(regex);

  return (
    <span className={className}>
      {parts.map((part, i) =>
        part.toLowerCase() === trimmedQuery.toLowerCase() ? (
          <mark key={i} className="bg-brand/20 text-brand font-semibold rounded px-0.5 py-0 mx-0">
            {part}
          </mark>
        ) : (
          part
        ),
      )}
    </span>
  );
}
