'use client';

import { useEffect, useRef, useState } from 'react';

type Widget = {
  label: string;
  value: string;
  state: 'ok' | 'info' | 'warn';
  icon: string;
  accent: string;
  glow: string;
};

const initialWidgets: Widget[] = [
  { label: 'AI Status', value: 'ONLINE', state: 'ok', icon: '⬡', accent: 'from-green/20 to-transparent border-green/20', glow: 'shadow-[0_0_20px_rgba(32,227,162,0.08)]' },
  { label: 'Threat Feed', value: 'Connected', state: 'ok', icon: '◈', accent: 'from-cyan/20 to-transparent border-cyan/20', glow: 'shadow-[0_0_20px_rgba(180,140,255,0.08)]' },
  { label: 'Security Intel', value: 'Active', state: 'ok', icon: '◉', accent: 'from-blue/20 to-transparent border-blue/20', glow: 'shadow-[0_0_20px_rgba(109,91,255,0.08)]' },
  { label: 'AI Agents', value: '8 Active', state: 'ok', icon: '⬟', accent: 'from-purple-500/20 to-transparent border-purple-500/20', glow: 'shadow-[0_0_20px_rgba(168,85,247,0.08)]' },
  { label: 'Memory', value: '14.2 GB', state: 'info', icon: '⬠', accent: 'from-amber-400/20 to-transparent border-amber-400/20', glow: 'shadow-[0_0_20px_rgba(251,191,36,0.08)]' },
  { label: 'Automation Jobs', value: 'Running', state: 'ok', icon: '◆', accent: 'from-green/20 to-transparent border-green/20', glow: 'shadow-[0_0_20px_rgba(32,227,162,0.08)]' },
  { label: 'Last Scan', value: '2 seconds ago', state: 'info', icon: '◇', accent: 'from-cyan/20 to-transparent border-cyan/20', glow: 'shadow-[0_0_20px_rgba(180,140,255,0.08)]' },
  { label: 'System Health', value: '99.98%', state: 'ok', icon: '△', accent: 'from-green/20 to-transparent border-green/20', glow: 'shadow-[0_0_20px_rgba(32,227,162,0.08)]' },
];

const AGENT_COUNTS = ['8 Active', '7 Active', '8 Active', '8 Active'];
const DOT_CLASS = { ok: 'w-dot-ok', info: 'w-dot-info', warn: 'w-dot-warn' };

export default function LiveDashboard() {
  const [widgets, setWidgets] = useState<Widget[]>(initialWidgets);
  const secondsAgo = useRef(2);

  useEffect(() => {
    const tick = setInterval(() => {
      secondsAgo.current = secondsAgo.current >= 12 ? 0 : secondsAgo.current + 1;
      const next = secondsAgo.current;
      setWidgets((w) =>
        w.map((widget) =>
          widget.label === 'Last Scan'
            ? { ...widget, value: next === 0 ? 'just now' : `${next} second${next === 1 ? '' : 's'} ago` }
            : widget,
        ),
      );
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    const memTick = setInterval(() => {
      const val = (14.2 + (Math.random() - 0.5) * 0.4).toFixed(1);
      setWidgets((w) => w.map((x) => (x.label === 'Memory' ? { ...x, value: `${val} GB` } : x)));
    }, 4200);
    const healthTick = setInterval(() => {
      const val = (99.98 + (Math.random() - 0.5) * 0.06).toFixed(2);
      setWidgets((w) => w.map((x) => (x.label === 'System Health' ? { ...x, value: `${val}%` } : x)));
    }, 5000);
    let ai = 0;
    const agentTick = setInterval(() => {
      ai = (ai + 1) % AGENT_COUNTS.length;
      setWidgets((w) => w.map((x) => (x.label === 'AI Agents' ? { ...x, value: AGENT_COUNTS[ai]! } : x)));
    }, 6000);
    return () => { clearInterval(memTick); clearInterval(healthTick); clearInterval(agentTick); };
  }, []);

  return (
    <section id="dashboard" className="scroll-mt-[72px] px-8 pt-10 pb-20">
      <div className="mx-auto max-w-[1200px]">
        <div className="mb-12 text-center">
          <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
            Live System Dashboard
          </span>
          <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
            Real-time operational status
          </h2>
          <p className="mx-auto max-w-[560px] text-[15.5px] leading-relaxed text-steel">
            A continuous read on platform health, intelligence sync, and active agents.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {widgets.map((w) => (
            <div
              key={w.label}
              className={`group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-5 transition-all duration-300 hover:-translate-y-1.5 ${w.accent} ${w.glow} hover:brightness-110`}
            >
              {/* Gradient accent bar at top */}
              <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-current to-transparent opacity-60" />

              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-dot ${DOT_CLASS[w.state]}`} />
                  <span className="font-mono text-[10px] uppercase tracking-wider text-steel">{w.label}</span>
                </div>
                <span className="font-mono text-[16px] text-steelDim opacity-50">{w.icon}</span>
              </div>

              <div className="font-display text-[22px] font-bold text-text transition-all duration-500">
                {w.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
