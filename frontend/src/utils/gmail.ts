/**
 * Reusable utility helper for generating and interacting with Gmail web permalinks.
 */

/**
 * Generates a direct web permalink to open an email or thread in Gmail.
 *
 * @param messageId - The unique Gmail message ID or RFC822 message ID.
 * @param threadId - Optional Gmail thread ID for opening the conversation thread.
 * @returns Full Gmail URL string, or null if the message identifier is missing/invalid.
 */
export function getGmailUrl(
  messageId?: string | null,
  threadId?: string | null
): string | null {
  const cleanMsgId = messageId?.trim();
  const cleanThreadId = threadId?.trim();

  if (!cleanMsgId && !cleanThreadId) {
    return null;
  }

  // Thread view permalink
  if (cleanThreadId) {
    return `https://mail.google.com/mail/u/0/#all/${encodeURIComponent(cleanThreadId)}`;
  }

  if (cleanMsgId) {
    // Hex Gmail Message ID format (e.g. 18d4f09a12c8b)
    if (/^[0-9a-fA-F]{16,}$/.test(cleanMsgId)) {
      return `https://mail.google.com/mail/u/0/#all/${encodeURIComponent(cleanMsgId)}`;
    }
    // Search query permalink fallback for RFC822 Message-ID headers
    return `https://mail.google.com/mail/u/0/#search/rfc822msgid%3A${encodeURIComponent(cleanMsgId)}`;
  }

  return null;
}

/**
 * Safely opens a Gmail URL in a new browser tab without navigating away from MailSentry.
 *
 * @param url - The target Gmail URL string.
 * @returns boolean indicating whether the window.open succeeded.
 */
export function openGmailInNewTab(url: string | null): boolean {
  if (!url) return false;
  if (typeof window === "undefined") return false;

  window.open(url, "_blank", "noopener,noreferrer");
  return true;
}
