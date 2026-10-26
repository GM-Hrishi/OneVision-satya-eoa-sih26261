import "./portal.css";
import type { Metadata } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Approval Portal (Mock, for demo)",
  description: "Demo stand-in for an approval portal. Not an AICTE system. Synthetic data only.",
  robots: { index: false, follow: false },
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  await headers(); // dynamic rendering, so every page gets the per-request CSP nonce
  return (
    <html lang="en">
      <body>
        <a className="skip" href="#main">
          Skip to main content
        </a>
        <div className="banner" role="note">
          Demo stand-in. Not an AICTE system. Synthetic data only.
        </div>
        <header className="masthead">
          <p className="title">Approval Portal (Mock, for demo)</p>
          <p className="sub">Built by Team OneVision to demonstrate the proposed SATYA hooks. No real data.</p>
        </header>
        <main id="main">{children}</main>
        <footer className="foot">
          Mock portal for the SATYA-EoA prototype · synthetic data only · not affiliated with or connected to AICTE
        </footer>
      </body>
    </html>
  );
}
