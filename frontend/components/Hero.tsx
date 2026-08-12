import AICore from './AICore';

export default function Hero() {
  return (
    <div className="mx-auto grid max-w-[1200px] grid-cols-1 items-center gap-10 px-8 pb-24 pt-24 md:grid-cols-[1.05fr_0.95fr]">
      <div>
        <span className="rise-in mb-6 inline-flex items-center gap-2 rounded-full border border-cyan/25 bg-cyan/5 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-cyan">
          ● Powered by ZeroDay Security Services
        </span>

        <h1
          className="rise-in mb-5 font-display text-[40px] font-bold leading-[1.02] tracking-tight text-text sm:text-[52px] lg:text-[64px]"
          style={{ animationDelay: '0.08s' }}
        >
          ZeroDay
          <br />
          <span className="bg-gradient-to-r from-cyan to-blue bg-clip-text text-transparent">
            Security AI
          </span>
        </h1>

        <p
          className="rise-in mb-8 max-w-[480px] text-[16.5px] leading-relaxed text-steel"
          style={{ animationDelay: '0.16s' }}
        >
          Advanced AI Cybersecurity Intelligence Platform for vulnerability analysis, threat
          intelligence, and security automation — built to think like an analyst and act like an
          operator.
        </p>

        <div className="rise-in flex flex-wrap gap-3.5" style={{ animationDelay: '0.24s' }}>
          <a href="/assistant" className="btn btn-primary">
            Launch AI Assistant →
          </a>
          <a href="#dashboard" className="btn btn-ghost">
            View Live Dashboard
          </a>
        </div>

        <div
          className="rise-in mt-7 font-mono text-[11.5px] tracking-wide text-steelDim"
          style={{ animationDelay: '0.32s' }}
        >
          Powered by <b className="text-steel">ZeroDay Security Services</b>
        </div>
      </div>

      <AICore />
    </div>
  );
}
