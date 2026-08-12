import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ZeroDay Security AI — Advanced AI Cybersecurity Intelligence Platform',
  description:
    'AI cybersecurity intelligence platform for vulnerability analysis, threat intelligence, and security automation, powered by ZeroDay Security Services.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font -- App Router root layout is the documented location for a shared font link, unlike the legacy pages/_document.js this rule targets */}
        <link
          href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      {/* Synchronously disable scroll restoration so the page always opens at the top */}
        <script dangerouslySetInnerHTML={{ __html: "if(typeof window!=='undefined'){history.scrollRestoration='manual';window.scrollTo(0,0);}" }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
