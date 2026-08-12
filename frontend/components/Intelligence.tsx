const stats = [
  { value: '240,000+', label: 'CVEs Tracked' },
  { value: '47', label: 'Threat Actor Groups' },
  { value: '99.7%', label: 'Detection Rate' },
  { value: '< 2s', label: 'IOC Lookup Time' },
];

const frameworks = [
  {
    name: 'MITRE ATT&CK',
    icon: '⬡',
    color: 'text-cyan border-cyan/30 bg-cyan/5',
    desc: '14 tactics, 196 techniques mapped',
  },
  {
    name: 'OWASP Top 10',
    icon: '◈',
    color: 'text-blue border-blue/30 bg-blue/5',
    desc: 'Web application risk coverage',
  },
  {
    name: 'NIST CSF 2.0',
    icon: '⬟',
    color: 'text-purple-400 border-purple-500/30 bg-purple-500/5',
    desc: 'Govern, Identify, Protect, Detect, Respond, Recover',
  },
  {
    name: 'CVE / NVD',
    icon: '◉',
    color: 'text-amber-400 border-amber-400/30 bg-amber-400/5',
    desc: 'Live feed with EPSS & CISA KEV cross-ref',
  },
  {
    name: 'CWE Database',
    icon: '⬠',
    color: 'text-green border-green/30 bg-green/5',
    desc: '900+ weakness patterns indexed',
  },
  {
    name: 'ThreatFox IOC',
    icon: '◆',
    color: 'text-red border-red/30 bg-red/5',
    desc: 'abuse.ch botnet C2 & malware delivery feed',
  },
];

export default function Intelligence() {
  return (
    <section id="intelligence" className="px-8 py-24">
      {/* Header */}
      <div className="mx-auto mb-16 max-w-[640px] text-center">
        <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
          Threat Intelligence
        </span>
        <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
          Grounded in the frameworks analysts trust
        </h2>
        <p className="text-[15.5px] leading-relaxed text-steel">
          Knowledge retrieval is fused from the standards and databases that define the industry —
          not a static snapshot, but live-synced feeds.
        </p>
      </div>

      {/* Stats row */}
      <div className="mx-auto mb-14 grid max-w-[1200px] grid-cols-2 gap-4 sm:grid-cols-4">
        {stats.map((s) => (
          <div
            key={s.label}
            className="glass-panel rounded-2xl px-6 py-5 text-center transition-all duration-300 hover:-translate-y-1 hover:border-cyan/30 hover:shadow-[0_8px_28px_rgba(180,140,255,0.08)]"
          >
            <div className="mb-1 font-display text-[26px] font-bold text-cyan">{s.value}</div>
            <div className="font-mono text-[11px] uppercase tracking-wider text-steel">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Framework cards */}
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {frameworks.map((f) => (
          <div
            key={f.name}
            className={`group flex items-start gap-4 rounded-2xl border p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_10px_32px_rgba(0,0,0,0.3)] ${f.color}`}
          >
            <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl border text-[18px] ${f.color}`}>
              {f.icon}
            </div>
            <div>
              <h3 className="mb-1 font-display text-[15px] font-semibold text-text">{f.name}</h3>
              <p className="text-[12.5px] leading-relaxed text-steel">{f.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
