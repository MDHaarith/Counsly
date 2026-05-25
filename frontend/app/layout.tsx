import React from "react";
import Script from "next/script";
import { AppProvider } from "./AppContext";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>Counsly 2027 — TNEA Counseling Workspace</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="Algorithmic TNEA counseling workspace grounded in official guidance, cutoff evidence, and deterministic compare flows." />
      </head>
      <body>
        <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" />
        <AppProvider>
          <AppShell>{children}</AppShell>
        </AppProvider>
      </body>
    </html>
  );
}
