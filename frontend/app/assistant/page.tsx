'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import logo from '@/public/logo.png';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCallsMade?: number;
  agentName?: string;
  timestamp: Date;
};

type Agent = {
  id: string;
  name: string;
  description: string;
};

type AuthMode = 'login' | 'register';

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

/** Agent definitions — shown before the API responds (overridden by live data) */
const STATIC_AGENTS: Agent[] = [
  { id: 'master', name: 'ZeroDay AI', description: 'Unified intelligence: vulnerability analysis, web security, OSINT, threat intel, SOC, red team, compliance, reporting' },
  { id: 'vulnerability_analyst', name: 'Vulnerability Analyst', description: 'CVE risk scoring, EPSS, CISA KEV, contextual remediation timelines' },
  { id: 'threat_intelligence', name: 'Threat Intelligence', description: 'IOC correlation, threat actor tracking, MITRE ATT&CK TTPs' },
  { id: 'soc_analyst', name: 'SOC Analyst', description: 'Alert triage, P1-P4 severity, incident correlation and response' },
  { id: 'pentest_assistant', name: 'Pentest Assistant', description: 'Engagement methodology, scope planning, structured reporting' },
  { id: 'web_security_analyst', name: 'Web Security Analyst', description: 'OWASP Top 10, injection attacks, auth bypass, SSRF, GraphQL security' },
  { id: 'reconnaissance', name: 'Reconnaissance', description: 'OSINT, subdomain enumeration, JS bundle mining, cloud asset discovery' },
  { id: 'security_automation', name: 'Security Automation', description: 'Compliance scanning, detection rules, remediation workflow automation' },
];

/** Color scheme per agent */
const AGENT_COLORS: Record<string, { dot: string; bg: string; border: string; text: string }> = {
  master:               { dot: 'bg-cyan',        bg: 'bg-cyan/10',        border: 'border-cyan/40',        text: 'text-cyan'        },
  assistant:            { dot: 'bg-cyan',        bg: 'bg-cyan/10',        border: 'border-cyan/40',        text: 'text-cyan'        },
  vulnerability_analyst:{ dot: 'bg-red',         bg: 'bg-red/10',         border: 'border-red/40',         text: 'text-red'         },
  threat_intelligence:  { dot: 'bg-blue',        bg: 'bg-blue/10',        border: 'border-blue/40',        text: 'text-blue'        },
  soc_analyst:          { dot: 'bg-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-400/40',   text: 'text-amber-400'   },
  pentest_assistant:    { dot: 'bg-purple-400',  bg: 'bg-purple-400/10',  border: 'border-purple-400/40',  text: 'text-purple-400'  },
  web_security_analyst: { dot: 'bg-orange-400',  bg: 'bg-orange-400/10',  border: 'border-orange-400/40',  text: 'text-orange-400'  },
  reconnaissance:       { dot: 'bg-teal-400',    bg: 'bg-teal-400/10',    border: 'border-teal-400/40',    text: 'text-teal-400'    },
  security_automation:  { dot: 'bg-green',       bg: 'bg-green/10',       border: 'border-green/40',       text: 'text-green'       },
};
const DEFAULT_AGENT_COLOR = AGENT_COLORS.assistant!;

const AGENT_ICONS: Record<string, string> = {
  master:               '◈',
  assistant:            '◈',
  vulnerability_analyst:'◉',
  threat_intelligence:  '⬡',
  soc_analyst:          '⬟',
  pentest_assistant:    '⬠',
  web_security_analyst: '◍',
  reconnaissance:       '◎',
  security_automation:  '◆',
};

// ─────────────────────────────────────────────────────────────────────────────
// Auth helpers
// ─────────────────────────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('zd_access_token');
}

function saveToken(t: string): void {
  localStorage.setItem('zd_access_token', t);
}

function clearToken(): void {
  localStorage.removeItem('zd_access_token');
}

// ─────────────────────────────────────────────────────────────────────────────
// Auth Panel component
// ─────────────────────────────────────────────────────────────────────────────

