import AICore from './AICore';

const badges = ['Real-Time Threat Detection', '24/7 Autonomous Monitoring', 'Zero-Day Protection'];

export default function Hero() {
  return (
    <div className="relative overflow-hidden">
      {/* Ambient glow blobs behind the hero content */}
      <div
        className="glow-blob left-[6%] top-[6%] h-[380px] w-[380px] bg-blue/25"
        aria-hidden="true"
      />
      <div
        className="glow-blob right-[4%] top-[2%] h-[420px] w-[420px] bg-cyan/20"
        aria-hidden="true"
      />

      <div className="relative z-[1] mx-auto grid max-w-[1200px] grid-cols-1 items-center gap-14 px-6 pb-16 pt-20 sm:px-8 sm:pt-28 md:grid-cols-[1.05fr_0.95fr]">
        <div>
          <span className="rise-in mb-6 inline-flex items-center gap-2 rounded-full border border-cyan/25 bg-cyan/5 px-3.5 py-1.5 font-mono text-[11px] uppercase tracking-widest text-cyan">
            <span className="status-dot" /> Powered by ZeroDay Security Services
          </span>

          <h1
            className="rise-in mb-5 font-display text-[38px] font-bold leading-[1.06] tracking-tight text-text sm:text-[52px] lg:text-[62px]"
            style={{ animationDelay: '0.08s' }}
          >
            Defend Your Stack
            <br />
            Against{' '}
            <span className="bg-gradient-to-r from-blue via-cyan to-cyan bg-clip-text text-transparent">
              Every Threat
            </span>
          </h1>

          <p
            className="rise-in mb-8 max-w-[480px] text-[16.5px] leading-relaxed text-steel"
            style={{ animationDelay: '0.16s' }}
          >
            Advanced AI cybersecurity intelligence for vulnerability analysis, threat
            intelligence, and security automation — built to think like an analyst and act like
            an operator.
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

        <div className="relative">
          <div className="glow-blob left-1/2 top-1/2 h-[320px] w-[320px] -translate-x-1/2 -translate-y-1/2 bg-blue/20" />
          <div className="glass-panel relative rounded-[28px] p-6 shadow-glow sm:p-9">
            <AICore />
          </div>
        </div>
      </div>

      {/* Floating feature pills — mirrors a product screenshot's callouts */}
      <div className="relative z-[1] mx-auto mt-4 flex max-w-[1100px] flex-wrap items-center justify-center gap-4 px-6 pb-24 sm:gap-6 sm:px-8">
        {badges.map((b) => (
          <span
            key={b}
            className="tilt-pill glass-panel rounded-2xl px-5 py-3 font-mono text-[11px] uppercase tracking-widest text-steel shadow-[0_18px_40px_-16px_rgba(0,0,0,0.55)] transition-all duration-300"
          >
            <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-green shadow-[0_0_8px_var(--green)]" />
            {b}
          </span>
        ))}
      </div>
    </div>
  );
}
