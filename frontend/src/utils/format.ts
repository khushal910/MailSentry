export const formatConfidence = (n: number) => {
  if (n <= 1) return `${(n * 100).toFixed(1)}%`;
  return `${n.toFixed(1)}%`;
};

export const formatNumber = (n: number | undefined | null): string => {
  if (n === undefined || n === null || isNaN(n)) return "0";
  return n.toLocaleString();
};

export const formatDate = (iso: string | Date | undefined | null) => {
  if (!iso) return "—";
  try {
    let str = typeof iso === "string" ? iso : iso.toISOString();
    // Normalize ISO strings without timezone offsets to UTC (ending with Z)
    if (
      typeof str === "string" &&
      !str.endsWith("Z") &&
      !str.includes("+") &&
      !/T\d{2}:\d{2}:\d{2}.*[-+]\d{2}/.test(str)
    ) {
      str = str + "Z";
    }
    return new Date(str).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return String(iso);
  }
};

export const truncate = (s: string, n = 60) =>
  s.length > n ? `${s.slice(0, n - 1)}…` : s;
