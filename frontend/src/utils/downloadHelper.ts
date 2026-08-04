/**
 * Helper to trigger actual browser download of PKL artifact files with explicit file size metadata
 */
export function downloadPklFile(
  filename: string,
  contentDescription: string,
  sizeMb: number = 0.05
) {
  // Create realistic pickle binary payload header (Python 3 pickle protocol 4)
  const header = `\x80\x04\x95\x40\x00\x00\x00\x00\x00\x00\x00}\x94(\x8c\x0bmodel_type\x94\x8c\x12MailSentry_MLOps\x94\x8c\x07version\x94\x8c\x06v2.0.0\x94\x8c\x0bdescription\x94\x8c${contentDescription}\x94\x8c\x07size_mb\x94\x8c${sizeMb.toFixed(2)}MB\x94u.`;

  // Pad payload bytes to match requested file size
  const targetBytes = Math.max(header.length, Math.round(sizeMb * 1024 * 1024));
  const paddingLength = Math.max(0, targetBytes - header.length);
  const padding = "0".repeat(paddingLength);
  
  const blob = new Blob([header + padding], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".pkl") ? filename : `${filename}.pkl`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
