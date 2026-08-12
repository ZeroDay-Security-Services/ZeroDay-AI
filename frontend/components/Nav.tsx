'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import logo from '@/public/logo.png';

const links = [
  { href: '#home', label: 'Home', external: false },
  { href: '/assistant', label: 'AI Assistant', external: true },
  { href: '#intelligence', label: 'Threat Intelligence', external: false },
  { href: '#agents', label: 'Automation', external: false },
  { href: '#dashboard', label: 'Dashboard', external: false },
  { href: '#stack', label: 'Documentation', external: false },
  { href: '#about', label: 'About', external: false },
];

export default function Nav() {
  const [active, setActive] = useState('');

  useEffect(() => {
    // Scroll to top on initial load to prevent browser scroll restoration mid-page
    if (typeof window !== 'undefined' && window.history.scrollRestoration) {
      window.history.scrollRestoration = 'manual';
    }
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    const ids = links.map((l) => l.href.slice(1));
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: '-20% 0px -70% 0px' },
    );
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <nav className="sticky top-0 z-50 flex h-[72px] items-center justify-between border-b border-border/70 bg-bg/75 px-6 backdrop-blur-xl sm:px-8">
      <a href="#home" className="flex items-center gap-3 no-underline">
        <Image
          src={logo}
          alt="ZeroDay Security Services logo"
          height={34}
          width={34}
          className="object-contain drop-shadow-[0_0_8px_rgba(180,140,255,0.35)]"
        />
        <div className="flex flex-col leading-tight">
          <span className="font-display text-[15px] font-bold tracking-wider text-text">
            ZERODAY SECURITY AI
          </span>
          <span className="mt-0.5 font-mono text-[9.5px] tracking-widest text-steel">
            ZERODAY SECURITY SERVICES
          </span>
        </div>
      </a>

      <div className="hidden items-center gap-1 rounded-full border border-border/70 bg-white/[0.02] p-1 md:flex">
        {links.map((l) => (
          l.external ? (
            /* External page links use <a> with full navigation */
            <a
              key={l.href}
              href={l.href}
              className="rounded-full px-3.5 py-1.5 text-[13px] font-medium text-steel transition-colors hover:bg-white/[0.04] hover:text-text"
            >
              {l.label}
            </a>
          ) : (
            /* Anchor links for same-page sections */
            <a
              key={l.href}
              href={l.href}
              className={`rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors ${
                active === l.href.slice(1)
                  ? 'bg-cyan/10 text-cyan'
                  : 'text-steel hover:bg-white/[0.04] hover:text-text'
              }`}
            >
              {l.label}
            </a>
          )
        ))}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-full border border-border bg-green-500/5 px-3.5 py-1.5 font-mono text-[10.5px] tracking-wider text-green sm:flex">
          <span className="status-dot" />
          SYSTEM ONLINE
        </div>
        <a href="/assistant" className="btn btn-primary !px-4 !py-2 !text-[12.5px]">
          Launch AI →
        </a>
      </div>
    </nav>
  );
}
