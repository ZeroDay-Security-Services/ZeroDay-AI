const columns = [
  {
    icon: '◈',
    color: 'text-cyan border-cyan/30 bg-cyan/5',
    title: 'Frontend',
    items: [
      { name: 'Next.js 14 / React 18', note: 'App Router + TypeScript' },
      { name: 'Tailwind CSS', note: 'Utility-first styling' },
      { name: 'Framer Motion', note: 'Animations & transitions' },
      { name: 'Three.js', note: '3D particle backgrounds' },
    ],
  },
  {
    icon: '⬟',
    color: 'text-blue border-blue/30 bg-blue/5',
    title: 'Backend',
    items: [
      { name: 'FastAPI (Python 3.12)', note: 'Async REST + WebSocket' },
      { name: 'SQLAlchemy (async)', note: 'SQLite / PostgreSQL' },
      { name: 'JWT Auth', note: 'Access + refresh tokens' },
      { name: 'pytest (51 tests)', note: 'Full offline test suite' },
    ],
  },
  {
    icon: '⬡',
    color: 'text-purple-400 border-purple-500/30 bg-purple-500/5',
    title: 'AI Core',
    items: [
      { name: 'Multi-Agent Framework', note: '5 specialist agents' },
      { name: 'Tool-calling orchestration', note: 'Real data, no hallucinations' },
      { name: 'Claude / GPT / Gemini', note: 'Swappable LLM backend' },
      { name: 'Groq / Ollama support', note: 'Local + cloud inference' },
    ],
  },
  {
    icon: '◉',
    color: 'text-amber-400 border-amber-400/30 bg-amber-400/5',
    title: 'Data Sources',
    items: [
      { name: 'NVD + EPSS', note: 'Live CVE & exploit scores' },
      { name: 'CISA KEV', note: 'Known exploited vulns' },
      { name: 'ThreatFox', note: 'abuse.ch IOC feed' },
      { name: 'Compliance engines', note: 'CERT-In, DPDP, Cloud' },
    ],
  },
];

export default function TechStack() {
  return (
    <section id="stack" className="scroll-mt-20 px-8 py-20">
      <div className="mx-auto mb-12 max-w-[640px] text-center">
        <span className="mb-3.5 block font-mono text-[11px] uppercase tracking-widest text-cyan">
          Documentation
        </span>
        <h2 className="mb-4 font-display text-[28px] font-bold tracking-tight text-text sm:text-[38px]">
          Built on a modular, swappable core
        </h2>
        <p className="text-[15.5px] leading-relaxed text-steel">
          Every layer is independently replaceable — swap LLMs, databases, or data sources without
          touching the rest.
        </p>
      </div>

      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {columns.map((col) => (
          <div
            key={col.title}
            className={`group rounded-2xl border bg-gradient-to-b p-5 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_12px_40px_rgba(0,0,0,0.3)] ${col.color}`}
          >
            {/* Column header */}
            <div className="mb-5 flex items-center gap-3">
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl border text-[16px] ${col.color}`}>
                {col.icon}
              </div>
              <h3 className={`font-mono text-[12px] uppercase tracking-widest font-bold ${col.color.split(' ')[0]}`}>
                {col.title}
              </h3>
            </div>

            <ul className="space-y-3">
              {col.items.map((item) => (
                <li
                  key={item.name}
                  className="border-b border-border/60 pb-3 last:border-0 last:pb-0"
                >
                  <div className="text-[13.5px] font-medium text-text">{item.name}</div>
                  <div className="mt-0.5 font-mono text-[11px] text-steelDim">{item.note}</div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
