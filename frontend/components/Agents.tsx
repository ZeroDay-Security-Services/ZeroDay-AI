const agents = [
  {
    icon: '◉',
    color: 'from-cyan/15 to-cyan/5 border-cyan/30',
    iconColor: 'text-cyan border-cyan/30 bg-cyan/10',
    glow: 'hover:shadow-[0_16px_48px_rgba(0,232,255,0.12)] hover:border-cyan/50',
    name: 'Vulnerability Analyst',
    tagline: 'CVE Risk & Remediation',
    desc: 'Performs live CVE lookups, CVSS/EPSS scoring, and contextual risk analysis for your specific asset configuration.',
    bullets: ['NVD / EPSS integration', 'CISA KEV cross-reference', 'Contextual risk scoring', 'Patch priority guidance'],
  },
  {
    icon: '⬡',
    color: 'from-blue/15 to-blue/5 border-blue/30',
    iconColor: 'text-blue border-blue/30 bg-blue/10',
    glow: 'hover:shadow-[0_16px_48px_rgba(45,107,255,0.12)] hover:border-blue/50',
    name: 'Threat Intelligence',
    tagline: 'IOC & Actor Tracking',
    desc: 'Correlates indicators of compromise against live ThreatFox feeds, maps TTPs to MITRE ATT&CK, and profiles threat actors.',
    bullets: ['ThreatFox IOC lookup', 'Malware family detection', 'MITRE TTP mapping', 'Threat actor profiling'],
  },
  {
    icon: '◈',
    color: 'from-purple-500/15 to-purple-500/5 border-purple-500/30',
    iconColor: 'text-purple-400 border-purple-500/30 bg-purple-500/10',
    glow: 'hover:shadow-[0_16px_48px_rgba(168,85,247,0.12)] hover:border-purple-500/50',
    name: 'Pentesting Assistant',
    tagline: 'Recon & Enumeration',
    desc: 'Guides penetration testers through methodology, scope prioritization, and generates structured engagement reports.',
    bullets: ['Recon methodology', 'Enumeration guidance', 'Scope prioritization', 'Report generation'],
  },
  {
    icon: '⬟',
    color: 'from-amber-400/15 to-amber-400/5 border-amber-400/30',
    iconColor: 'text-amber-400 border-amber-400/30 bg-amber-400/10',
    glow: 'hover:shadow-[0_16px_48px_rgba(251,191,36,0.12)] hover:border-amber-400/50',
    name: 'SOC Analyst',
    tagline: 'Alert Triage & Incident Response',
    desc: 'Triages security alerts, assigns P1–P4 severity, correlates events across log streams, and drives incident response.',
    bullets: ['P1–P4 severity assignment', 'Alert correlation', 'Log stream analysis', 'Incident escalation'],
  },
  {
    icon: '⬠',
    color: 'from-green/15 to-green/5 border-green/30',
    iconColor: 'text-green border-green/30 bg-green/10',
    glow: 'hover:shadow-[0_16px_48px_rgba(32,227,162,0.12)] hover:border-green/50',
    name: 'Security Automation',
    tagline: 'Workflows & Detection Rules',
    desc: 'Executes approved security workflows, generates SIEM detection rules, and builds remediation scripts on demand.',
    bullets: ['Workflow orchestration', 'Detection rule authoring', 'Script generation', 'Compliance scanning'],
  },
];

export default function Agents() {
  return (
    <section id="agents" className="px-8 py-24">
      <div className="mx-auto mb-16 max-w-[640px] text-center">
        <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
          Automation
        </span>
        <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
          5 Specialist AI Agents
        </h2>
        <p className="text-[15.5px] leading-relaxed text-steel">
          Each agent specializes in one discipline with tailored system prompts and tool subsets —
          reporting through a shared reasoning engine.
        </p>
      </div>

      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {agents.slice(0, 3).map((a) => (
          <AgentCard key={a.name} agent={a} />
        ))}
      </div>
      <div className="mx-auto mt-5 grid max-w-[1200px] grid-cols-1 gap-5 sm:grid-cols-2">
        {agents.slice(3).map((a) => (
          <AgentCard key={a.name} agent={a} />
        ))}
      </div>
    </section>
  );
}

function AgentCard({ agent: a }: { agent: (typeof agents)[0] }) {
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-6 transition-all duration-300 hover:-translate-y-1.5 ${a.color} ${a.glow}`}
    >
      {/* Top accent */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-current to-transparent opacity-30" />

      <div className="mb-5 flex items-start gap-4">
        <div
          className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl border text-[20px] ${a.iconColor}`}
        >
          {a.icon}
        </div>
        <div>
          <div className="mb-0.5 flex items-center gap-2">
            <span className="w-dot w-dot-ok" style={{ width: 5, height: 5 }} />
            <span className="font-mono text-[9px] uppercase tracking-wider text-green">Active</span>
          </div>
          <h3 className="font-display text-[16px] font-semibold text-text">{a.name}</h3>
          <p className={`font-mono text-[10.5px] tracking-wide ${a.iconColor}`}>{a.tagline}</p>
        </div>
      </div>

      <p className="mb-5 text-[13px] leading-relaxed text-steel">{a.desc}</p>

      <ul className="space-y-1.5">
        {a.bullets.map((b) => (
          <li key={b} className="flex items-center gap-2 text-[12.5px] text-steel">
            <span className={`text-[10px] ${a.iconColor}`}>▶</span>
            {b}
          </li>
        ))}
      </ul>
    </div>
  );
}
