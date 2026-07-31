export const formatConfidence = (n: number) => {
  if (n <= 1) return `${(n * 100).toFixed(2)}%`;
  return `${n.toFixed(2)}%`;
};

export const formatDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
};

export const truncate = (s: string, n = 60) =>
  s.length > n ? `${s.slice(0, n - 1)}…` : s;
