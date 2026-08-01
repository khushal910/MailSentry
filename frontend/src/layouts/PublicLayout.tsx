import type { ReactNode } from "react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { CursorGlow } from "@/components/CursorGlow";

export function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-col bg-background text-foreground overflow-x-clip transition-colors duration-300">
      <CursorGlow />
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
