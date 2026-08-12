import Nav from '@/components/Nav';
import ParticleBackground from '@/components/ParticleBackground';
import Hero from '@/components/Hero';
import Capabilities from '@/components/Capabilities';
import Intelligence from '@/components/Intelligence';
import ThreatFeed from '@/components/ThreatFeed';
import Agents from '@/components/Agents';
import LiveDashboard from '@/components/LiveDashboard';
import TechStack from '@/components/TechStack';
import About from '@/components/About';
import Footer from '@/components/Footer';

/**
 * Landing page — single-page scrollable marketing/product overview.
 * The AI Assistant console lives at /assistant (its own route).
 *
 * Section order matches the Nav links:
 *   Home → Threat Intelligence → Automation → Dashboard → Documentation → About
 */
export default function HomePage() {
  return (
    <>
      {/* Animated particle canvas rendered behind everything */}
      <ParticleBackground />

      {/* Subtle blue grid overlay (fixed, z-index 1) */}
      <div className="grid-overlay" />

      {/* CRT scanline effect (fixed, z-index 2) */}
      <div className="scanline" />

      {/* Main content stack (z-index 3) */}
      <div className="relative z-[3]">
        <Nav />

        {/* ── HERO ─────────────────────────────────────── */}
        <section id="home" className="scroll-mt-[72px]">
          <Hero />
        </section>

        {/* ── CORE AI CAPABILITIES ─────────────────────── */}
        <Capabilities />

        {/* ── THREAT INTELLIGENCE ──────────────────────── */}
        <Intelligence />

        {/* ── LIVE THREAT FEED (log stream) ────────────── */}
        <ThreatFeed />

        {/* ── AUTOMATION (5 specialist agents) ─────────── */}
        <Agents />

        {/* ── LIVE SYSTEM DASHBOARD ────────────────────── */}
        <LiveDashboard />

        {/* ── DOCUMENTATION / TECH STACK ───────────────── */}
        <TechStack />

        {/* ── ABOUT ─────────────────────────────────────── */}
        <About />

        <Footer />
      </div>
    </>
  );
}
