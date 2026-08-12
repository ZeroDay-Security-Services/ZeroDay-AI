const pillars = [
  {
    icon: '◈',
    title: 'Security Research & Development',
    desc: 'ZeroDay Security AI is the flagship platform — a multi-agent system for CVE and vulnerability analysis, threat intelligence correlation, compliance evaluation, and SOC automation, built on live data feeds rather than static rule sets.',
  },
  {
    icon: '⬡',
    title: 'Practical Security Education',
    desc: 'Alongside product work, ZeroDay Security Services publishes hands-on cybersecurity content and designs CTF challenges — turning offensive and defensive security concepts into material people can actually learn from.',
  },
  {
    icon: '⬟',
    title: 'Community & Competition',
    desc: 'Active within the Siliguri cybersecurity community, including CTF challenge design for local hackathons — contributing infrastructure and challenge sets that push participants beyond textbook exercises.',
  },
];

export default function About() {
  return (
    <section id="about" className="scroll-mt-[72px] px-8 pt-10 pb-20">
      <div className="mx-auto max-w-[1200px]">
        <div className="mx-auto mb-12 max-w-[720px] text-center">
          <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
            About ZeroDay Security Services
          </h2>
          <p className="mb-3 text-[15.5px] leading-relaxed text-steel">
            ZeroDay Security Services is a founder-led cybersecurity research and development
            practice, building AI-driven tooling for vulnerability analysis, threat intelligence,
            and security automation — grounded in the frameworks, feeds, and workflows that
            working analysts actually rely on, rather than dashboards built for a demo.
          </p>
          <p className="text-[15.5px] leading-relaxed text-steel">
            The work spans three tracks: shipping real security platforms, publishing security
            research and educational content, and designing hands-on challenges for the wider
            security community — all reflecting the same standard applied to this platform.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {pillars.map((p) => (
            <div
              key={p.title}
              className="glass-panel rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-cyan/30 bg-cyan/5 text-[18px] text-cyan">
                {p.icon}
              </div>
              <h3 className="mb-2 font-display text-[15px] font-semibold text-text">{p.title}</h3>
              <p className="text-[13px] leading-relaxed text-steel">{p.desc}</p>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-10 max-w-[720px] text-center font-mono text-[12px] leading-relaxed text-steelDim">
          Founded and operated by <span className="text-steel">Vijay Ishan Chowdhury</span>,
          a cybersecurity researcher and developer based in Siliguri, West Bengal, India.
        </div>
      </div>
    </section>
  );
}
