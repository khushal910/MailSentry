import { useState, useEffect, useCallback } from "react";
import {
  Mail,
  CheckCircle2,
  XCircle,
  RefreshCw,
  AlertTriangle,
  Unlink,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { googleAuthApi, type GoogleStatusResponse } from "@/services/googleAuthApi";

export function GmailStatusCard() {
  const [statusData, setStatusData] = useState<GoogleStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<boolean>(false);
  const [disconnecting, setDisconnecting] = useState<boolean>(false);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await googleAuthApi.getStatus();
      setStatusData(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load Gmail connection status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleConnect = async () => {
    setConnecting(true);
    setError(null);
    try {
      await googleAuthApi.initiateConnect();
    } catch (err: any) {
      const msg = err?.message || "Failed to connect to Google OAuth service. Please retry.";
      setError(msg);
      toast.error(msg);
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await googleAuthApi.disconnect();
      toast.success("Gmail account disconnected.");
      setStatusData({ connected: false });
    } catch (err: any) {
      toast.error(err?.message || "Failed to disconnect Gmail.");
    } finally {
      setDisconnecting(false);
    }
  };

  // Loading state — Show skeleton
  if (loading) {
    return (
      <div className="glass rounded-xl p-5 border border-border/60 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-56" />
          </div>
          <Skeleton className="h-6 w-24 rounded-full" />
        </div>
        <div className="pt-2 flex items-center justify-between">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-9 w-32 rounded-lg" />
        </div>
      </div>
    );
  }

  // API error state — Show error card with retry button
  if (error) {
    return (
      <div className="glass rounded-xl p-5 border border-destructive/40 bg-destructive/5 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-foreground text-sm">Gmail Connection Error</h3>
              <p className="text-xs text-muted-foreground mt-0.5">{error}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStatus}
            className="border-destructive/30 hover:bg-destructive/10 text-xs shrink-0"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const isConnected = statusData?.connected === true;

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "N/A";
    try {
      const d = new Date(dateStr);
      return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  // Connected state (connected = true)
  if (isConnected && statusData) {
    return (
      <div className="glass rounded-xl p-5 border border-emerald-500/20 bg-emerald-500/5 shadow-sm transition-all space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                <Mail className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-foreground">Gmail Connected</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground font-medium">Gmail Status:</span>
                  <Badge
                    variant="outline"
                    className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-xs font-semibold px-2.5 py-0.5"
                  >
                    <CheckCircle2 className="mr-1 h-3 w-3 inline" />
                    Connected
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5 pt-2 sm:pt-0">
            <Button
              onClick={handleConnect}
              disabled={connecting}
              size="sm"
              className="bg-gradient-brand shadow-elegant text-xs font-medium"
            >
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${connecting ? "animate-spin" : ""}`} />
              {connecting ? "Connecting…" : "Reconnect"}
            </Button>
            <Button
              onClick={handleDisconnect}
              disabled={disconnecting || connecting}
              variant="outline"
              size="sm"
              className="text-xs text-destructive border-destructive/30 hover:bg-destructive/10 hover:text-destructive"
            >
              <Unlink className="mr-1.5 h-3.5 w-3.5" />
              {disconnecting ? "Disconnecting…" : "Disconnect"}
            </Button>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-emerald-500/10 text-xs">
          <div>
            <span className="text-muted-foreground font-medium block">Connected Email:</span>
            <span className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold text-xs truncate block mt-0.5">
              {statusData.google_email}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground font-medium block">Connected Since:</span>
            <span className="text-foreground font-medium mt-0.5 block">
              {formatDate(statusData.connected_at)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground font-medium block">Last Updated:</span>
            <span className="text-foreground font-medium mt-0.5 block">
              {formatDate(statusData.last_updated)}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Not Connected state (connected = false)
  return (
    <div className="glass rounded-xl p-5 border border-border/80 shadow-sm transition-all">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Connect Gmail</h2>
              <p className="text-xs text-muted-foreground">Enable AI Email Classification.</p>
            </div>
          </div>

          <div className="pt-2 flex items-center gap-2 text-xs">
            <span className="text-muted-foreground font-medium">Status:</span>
            <Badge
              variant="outline"
              className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs font-semibold px-2.5 py-0.5"
            >
              <XCircle className="mr-1 h-3 w-3 inline" />
              Not Connected
            </Badge>
          </div>
        </div>

        <div className="pt-2 sm:pt-0">
          <Button
            onClick={handleConnect}
            disabled={connecting}
            size="sm"
            className="bg-gradient-brand shadow-elegant text-xs font-medium w-full sm:w-auto"
          >
            <ExternalLink className={`mr-1.5 h-3.5 w-3.5 ${connecting ? "animate-spin" : ""}`} />
            {connecting ? "Connecting…" : "Connect Gmail"}
          </Button>
        </div>
      </div>
    </div>
  );
}
