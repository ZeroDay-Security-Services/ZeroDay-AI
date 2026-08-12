'use client';

import { useEffect, useRef, useState } from 'react';

type LogTag = 'INFO' | 'WARN' | 'OK' | 'CRIT';

const LINES: { tag: LogTag; msg: string }[] = [
  { tag: 'INFO', msg: 'Agent[VulnAnalyst] baseline scan complete — 0 critical findings' },
  { tag: 'WARN', msg: 'CVE-2026-11342 published — Apache module, CVSS 7.4, monitoring' },
  { tag: 'OK', msg: 'Agent[SOC] alert #4471 triaged — false positive, closed' },
  { tag: 'CRIT', msg: 'IOC match: outbound beacon pattern flagged, isolating host' },
  { tag: 'INFO', msg: 'Threat intel sync — MITRE ATT&CK dataset refreshed' },
  { tag: 'OK', msg: 'Agent[Automation] nightly workflow executed successfully' },
  { tag: 'WARN', msg: 'Unusual auth pattern detected on edge gateway — reviewing' },
  { tag: 'INFO', msg: 'Agent[Pentest] recon module returned 3 open services' },
];

const TAG_COLOR: Record<LogTag, string> = {
  INFO: 'text-cyan',
  WARN: 'text-[#ffb020]',
  OK: 'text-green',
  CRIT: 'text-red',
};

/** Illustrative live-feed simulation. Phase 4+ wires this to the real
 * CVE/threat-intel pipeline instead of the local rotation below. */
export default function ThreatFeed() {
  const [rows, setRows] = useState<{ id: number; ts: string; tag: LogTag; msg: string }[]>([]);
  const counter = useRef(0);

  useEffect(() => {
    function push() {
      const line = LINES[counter.current % LINES.length]!;
      const ts = new Date().toTimeString().slice(0, 8);
      setRows((prev) => {
        const next = [...prev, { id: counter.current, ts, tag: line.tag, msg: line.msg }];
        return next.length > 7 ? next.slice(next.length - 7) : next;
      });
      counter.current += 1;
    }
    for (let i = 0; i < 6; i++) push();
    const interval = setInterval(push, 3200);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="detection" className="scroll-mt-20 px-8 py-20">
      <div className="mx-auto mb-14 max-w-[640px]">
        <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
          Live Threat Feed
        </span>
        <h2 className="mb-3.5 font-display text-[26px] font-bold tracking-tight text-text sm:text-[36px]">
          Live signal, structured for action
        </h2>
        <p className="max-w-[560px] text-[15.5px] leading-relaxed text-steel">
          A continuous feed of correlated events, formatted the way an operator wants to read them.
        </p>
      </div>

      <div className="mx-auto max-w-[1200px] overflow-hidden rounded-2xl border border-border bg-[#0c0e1e]">
        <div className="flex items-center gap-2 border-b border-border bg-white/[0.015] px-4.5 py-3">
          <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-2 font-mono text-[11px] tracking-wide text-steel">
            root@zeroday — threat-feed.log
          </span>
        </div>
        <div className="max-h-[280px] overflow-hidden px-5 py-5 font-mono text-[12.5px] leading-[2]">
          {rows.map((r) => (
            <div key={r.id} className="flex gap-3 text-steel/90">
              <span className="flex-shrink-0 text-steelDim">[{r.ts}]</span>
              <span className={`flex-shrink-0 font-semibold ${TAG_COLOR[r.tag]}`}>{r.tag}</span>
              <span>{r.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
