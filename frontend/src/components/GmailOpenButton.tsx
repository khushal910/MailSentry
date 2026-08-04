import * as React from "react";
import { ExternalLink, Mail, MessageSquare, Reply, Forward, FileCode } from "lucide-react";
import { getGmailUrl, openGmailInNewTab } from "@/utils/gmail";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface GmailOpenButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Gmail message ID (e.g. 194be567a1b...) */
  messageId?: string | null;
  /** Optional Gmail thread ID */
  threadId?: string | null;
  /** Display variant: "icon" for subtle row actions, "button" for labeled button, "menu" for full dropdown */
  variant?: "icon" | "button" | "menu";
  /** Optional custom button label for "button" variant */
  label?: string;
  /** Size of the button */
  size?: "default" | "sm" | "lg" | "icon";
  /** Custom class names */
  className?: string;
  /** Optional callbacks for future extensible actions (Requirement #9) */
  onOpenThread?: () => void;
  onReply?: () => void;
  onForward?: () => void;
  onViewRaw?: () => void;
}

export const GmailOpenButton = React.forwardRef<HTMLButtonElement, GmailOpenButtonProps>(
  (
    {
      messageId,
      threadId,
      variant = "icon",
      label = "Open in Gmail",
      size = "sm",
      className = "",
      onClick,
      onOpenThread,
      onReply,
      onForward,
      onViewRaw,
      ...props
    },
    ref,
  ) => {
    const gmailUrl = getGmailUrl(messageId, threadId);
    const isAvailable = Boolean(gmailUrl);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      // CRITICAL: Prevent row click propagation if embedded inside a clickable table row
      e.stopPropagation();

      if (onClick) {
        onClick(e);
      }

      if (isAvailable && gmailUrl) {
        openGmailInNewTab(gmailUrl);
      }
    };

    // Tooltip text per requirements
    const tooltipText = isAvailable ? "Open Original Email in Gmail" : "Original email unavailable";

    // Standard accessible aria label
    const ariaLabel = isAvailable
      ? "Open original email in Gmail (opens in new tab)"
      : "Original email unavailable";

    // ── Dropdown Menu Variant (Future-Proof Requirement #9) ──
    if (variant === "menu") {
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              ref={ref}
              variant="outline"
              size={size}
              className={`gap-2 font-medium text-xs shadow-xs ${className}`}
              onClick={(e) => e.stopPropagation()}
              aria-label="Gmail actions menu"
              {...props}
            >
              <Mail className="h-3.5 w-3.5 text-brand" />
              <span>Gmail Actions</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48 text-xs">
            <DropdownMenuItem
              disabled={!isAvailable}
              onClick={(e) => {
                e.stopPropagation();
                if (gmailUrl) openGmailInNewTab(gmailUrl);
              }}
              className="cursor-pointer font-medium"
            >
              <ExternalLink className="mr-2 h-3.5 w-3.5 text-brand" />
              <span>Open Original Email</span>
            </DropdownMenuItem>

            {(onOpenThread || threadId) && (
              <DropdownMenuItem
                disabled={!threadId}
                onClick={(e) => {
                  e.stopPropagation();
                  if (onOpenThread) onOpenThread();
                  else if (threadId) openGmailInNewTab(getGmailUrl(undefined, threadId));
                }}
                className="cursor-pointer"
              >
                <MessageSquare className="mr-2 h-3.5 w-3.5 text-muted-foreground" />
                <span>Open Thread</span>
              </DropdownMenuItem>
            )}

            {onReply && (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onReply();
                }}
                className="cursor-pointer"
              >
                <Reply className="mr-2 h-3.5 w-3.5 text-muted-foreground" />
                <span>Reply in Gmail</span>
              </DropdownMenuItem>
            )}

            {onForward && (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onForward();
                }}
                className="cursor-pointer"
              >
                <Forward className="mr-2 h-3.5 w-3.5 text-muted-foreground" />
                <span>Forward</span>
              </DropdownMenuItem>
            )}

            {onViewRaw && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewRaw();
                  }}
                  className="cursor-pointer text-muted-foreground"
                >
                  <FileCode className="mr-2 h-3.5 w-3.5" />
                  <span>View Raw Metadata</span>
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    }

    // ── Button with Label Variant ──
    if (variant === "button") {
      return (
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-block" tabIndex={0}>
                <Button
                  ref={ref}
                  variant="outline"
                  size={size}
                  disabled={!isAvailable}
                  onClick={handleClick}
                  aria-label={ariaLabel}
                  className={`gap-1.5 font-medium text-xs transition-all duration-150 shadow-2xs ${
                    isAvailable
                      ? "hover:border-brand/50 hover:bg-brand/5 hover:text-brand cursor-pointer"
                      : "opacity-50 cursor-not-allowed"
                  } ${className}`}
                  {...props}
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>{label}</span>
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs font-semibold">
              {tooltipText}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    // ── Default Icon Variant (Subtle Linear/Superhuman Style) ──
    return (
      <TooltipProvider delayDuration={200}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-block" tabIndex={0}>
              <Button
                ref={ref}
                variant="ghost"
                size="icon"
                disabled={!isAvailable}
                onClick={handleClick}
                aria-label={ariaLabel}
                className={`h-8 w-8 rounded-lg transition-all duration-150 focus-visible:ring-2 focus-visible:ring-brand ${
                  isAvailable
                    ? "text-muted-foreground hover:text-brand hover:bg-brand/10 cursor-pointer active:scale-95"
                    : "opacity-40 cursor-not-allowed hover:bg-transparent"
                } ${className}`}
                {...props}
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs font-semibold">
            {tooltipText}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  },
);

GmailOpenButton.displayName = "GmailOpenButton";
