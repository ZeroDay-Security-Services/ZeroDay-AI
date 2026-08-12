'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentName?: string;
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
          throw new Error(d?.error?.message ?? 'Registration failed');
        }
      }
      const r = await fetch(`${BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d?.error?.message ?? 'Invalid email or password');
      }
      const { access_token } = await r.json();
      saveToken(access_token);
      onAuth(access_token);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center p-8">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <span className="font-mono text-[10px] uppercase tracking-widest text-cyan">
            {mode === 'login' ? 'Sign in to continue' : 'Create your account'}
          </span>
          <h3 className="mt-2 font-display text-[20px] font-bold text-text">
            ZeroDay AI Console
          </h3>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email address"
            required
            className="w-full rounded-xl border border-border bg-[#04060c] px-4 py-2.5 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
            className="w-full rounded-xl border border-border bg-[#04060c] px-4 py-2.5 font-mono text-[13px] text-text placeholder:text-steelDim focus:border-cyan/50 focus:outline-none"
          />
          {err && (
            <p className="font-mono text-[11px] text-red">{err}</p>
          )}
          <button
            type="submit"
            disabled={busy}
            className="btn btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
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
  // Per-agent conversation IDs: agentId -> conversationId
  const [convIds, setConvIds] = useState<Record<string, string>>({});
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('assistant');
  const [error, setError] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
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

  // Load history for the currently selected agent
  const loadAgentHistory = useCallback(async (agentId: string, tok: string) => {
    setHistoryLoading(true);
    setMessages([]);
    setError(null);
    try {
      let listUrl: string;
      let detailUrlPrefix: string;

      if (agentId === 'assistant') {
        listUrl = `${BASE}/api/v1/assistant/conversations?agent_id=assistant`;
        detailUrlPrefix = `${BASE}/api/v1/assistant/conversations/`;
      } else {
        listUrl = `${BASE}/api/v1/agents/conversations?agent=${agentId}`;
        detailUrlPrefix = `${BASE}/api/v1/agents/conversations/`;
      }

      const listRes = await fetch(listUrl, { headers: { Authorization: `Bearer ${tok}` } });
      if (!listRes.ok) return;
      const convos = await listRes.json();
      if (!convos || convos.length === 0) return;

      const latestId = convos[0].id;
      const detailRes = await fetch(`${detailUrlPrefix}${latestId}`, {
        headers: { Authorization: `Bearer ${tok}` },
      });
      if (!detailRes.ok) return;

      const detail = await detailRes.json();
      // Save the conversation ID for this agent
      setConvIds((prev) => ({ ...prev, [agentId]: detail.id }));

      // Determine agent display name
      const agentName = agentId === 'assistant' ? 'General Assistant' : detail.agent_id;

      setMessages(
        detail.messages
          .filter((m: any) => m.role === 'user' || m.role === 'assistant')
          .map((m: any, i: number) => ({
            id: `hist-${i}`,
            role: m.role,
            agentName: m.role === 'assistant' ? agentName : undefined,
            content: Array.isArray(m.content)
              ? m.content.map((c: any) => c.text || '').join('')
              : String(m.content),
          }))
      );
    } catch (e) {
      console.error('Failed to load history', e);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Load history whenever token or selected agent changes
  useEffect(() => {
    if (!token) return;
    loadAgentHistory(selectedAgent, token);
  }, [token, selectedAgent, loadAgentHistory]);

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
    setConvIds({});
    setError(null);
  }

  function newSession() {
    // Clear conversation ID for current agent to start fresh
    setConvIds((prev) => {
      const updated = { ...prev };
      delete updated[selectedAgent];
      return updated;
    });
    setMessages([]);
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
      let data: { reply: string; conversation_id?: string; agent_name?: string; tool_calls_made?: number };
      const currentConvId = convIds[selectedAgent];

      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      };

      if (selectedAgent === 'assistant') {
        const res = await fetch(`${BASE}/api/v1/assistant/chat`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ message: text, conversation_id: currentConvId ?? null }),
        });
        if (res.status === 401) { clearToken(); setToken(null); throw new Error('Session expired'); }
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          throw new Error(e?.error?.message ?? e?.detail ?? `HTTP ${res.status}`);
        }
        data = await res.json();
        data.agent_name = 'General Assistant';
      } else {
        const res = await fetch(`${BASE}/api/v1/agents/run`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            agent: selectedAgent,
            message: text,
            conversation_id: currentConvId ?? null,
          }),
        });
        if (res.status === 401) { clearToken(); setToken(null); throw new Error('Session expired'); }
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          throw new Error(e?.error?.message ?? e?.detail ?? `HTTP ${res.status}`);
        }
        data = await res.json();
      }

      // Save the conversation ID for this agent
      if (data.conversation_id) {
        setConvIds((prev) => ({ ...prev, [selectedAgent]: data.conversation_id! }));
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.reply || '(no reply)',
          agentName: data.agent_name,
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

  // Get display name for the current agent
  const currentAgentName =
    selectedAgent === 'assistant'
      ? 'General Assistant'
      : agents.find((a) => a.id === selectedAgent)?.name ?? selectedAgent.replace(/_/g, ' ');

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
                  onClick={() => setSelectedAgent('assistant')}
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
                    onClick={() => setSelectedAgent(a.id)}
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
                {currentAgentName.toUpperCase()}
              </span>
              <button
                type="button"
                onClick={newSession}
                className="ml-auto font-mono text-[10px] text-steelDim hover:text-cyan transition-colors"
              >
                NEW SESSION
              </button>
            </div>

            {/* Message thread */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4" style={{ minHeight: 0 }}>
              {historyLoading && (
                <div className="flex items-center justify-center py-8">
                  <span className="font-mono text-[11px] text-steelDim animate-pulse">Loading conversation history...</span>
                </div>
              )}
              {!historyLoading && messages.length === 0 && (
                <div className="flex h-full min-h-[200px] items-center justify-center">
                  <div className="text-center">
                    <div className="mb-4 text-[32px] opacity-20">◈</div>
                    <p className="font-mono text-[12px] text-steelDim leading-relaxed">
                      Start a new conversation with the <span className="text-steel">{currentAgentName}</span>
                    </p>
                  </div>
                </div>
              )}
              {!historyLoading && messages.map((m) => (
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
                        <span className="font-mono text-[9px] uppercase tracking-widest text-cyan">
                          {m.agentName ?? currentAgentName}
                        </span>
                        {m.toolCallsMade ? (
                          <span className="font-mono text-[9px] text-green">
                            {m.toolCallsMade} tool{m.toolCallsMade > 1 ? 's' : ''} used
                          </span>
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
                    <span className="font-mono text-[11px] text-steel ml-1">Analyzing...</span>
                  </div>
                </div>
              )}
              {error && (
                <div className="rounded-xl border border-red/20 bg-red/5 px-4 py-3 font-mono text-[11.5px] text-red">
                  {error}
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input bar */}
            <div className="border-t border-border p-4 flex gap-3 bg-[#070c18]">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder={`Message ${currentAgentName}... (Enter to send, Shift+Enter for new line)`}
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
