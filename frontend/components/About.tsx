const highlights = [
  {
    icon: '◈',
    title: 'Founder-Led Security R&D',
    desc: 'Built and maintained by a working cybersecurity researcher — not a generic vendor template.',
  },
  {
    icon: '⬡',
    title: 'Research, Not Just a Product',
    desc: 'ZeroDay Security Services spans hands-on development, applied research, CTF design, and security education.',
  },
  {
    icon: '⬟',
    title: 'Built for Analysts',
    desc: 'Every module is shaped by real SOC, pentest, and vulnerability-analysis workflows, not boilerplate dashboards.',
  },
];

export default function About() {
  return (
    <section id="about" className="scroll-mt-20 px-8 py-20">
      <div className="mx-auto max-w-[1200px]">
        <div className="mx-auto mb-12 max-w-[680px] text-center">
          <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
            About
          </span>
          <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
            About ZeroDay Security Services
          </h2>
          <p className="text-[15.5px] leading-relaxed text-steel">
            ZeroDay Security Services is a cybersecurity research and development practice
            building AI-driven tooling for vulnerability analysis, threat intelligence, and
            security automation — grounded in the frameworks and data sources analysts already
            trust, and shaped by real offensive and defensive security work rather than
            marketing copy.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {highlights.map((h) => (
            <div
              key={h.title}
              className="glass-panel rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-cyan/30 bg-cyan/5 text-[18px] text-cyan">
                {h.icon}
              </div>
              <h3 className="mb-2 font-display text-[15px] font-semibold text-text">{h.title}</h3>
              <p className="text-[13px] leading-relaxed text-steel">{h.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
