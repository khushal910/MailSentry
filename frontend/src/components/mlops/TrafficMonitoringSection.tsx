import { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { Button } from "@/components/ui/button";

const mockTimeSeriesData = {
  "1h": Array.from({ length: 12 }, (_, i) => ({
    time: `${i * 5}m`,
    requests: Math.floor(35 + Math.random() * 20),
    latency: Number((1.5 + Math.random() * 0.6).toFixed(2)),
    errorRate: Number((Math.random() * 0.05).toFixed(2)),
    cpu: Math.floor(12 + Math.random() * 8),
    memory: Math.floor(235 + Math.random() * 15),
  })),
  "24h": Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    requests: Math.floor(30 + Math.random() * 30),
    latency: Number((1.4 + Math.random() * 0.8).toFixed(2)),
    errorRate: Number((Math.random() * 0.08).toFixed(2)),
    cpu: Math.floor(10 + Math.random() * 12),
    memory: Math.floor(230 + Math.random() * 25),
  })),
  "7d": Array.from({ length: 7 }, (_, i) => ({
    time: `Day ${i + 1}`,
    requests: Math.floor(400 + Math.random() * 250),
    latency: Number((1.6 + Math.random() * 0.5).toFixed(2)),
    errorRate: Number((Math.random() * 0.04).toFixed(2)),
    cpu: Math.floor(14 + Math.random() * 6),
    memory: Math.floor(240 + Math.random() * 20),
  })),
  "30d": Array.from({ length: 15 }, (_, i) => ({
    time: `Day ${i * 2 + 1}`,
    requests: Math.floor(800 + Math.random() * 400),
    latency: Number((1.5 + Math.random() * 0.7).toFixed(2)),
    errorRate: Number((Math.random() * 0.06).toFixed(2)),
    cpu: Math.floor(15 + Math.random() * 8),
    memory: Math.floor(245 + Math.random() * 30),
  })),
};

export function TrafficMonitoringSection() {
  const [timeFilter, setTimeFilter] = useState<"1h" | "24h" | "7d" | "30d">("24h");
  const data = mockTimeSeriesData[timeFilter];

  return (
    <div className="space-y-4 rounded-xl border border-border/80 bg-card p-6 shadow-xs">
      {/* Header & Filter Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-foreground">Traffic & Infrastructure Telemetry</h2>
          <p className="text-xs sm:text-sm text-muted-foreground font-medium mt-0.5">
            Real-time inference requests, latencies, CPU/Memory telemetry, and HTTP error rates.
          </p>
        </div>

        {/* Time Filters */}
        <div className="flex items-center gap-1.5 bg-muted/60 p-1.5 rounded-lg border border-border/60">
          {(["1h", "24h", "7d", "30d"] as const).map((filter) => (
            <Button
              key={filter}
              variant={timeFilter === filter ? "default" : "ghost"}
              size="sm"
              onClick={() => setTimeFilter(filter)}
              className={`h-8 px-3.5 text-xs sm:text-sm font-bold rounded-md ${
                timeFilter === filter
                  ? "bg-foreground text-background shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {filter.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      {/* 4 Technical Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
        {/* Chart 1: Prediction Requests */}
        <ChartCard title="Prediction Requests (req/s)">
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.4} />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", fontSize: "12px", fontWeight: "bold", borderRadius: "8px" }} />
              <Area type="monotone" dataKey="requests" stroke="#10b981" fill="#10b98120" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 2: P95 Latency */}
        <ChartCard title="Latency P95 (ms)">
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.4} />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", fontSize: "12px", fontWeight: "bold", borderRadius: "8px" }} />
              <Area type="monotone" dataKey="latency" stroke="#3b82f6" fill="#3b82f620" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 3: Error Rate */}
        <ChartCard title="Error Rate (%)">
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.4} />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", fontSize: "12px", fontWeight: "bold", borderRadius: "8px" }} />
              <Area type="monotone" dataKey="errorRate" stroke="#f43f5e" fill="#f43f5e20" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 4: CPU & Memory */}
        <ChartCard title="CPU Usage (%)">
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.4} />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", fontSize: "12px", fontWeight: "bold", borderRadius: "8px" }} />
              <Area type="monotone" dataKey="cpu" stroke="#8b5cf6" fill="#8b5cf620" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-muted/20 p-3.5 space-y-2">
      <span className="block text-xs sm:text-sm font-bold text-foreground">{title}</span>
      {children}
    </div>
  );
}
