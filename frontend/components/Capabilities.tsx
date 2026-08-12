const capabilities = [
  {
    icon: '⬡',
    color: 'from-cyan/20 to-cyan/5 border-cyan/30',
    iconColor: 'text-cyan',
    glow: 'hover:shadow-[0_12px_40px_rgba(180,140,255,0.12)] hover:border-cyan/40',
    title: 'CVE & Vulnerability Analysis',
    desc: 'Live CVSS/EPSS scores from NVD. Contextual risk scoring across criticality, exposure, and threat actor sophistication.',
    tags: ['NVD', 'EPSS', 'CISA KEV'],
  },
  {
    icon: '◈',
    color: 'from-blue/20 to-blue/5 border-blue/30',
    iconColor: 'text-blue',
    glow: 'hover:shadow-[0_12px_40px_rgba(109,91,255,0.12)] hover:border-blue/40',
    title: 'Threat Intelligence',
    desc: 'IOC correlation via ThreatFox, malware family tracking, MITRE ATT&CK TTP mapping, and threat actor profiling.',
    tags: ['ThreatFox', 'MITRE', 'IOC'],
  },
  {
    icon: '⬟',
    color: 'from-purple-500/20 to-purple-500/5 border-purple-500/30',
    iconColor: 'text-purple-400',
    glow: 'hover:shadow-[0_12px_40px_rgba(168,85,247,0.12)] hover:border-purple-500/40',
    title: 'Compliance Engines',
    desc: 'Real rule evaluation for Cloud posture, CERT-In 2022 Directions, and DPDP Act 2023 — not hardcoded pass/fail.',
    tags: ['CERT-In', 'DPDP', 'Cloud'],
  },
  {
    icon: '◉',
    color: 'from-amber-400/20 to-amber-400/5 border-amber-400/30',
    iconColor: 'text-amber-400',
    glow: 'hover:shadow-[0_12px_40px_rgba(251,191,36,0.12)] hover:border-amber-400/40',
    title: 'SOC & Incident Response',
    desc: 'Alert triage, P1–P4 severity classification, incident correlation, and threat hunting across log streams.',
    tags: ['Triage', 'P1–P4', 'Hunting'],
  },
  {
    icon: '⬠',
    color: 'from-green/20 to-green/5 border-green/30',
    iconColor: 'text-green',
    glow: 'hover:shadow-[0_12px_40px_rgba(32,227,162,0.12)] hover:border-green/40',
    title: 'Pentesting Assistance',
    desc: 'Recon methodology, enumeration guidance, scope prioritization, and structured report generation.',
    tags: ['Recon', 'Enum', 'Report'],
  },
  {
    icon: '⬡',
    color: 'from-red/20 to-red/5 border-red/30',
    iconColor: 'text-red',
    glow: 'hover:shadow-[0_12px_40px_rgba(255,58,85,0.12)] hover:border-red/40',
    title: 'Security Automation',
    desc: 'Executes approved workflows, generates detection rules and remediation scripts to eliminate repetitive analyst work.',
    tags: ['Workflows', 'Rules', 'Scripts'],
  },
];

export default function Capabilities() {
  return (
    <section id="capabilities" className="scroll-mt-[72px] px-8 pt-10 pb-20">
      <div className="mx-auto mb-12 max-w-[640px] text-center">
        <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
          AI Intelligence Modules
        </span>
        <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
          Core AI Capabilities
        </h2>
        <p className="text-[15.5px] leading-relaxed text-steel">
          ZeroDay Security AI is built to reason across the full security lifecycle — not a
          single-purpose chatbot.
        </p>
      </div>

      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {capabilities.map((c) => (
          <div
            key={c.title}
            className={`group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-6 transition-all duration-300 hover:-translate-y-1.5 ${c.color} ${c.glow}`}
          >
            {/* top accent line */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-current to-transparent opacity-40" />

            <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-xl border bg-[#04060c]/60 text-[20px] ${c.color} ${c.iconColor}`}>
              {c.icon}
            </div>

            <h3 className="mb-2.5 font-display text-[17px] font-semibold text-text">{c.title}</h3>
            <p className="mb-5 text-[13.5px] leading-relaxed text-steel">{c.desc}</p>

            <div className="flex flex-wrap gap-1.5">
              {c.tags.map((t) => (
                <span
                  key={t}
                  className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] tracking-wide ${c.color} ${c.iconColor}`}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
