/**
 * API client for ZeroDay Security AI backend.
 * Base URL is configured via NEXT_PUBLIC_API_BASE_URL env var.
 */

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...rest } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(rest.headers as Record<string, string> | undefined),
  };
  const response = await fetch(`${BASE}/api/v1${path}`, { ...rest, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface ChatResponse {
  conversation_id: string;
  reply: string;
  tool_calls_made: number;
}

export interface AgentResponse {
  agent: string;
  reply: string;
  tool_calls_made: number;
}

export async function sendChat(
  message: string,
  token: string,
  conversationId?: string
): Promise<ChatResponse> {
  return request<ChatResponse>("/assistant/chat", {
    method: "POST",
    token,
    body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
  });
}

export async function runAgent(
  agent: string,
  message: string,
  token: string
): Promise<AgentResponse> {
  return request<AgentResponse>("/agents/run", {
    method: "POST",
    token,
    body: JSON.stringify({ agent, message }),
  });
}

export async function listAgents(): Promise<{ agents: { id: string; name: string; description: string }[] }> {
  return request("/agents/");
}

export async function healthCheck(): Promise<{ status: string }> {
  return request("/health");
}