function AuthPanel({ onAuth }: { onAuth: (token: string) => void }) {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);

    try {
      // Register first if in register mode
      if (mode === 'register') {
        const r = await fetch(`${BASE}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          // Backend UserCreate schema requires: email, full_name (min 1 char), password (min 8 chars)
          body: JSON.stringify({ email, full_name: fullName, password }),
        });
        if (!r.ok) {
          const d = await r.json().catch(() => ({}));
          throw new Error(d?.detail ?? d?.error?.message ?? `Registration failed (${r.status})`);
        }
      }

      // Login (always runs — auto-login after register)
      const r = await fetch(`${BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d?.detail ?? d?.error?.message ?? `Login failed (${r.status})`);
      }
      const d = await r.json();
      const token: string | undefined = d.access_token ?? d.token;
      if (!token) throw new Error('No token in server response');
      saveToken(token);
      onAuth(token);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <div className="w-full max-w-[400px]">
        {/* Icon */}
        <div className="mb-6 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan/30 bg-cyan/5 text-3xl text-cyan shadow-[0_0_32px_rgba(180,140,255,0.1)]">
            ◈
          </div>
        </div>

        {/* Heading */}
        <h2 className="mb-1 text-center font-display text-[22px] font-bold text-text">
          {mode === 'login' ? 'Sign in to ZeroDay AI' : 'Create your account'}
        </h2>
        <p className="mb-7 text-center font-mono text-[11.5px] text-steelDim">
          {mode === 'login'
            ? 'Authenticate to access the AI security console'
            : 'Free account — full access, no credit card needed'}
        </p>

        {/* Mode toggle */}
        <div className="mb-6 flex rounded-xl border border-border bg-[#04060c] p-1">
          {(['login', 'register'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => { setMode(m); setErr(null); }}
              className={`flex-1 rounded-lg py-2 font-mono text-[11px] uppercase tracking-wider transition-all ${
                mode === m
                  ? 'bg-cyan/10 text-cyan shadow-[inset_0_0_12px_rgba(180,140,255,0.05)]'
                  : 'text-steelDim hover:text-steel'
              }`}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-4">
          {/* Full name — only shown during registration */}
          {mode === 'register' && (
            <div>
              <label className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-wider text-steel">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                required
                minLength={1}
                className="w-full rounded-xl border border-border bg-[#04060c] px-4 py-3 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none focus:shadow-[0_0_0_3px_rgba(180,140,255,0.08)] transition-all"
              />
            </div>
          )}
          <div>
            <label className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-wider text-steel">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@zeroday.dev"
              required
              className="w-full rounded-xl border border-border bg-[#04060c] px-4 py-3 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none focus:shadow-[0_0_0_3px_rgba(180,140,255,0.08)] transition-all"
            />
          </div>
          <div>
            <label className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-wider text-steel">
              Password
              {mode === 'register' && (
                <span className="ml-2 text-steelDim normal-case">(min 8 characters)</span>
              )}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={mode === 'register' ? 8 : 1}
              className="w-full rounded-xl border border-border bg-[#04060c] px-4 py-3 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none focus:shadow-[0_0_0_3px_rgba(180,140,255,0.08)] transition-all"
            />
          </div>

          {/* Error message */}
          {err && (
            <div className="flex items-start gap-2 rounded-xl border border-red/25 bg-red/5 px-4 py-3">
              <span className="mt-0.5 text-[11px] text-red">⚠</span>
              <span className="font-mono text-[11.5px] text-red">{err}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="btn btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign In →' : 'Create Account →'}
          </button>
        </form>

        {/* Mode switcher link */}
        <p className="mt-5 text-center font-mono text-[11px] text-steelDim">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setErr(null); }}
            className="text-cyan hover:underline"
          >
            {mode === 'login' ? 'Register free' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Message bubble component
// ─────────────────────────────────────────────────────────────────────────────

function MessageBubble({ msg, agentColor }: { msg: Message; agentColor: typeof AGENT_COLORS[string] }) {
  const isUser = msg.role === 'user';
  const time = msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-2.5`}>
      {/* Assistant avatar */}
      {!isUser && (
        <div className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border text-[13px] mt-0.5 ${agentColor.bg} ${agentColor.border} ${agentColor.text}`}>
          {AGENT_ICONS[msg.agentName ?? 'assistant'] ?? '◈'}
        </div>
      )}

      <div className={`max-w-[78%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {/* Header row for assistant messages */}
        {!isUser && (
          <div className="flex items-center gap-2 px-1">
            <span className={`font-mono text-[9.5px] uppercase tracking-widest ${agentColor.text}`}>
              ZeroDay AI
            </span>
            {msg.toolCallsMade ? (
              <span className="font-mono text-[9px] text-green">
                {msg.toolCallsMade} tool{msg.toolCallsMade > 1 ? 's' : ''} used
              </span>
            ) : null}
            <span className="font-mono text-[9px] text-steelDim">{time}</span>
          </div>
        )}

        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-[13.5px] leading-relaxed ${
            isUser
              ? 'bg-blue/15 border border-blue/25 text-text rounded-tr-sm'
              : `border text-text rounded-tl-sm ${agentColor.bg} ${agentColor.border}`
          }`}
        >
          <pre className="whitespace-pre-wrap font-[inherit]">{msg.content}</pre>
        </div>

        {/* Timestamp for user messages */}
        {isUser && (
          <span className="px-1 font-mono text-[9px] text-steelDim">{time}</span>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main /assistant page
// ─────────────────────────────────────────────────────────────────────────────

export default function AssistantPage() {
  // ── Auth state ────────────────────────────────────────────
  const [token, setToken] = useState<string | null>(null);

  // ── Agent list (fetched from backend, falls back to static) ─
  const [agents, setAgents] = useState<Agent[]>(STATIC_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<string>('master');

  // ── Chat state ────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ── Restore token from localStorage on mount ──────────────
  useEffect(() => {
    setToken(getToken());
  }, []);

  // ── Fetch live agent list once authenticated ──────────────
  useEffect(() => {
    if (!token) return;
    fetch(`${BASE}/api/v1/agents/`)
      .then((r) => r.json())
      .then((d: { agents?: Agent[] }) => {
        if (Array.isArray(d.agents) && d.agents.length > 0) setAgents(d.agents);
      })
      .catch(() => { /* Keep static fallback */ });
  }, [token]);

  // ── Auto-scroll to latest message ────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Switch agent → clear conversation ────────────────────
  function selectAgent(id: string) {
    setSelectedAgent(id);
    setMessages([]);
    setConversationId(null);
    setError(null);
    // Re-focus input after switching
    setTimeout(() => textareaRef.current?.focus(), 50);
  }

  // ── Auth callbacks ────────────────────────────────────────
  function handleAuth(t: string) {
    setToken(t);
  }

  function logout() {
    clearToken();
    setToken(null);
    setMessages([]);
    setConversationId(null);
    setError(null);
  }

  // ── Send message ──────────────────────────────────────────
  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading || !token) return;

    setInput('');
    setError(null);

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      };

      let data: { reply?: string; conversation_id?: string; tool_calls_made?: number };

      if (selectedAgent === 'assistant') {
        // Legacy general assistant route — maintains conversation history
        const res = await fetch(`${BASE}/api/v1/assistant/chat`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ message: text, conversation_id: conversationId }),
        });
        if (res.status === 401) { clearToken(); setToken(null); throw new Error('Session expired — please sign in again'); }
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          throw new Error(e?.error?.message ?? e?.detail ?? `HTTP ${res.status}`);
        }
        data = await res.json();
        if (data.conversation_id) setConversationId(data.conversation_id);
      } else {
        // All named agents (master + specialists) — single-turn via agents/run
        const res = await fetch(`${BASE}/api/v1/agents/run`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ agent: selectedAgent, message: text }),
        });
        if (res.status === 401) { clearToken(); setToken(null); throw new Error('Session expired — please sign in again'); }
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          throw new Error(e?.error?.message ?? e?.detail ?? `HTTP ${res.status}`);
        }
        data = await res.json();
      }

      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: data.reply ?? '(no reply)',
        toolCallsMade: data.tool_calls_made,
        agentName: selectedAgent,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [input, loading, token, selectedAgent, conversationId]);

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const agentColor = AGENT_COLORS[selectedAgent] ?? DEFAULT_AGENT_COLOR;
  const currentAgent = selectedAgent === 'assistant'
    ? { id: 'assistant', name: 'General Assistant', description: 'Multi-domain AI security analyst' }
    : agents.find((a) => a.id === selectedAgent) ?? agents[0];

  // ─────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#04060c]">

      {/* ── TOP NAV BAR ──────────────────────────────────── */}
      <header className="flex flex-shrink-0 items-center justify-between border-b border-border bg-bg/80 px-6 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          {/* Back to landing page */}
          <Link
            href="/"
            className="mr-1 flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 font-mono text-[10.5px] text-steelDim transition-all hover:border-cyan/40 hover:text-cyan"
          >
            ← Home
          </Link>
          <Image src={logo} alt="ZeroDay Security AI" width={28} height={28} className="object-contain" />
          <div>
            <div className="font-display text-[13px] font-bold tracking-wider text-text">ZERODAY AI CONSOLE</div>
            <div className="font-mono text-[9px] tracking-widest text-steelDim">SECURITY INTELLIGENCE PLATFORM</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Active agent indicator */}
          {token && currentAgent && (
            <div className={`hidden items-center gap-2 rounded-full border px-3 py-1 font-mono text-[10px] tracking-wide sm:flex ${agentColor.bg} ${agentColor.border} ${agentColor.text}`}>
              <span className={`inline-block h-1.5 w-1.5 rounded-full ${agentColor.dot} animate-pulse`} />
              {currentAgent.name}
            </div>
          )}

          {/* System status */}
          <div className="flex items-center gap-2 rounded-full border border-border bg-green-500/5 px-3 py-1.5 font-mono text-[10.5px] tracking-wider text-green">
            <span className="status-dot" />
            ONLINE
          </div>

          {/* Sign out */}
          {token && (
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-border px-3 py-1.5 font-mono text-[10.5px] text-steelDim transition-all hover:border-red/40 hover:text-red"
            >
              Sign out
            </button>
          )}
        </div>
      </header>

      {/* ── BODY (sidebar + chat) ─────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── LEFT SIDEBAR — Agent selector ────────────────── */}
        <aside className="hidden w-[220px] flex-shrink-0 flex-col border-r border-border bg-[#060b16] md:flex">
          <div className="border-b border-border px-4 py-3">
            <span className="font-mono text-[9.5px] uppercase tracking-widest text-steelDim">Agents</span>
          </div>

          <nav className="flex-1 overflow-y-auto p-2 space-y-1">
            {/* General assistant option */}
            <AgentSidebarItem
              id="assistant"
              name="General Assistant"
              description="Multi-domain security analyst"
              selected={selectedAgent === 'assistant'}
              onSelect={selectAgent}
            />

            {/* Separator */}
            <div className="mx-2 my-2 border-t border-border" />
            <p className="px-3 py-1 font-mono text-[9px] uppercase tracking-widest text-steelDim">Specialists</p>

            {/* Specialist agents */}
            {agents.map((a) => (
              <AgentSidebarItem
                key={a.id}
                id={a.id}
                name={a.name}
                description={a.description}
                selected={selectedAgent === a.id}
                onSelect={selectAgent}
              />
            ))}
          </nav>

          {/* Sidebar footer — backend status */}
          <div className="border-t border-border p-4">
            <div className="font-mono text-[9.5px] text-steelDim">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-dot w-dot-ok" style={{ width: 5, height: 5 }} />
                Backend connected
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-dot w-dot-info" style={{ width: 5, height: 5 }} />
                Groq LLM active
              </div>
            </div>
          </div>
        </aside>

        {/* ── MAIN CHAT AREA ───────────────────────────────── */}
        <main className="flex flex-1 flex-col overflow-hidden">

          {/* Unauthenticated → show auth panel */}
          {!token ? (
            <AuthPanel onAuth={handleAuth} />
          ) : (
            <>
              {/* ── Chat header bar ───────────────────────── */}
              <div className={`flex flex-shrink-0 items-center gap-3 border-b px-5 py-3 ${agentColor.bg} ${agentColor.border} border-b`}>
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg border text-[15px] ${agentColor.bg} ${agentColor.border} ${agentColor.text}`}>
                  {AGENT_ICONS[selectedAgent] ?? '◈'}
                </div>
                <div>
                  <div className={`font-mono text-[11px] font-bold uppercase tracking-wider ${agentColor.text}`}>
                    {currentAgent?.name ?? 'Agent'}
                  </div>
                  <div className="font-mono text-[10px] text-steelDim">
                    {currentAgent?.description ?? ''}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => { setMessages([]); setConversationId(null); setError(null); }}
                  className="ml-auto rounded-lg border border-border px-3 py-1 font-mono text-[9.5px] text-steelDim transition-all hover:border-cyan/40 hover:text-cyan"
                >
                  NEW SESSION
                </button>
              </div>

              {/* ── Message thread ────────────────────────── */}
              <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5" style={{ minHeight: 0 }}>
                {/* Empty state */}
                {messages.length === 0 && (
                  <div className="flex h-full items-center justify-center">
                    <div className="max-w-[460px] text-center">
                      <div className={`mb-5 text-[40px] ${agentColor.text} opacity-30`}>
                        {AGENT_ICONS[selectedAgent] ?? '◈'}
                      </div>
                      <h3 className="mb-2 font-display text-[17px] font-semibold text-text">
                        {currentAgent?.name ?? 'AI Assistant'}
                      </h3>
                      <p className="mb-5 text-[13px] leading-relaxed text-steelDim">
                        {currentAgent?.description}
                      </p>
                      {/* Example prompts */}
                      <ExamplePrompts agentId={selectedAgent} onSelect={(p) => { setInput(p); textareaRef.current?.focus(); }} />
                    </div>
                  </div>
                )}

                {/* Message bubbles */}
                {messages.map((m) => (
                  <MessageBubble key={m.id} msg={m} agentColor={agentColor} />
                ))}

                {/* Typing indicator */}
                {loading && (
                  <div className="flex justify-start gap-2.5">
                    <div className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border text-[13px] ${agentColor.bg} ${agentColor.border} ${agentColor.text}`}>
                      {AGENT_ICONS[selectedAgent] ?? '◈'}
                    </div>
                    <div className={`rounded-2xl rounded-tl-sm border px-4 py-3 flex items-center gap-2 ${agentColor.bg} ${agentColor.border}`}>
                      <span className="w-dot w-dot-ok" style={{ animationDelay: '0s' }} />
                      <span className="w-dot w-dot-ok" style={{ animationDelay: '0.2s' }} />
                      <span className="w-dot w-dot-ok" style={{ animationDelay: '0.4s' }} />
                      <span className="ml-1 font-mono text-[11px] text-steel">Analyzing…</span>
                    </div>
                  </div>
                )}

                {/* Error bubble */}
                {error && (
                  <div className="flex justify-start">
                    <div className="max-w-[82%] rounded-2xl border border-red/25 bg-red/5 px-4 py-3 font-mono text-[11.5px] text-red">
                      ⚠ {error}
                    </div>
                  </div>
                )}

                {/* Scroll anchor */}
                <div ref={bottomRef} />
              </div>

              {/* ── Input bar ────────────────────────────── */}
              <div className="flex-shrink-0 border-t border-border bg-[#04060c] p-4">
                <div className="flex items-end gap-3">
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder={`Message ${currentAgent?.name ?? 'ZeroDay AI'}… (Enter to send, Shift+Enter for new line)`}
                    rows={2}
                    className={`flex-1 resize-none rounded-xl border bg-[#070c18] px-4 py-3 font-mono text-[13px] text-text placeholder:text-steelDim focus:outline-none transition-all ${
                      input.trim()
                        ? `${agentColor.border} focus:shadow-[0_0_0_3px_rgba(180,140,255,0.06)]`
                        : 'border-border focus:border-cyan/40'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={send}
                    disabled={loading || !input.trim()}
                    className="btn btn-primary self-end disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
                  >
                    Send
                  </button>
                </div>
                <p className="mt-2 font-mono text-[9.5px] text-steelDim">
                  Enter to send · Shift+Enter for new line · Responses powered by Groq (llama-3.3-70b)
                </p>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Agent sidebar item sub-component
// ─────────────────────────────────────────────────────────────────────────────

function AgentSidebarItem({
  id, name, description, selected, onSelect,
}: {
  id: string;
  name: string;
  description: string;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const c = AGENT_COLORS[id] ?? DEFAULT_AGENT_COLOR;

  return (
    <button
      type="button"
      onClick={() => onSelect(id)}
      className={`group w-full rounded-xl px-3 py-2.5 text-left transition-all duration-150 ${
        selected
          ? `${c.bg} border ${c.border}`
          : 'border border-transparent hover:bg-white/[0.03] hover:border-border'
      }`}
    >
      <div className="flex items-center gap-2.5">
        <span className={`text-[15px] ${selected ? c.text : 'text-steelDim group-hover:text-steel'}`}>
          {AGENT_ICONS[id] ?? '◈'}
        </span>
        <span className={`font-mono text-[11px] font-medium leading-tight ${selected ? c.text : 'text-steel'}`}>
          {name}
        </span>
      </div>
      {selected && (
        <p className="mt-1.5 pl-7 font-mono text-[9.5px] leading-relaxed text-steelDim">
          {description}
        </p>
      )}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Example prompts per agent
// ─────────────────────────────────────────────────────────────────────────────

const EXAMPLES: Record<string, string[]> = {
  assistant: [
    'Score CVE-2021-44228 for an internet-facing server, criticality 9',
    'Check my CERT-In compliance — logs retained 90 days, no NTP server',
    'What TTPs does APT29 commonly use?',
  ],
  vulnerability_analyst: [
    'Score CVE-2024-3400 for a perimeter firewall',
    'What is the EPSS score for CVE-2021-44228?',
    'Compare risk of CVE-2023-20198 vs CVE-2022-1388',
  ],
  threat_intelligence: [
    'Analyze IOC: 185.220.101.45 — is it malicious?',
    'What malware families target healthcare sector?',
    'Map Lazarus Group TTPs to MITRE ATT&CK',
  ],
  soc_analyst: [
    'Triage: 500 failed SSH logins from single IP in 10 minutes',
    'Alert: C2 beacon detected on port 443 — severity?',
    'How do I correlate these two log events into an incident?',
  ],
  pentest_assistant: [
    'What recon steps should I run on a web app target?',
    'How do I enumerate subdomains without triggering WAF?',
    'Help me write an executive summary for a pentest report',
  ],
  security_automation: [
    'Generate a Sigma rule to detect Pass-the-Hash attacks',
    'Write a Python script to parse Zeek connection logs for beaconing',
    'Create a CERT-In compliance checklist for a cloud provider',
  ],
};

const DEFAULT_EXAMPLES = EXAMPLES.assistant ?? [];

function ExamplePrompts({ agentId, onSelect }: { agentId: string; onSelect: (p: string) => void }) {
  const prompts = EXAMPLES[agentId] ?? DEFAULT_EXAMPLES;
  const c = AGENT_COLORS[agentId] ?? DEFAULT_AGENT_COLOR;

  return (
    <div className="space-y-2">
      <p className="font-mono text-[9.5px] uppercase tracking-widest text-steelDim">Try asking…</p>
      {prompts.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onSelect(p)}
          className={`w-full rounded-xl border px-4 py-2.5 text-left font-mono text-[11.5px] text-steel transition-all hover:-translate-y-0.5 ${c.bg} ${c.border} hover:${c.text}`}
        >
          &ldquo;{p}&rdquo;
        </button>
      ))}
    </div>
  );
}
