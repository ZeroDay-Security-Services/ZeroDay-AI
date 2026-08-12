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
    <nav className="sticky top-0 z-50 flex items-center justify-between border-b border-border bg-bg/80 px-8 py-[18px] backdrop-blur-md">
      <a href="#home" className="flex items-center gap-3 no-underline">
        <Image
          src={logo}
          alt="ZeroDay Security Services logo"
          height={34}
          width={34}
          className="object-contain drop-shadow-[0_0_8px_rgba(0,232,255,0.35)]"
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

      <div className="hidden items-center gap-8 md:flex">
        {links.map((l) => (
          l.external ? (
            /* External page links use <a> with full navigation */
            <a
              key={l.href}
              href={l.href}
              className="group relative py-1 text-[13px] font-medium text-steel transition-colors hover:text-cyan"
            >
              {l.label}
              <span className="absolute -bottom-0.5 left-0 h-px bg-cyan transition-all duration-300 w-0 group-hover:w-full" />
            </a>
          ) : (
            /* Anchor links for same-page sections */
            <a
              key={l.href}
              href={l.href}
              className={`group relative py-1 text-[13px] font-medium transition-colors ${
                active === l.href.slice(1) ? 'text-cyan' : 'text-steel hover:text-text'
              }`}
            >
              {l.label}
              <span
                className={`absolute -bottom-0.5 left-0 h-px bg-cyan transition-all duration-300 ${
                  active === l.href.slice(1) ? 'w-full' : 'w-0 group-hover:w-full'
                }`}
              />
            </a>
          )
        ))}
      </div>

      <div className="flex items-center gap-2 rounded-full border border-border bg-green-500/5 px-3.5 py-1.5 font-mono text-[10.5px] tracking-wider text-green">
        <span className="status-dot" />
        SYSTEM ONLINE
      </div>
    </nav>
  );
}
