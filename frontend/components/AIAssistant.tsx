'use client';

import { useEffect, useRef, useState } from 'react';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCallsMade?: number;
};

type Agent = { id: string; name: string; description: string };

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// ─────────────────────────────────────────────────────────────
// Auth helpers
// ─────────────────────────────────────────────────────────────
function getToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('zd_access_token');
}
function saveToken(t: string) {
  localStorage.setItem('zd_access_token', t);
}
function clearToken() {
  localStorage.removeItem('zd_access_token');
}

// ─────────────────────────────────────────────────────────────
// Auth panel (login / register)
// ─────────────────────────────────────────────────────────────
function AuthPanel({ onAuth }: { onAuth: (token: string) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      if (mode === 'register') {
        const r = await fetch(`${BASE}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!r.ok) {
          const d = await r.json().catch(() => ({}));
          throw new Error(d?.detail ?? d?.error?.message ?? `Registration failed (${r.status})`);
        }
        // Auto-login after register
        setMode('login');
      }

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
      const token = d.access_token ?? d.token;
      if (!token) throw new Error('No token in response');
      saveToken(token);
      onAuth(token);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-[420px]">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mb-3 flex justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan/30 bg-cyan/10 text-2xl text-cyan">
              ◈
            </div>
          </div>
          <h3 className="mb-1.5 font-display text-[22px] font-bold text-text">
            {mode === 'login' ? 'Sign in to ZeroDay AI' : 'Create your account'}
          </h3>
          <p className="font-mono text-[12px] text-steelDim">
            {mode === 'login'
              ? 'Authenticate to access the AI security console'
              : 'Free account — no credit card required'}
          </p>
        </div>

        {/* Tab switcher */}
        <div className="mb-6 flex rounded-xl border border-border bg-[#04060c] p-1">
          {(['login', 'register'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => { setMode(m); setErr(null); }}
              className={`flex-1 rounded-lg py-2 font-mono text-[11px] uppercase tracking-wider transition-all ${
                mode === m
                  ? 'bg-cyan/10 text-cyan shadow-[0_0_12px_rgba(180,140,255,0.08)]'
                  : 'text-steelDim hover:text-steel'
              }`}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-4">
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
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full rounded-xl border border-border bg-[#04060c] px-4 py-3 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none focus:shadow-[0_0_0_3px_rgba(180,140,255,0.08)] transition-all"
            />
          </div>

          {err && (
            <div className="rounded-xl border border-red/20 bg-red/5 px-4 py-3 font-mono text-[11.5px] text-red">
              ⚠ {err}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="btn btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign In →' : 'Create Account →'}
          </button>
        </form>

        <p className="mt-5 text-center font-mono text-[11px] text-steelDim">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setErr(null); }}
            className="text-cyan hover:underline"
          >
            {mode === 'login' ? 'Register' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main AI Assistant component
// ─────────────────────────────────────────────────────────────
export default function AIAssistant() {
  const [token, setToken] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('assistant');
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Restore token from localStorage on mount
  useEffect(() => {
    setToken(getToken());
  }, []);

  // Load agents when authenticated
  useEffect(() => {
    if (!token) return;
    fetch(`${BASE}/api/v1/agents/`)
      .then((r) => r.json())
      .then((d) => setAgents(d.agents ?? []))
      .catch(() => {});
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleAuth(t: string) {
    setToken(t);
  }

  function logout() {
    clearToken();
    setToken(null);
    setMessages([]);
    setConversationId(null);
  }

  function reset() {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }

  async function send() {
    const text = input.trim();
    if (!text || loading || !token) return;
    setInput('');
    setError(null);

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      let data: { reply: string; conversation_id?: string; tool_calls_made?: number };

      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      };

      if (selectedAgent === 'assistant') {
        const res = await fetch(`${BASE}/api/v1/assistant/chat`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ message: text, conversation_id: conversationId }),
        });
        if (res.status === 401) {
          clearToken();
          setToken(null);
          throw new Error('Session expired — please sign in again');
        }
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          throw new Error(e?.error?.message ?? e?.detail ?? `HTTP ${res.status}`);
        }
        data = await res.json();
        if (data.conversation_id) setConversationId(data.conversation_id);
      } else {
        const res = await fetch(`${BASE}/api/v1/agents/run`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ agent: selectedAgent, message: text }),
        });
        if (res.status === 401) {
          clearToken();
          setToken(null);
          throw new Error('Session expired — please sign in again');
        }
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          throw new Error(e?.error?.message ?? e?.detail ?? `HTTP ${res.status}`);
        }
        data = await res.json();
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.reply || '(no reply)',
          toolCallsMade: data.tool_calls_made,
        },
      ]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <section
      id="ai-assistant"
      className="flex min-h-screen flex-col px-6 pb-12 pt-10 sm:px-8"
    >
      <div className="mx-auto flex w-full max-w-[1200px] flex-1 flex-col">

        {/* Section header */}
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="mb-2 block font-mono text-[11px] uppercase tracking-widest text-cyan">
              AI Assistant
            </span>
            <h2 className="font-display text-[24px] font-bold tracking-tight text-text sm:text-[32px]">
              ZeroDay Security AI Console
            </h2>
            <p className="mt-2 max-w-[540px] text-[14.5px] leading-relaxed text-steel">
              Ask about CVEs, compliance posture, threat indicators, or behavioral anomalies. Select
              a specialist agent for focused analysis.
            </p>
          </div>
          {token && (
            <button
              type="button"
              onClick={logout}
              className="flex items-center gap-2 rounded-xl border border-border px-4 py-2 font-mono text-[11px] tracking-wide text-steelDim transition-all hover:border-red/40 hover:text-red"
            >
              <span className="text-[10px]">◼</span> Sign out
            </button>
          )}
        </div>

        {/* Auth gate or chat */}
        {!token ? (
          <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-[#070c18]">
            <AuthPanel onAuth={handleAuth} />
          </div>
        ) : (
          <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-[#070c18]">
            {/* Agent selector bar */}
            <div className="border-b border-border px-5 py-3">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => { setSelectedAgent('assistant'); reset(); }}
                  className={`font-mono text-[10.5px] uppercase tracking-wider px-3.5 py-1.5 rounded-full border transition-all ${
                    selectedAgent === 'assistant'
                      ? 'border-cyan text-cyan bg-cyan/10 shadow-[0_0_12px_rgba(180,140,255,0.1)]'
                      : 'border-border text-steelDim hover:border-cyan/40 hover:text-cyan'
                  }`}
                >
                  General Assistant
                </button>
                {agents.map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => { setSelectedAgent(a.id); reset(); }}
                    title={a.description}
                    className={`font-mono text-[10.5px] uppercase tracking-wider px-3.5 py-1.5 rounded-full border transition-all ${
                      selectedAgent === a.id
                        ? 'border-cyan text-cyan bg-cyan/10 shadow-[0_0_12px_rgba(180,140,255,0.1)]'
                        : 'border-border text-steelDim hover:border-cyan/40 hover:text-cyan'
                    }`}
                  >
                    {a.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Terminal-style title bar */}
            <div className="flex items-center gap-2 border-b border-border bg-white/[0.015] px-5 py-2.5">
              <span className="w-dot w-dot-ok" />
              <span className="font-mono text-[10.5px] tracking-wider text-steel">
                {selectedAgent === 'assistant'
                  ? 'GENERAL ASSISTANT'
                  : selectedAgent.toUpperCase().replace(/_/g, ' ')}
              </span>
              <button
                type="button"
                onClick={reset}
                className="ml-auto font-mono text-[10px] text-steelDim hover:text-cyan transition-colors"
              >
                NEW SESSION
              </button>
            </div>

            {/* Message thread — fills available height */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4" style={{ minHeight: 0 }}>
              {messages.length === 0 && (
                <div className="flex h-full min-h-[200px] items-center justify-center">
                  <div className="text-center">
                    <div className="mb-4 text-[32px] opacity-20">◈</div>
                    <p className="font-mono text-[12px] text-steelDim leading-relaxed">
                      Ask a security question — e.g.
                      <br />
                      <span className="text-steel">&ldquo;Score CVE-2021-44228 for an internet-facing server, criticality 9&rdquo;</span>
                      <br />
                      <span className="text-steel">&ldquo;Check my CERT-In compliance — logs retained 90 days, no NTP server&rdquo;</span>
                    </p>
                  </div>
                </div>
              )}
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[82%] rounded-2xl px-4 py-3 text-[13.5px] leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-blue/15 border border-blue/25 text-text'
                        : 'glass-panel border-border text-text'
                    }`}
                  >
                    {m.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-mono text-[9px] uppercase tracking-widest text-cyan">ZeroDay AI</span>
                        {m.toolCallsMade ? (
                          <span className="font-mono text-[9px] text-green">{m.toolCallsMade} tool{m.toolCallsMade > 1 ? 's' : ''} used</span>
                        ) : null}
                      </div>
                    )}
                    <pre className="whitespace-pre-wrap font-[inherit]">{m.content}</pre>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="glass-panel rounded-2xl px-4 py-3 flex items-center gap-2">
                    <span className="w-dot w-dot-ok" style={{ animationDelay: '0s' }} />
                    <span className="w-dot w-dot-ok" style={{ animationDelay: '0.2s' }} />
                    <span className="w-dot w-dot-ok" style={{ animationDelay: '0.4s' }} />
                    <span className="font-mono text-[11px] text-steel ml-1">Analyzing…</span>
                  </div>
                </div>
              )}
              {error && (
                <div className="rounded-xl border border-red/20 bg-red/5 px-4 py-3 font-mono text-[11.5px] text-red">
                  ⚠ {error}
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input bar — pinned to bottom */}
            <div className="border-t border-border p-4 flex gap-3 bg-[#070c18]">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Ask ZeroDay AI… (Enter to send, Shift+Enter for new line)"
                rows={2}
                className="flex-1 resize-none rounded-xl border border-border bg-[#04060c] px-4 py-3 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none focus:shadow-[0_0_0_3px_rgba(180,140,255,0.06)] transition-all"
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
          </div>
        )}
      </div>
    </section>
  );
}
