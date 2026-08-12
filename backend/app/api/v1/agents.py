"""Specialized agent dispatch API.

ZeroDay Security AI provides a unified master agent that covers all security
domains, plus focused specialist agents for specific workflows.

All agents now persist conversation history per user, per agent, in the
database so each user sees their own private history for every agent.

ZeroDay Security Services - Vijay Ishan Chowdhury
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.master import MasterSecurityAgent
from app.agents.pentest_assistant import PentestAssistantAgent
from app.agents.reconnaissance import ReconnaissanceAgent
from app.agents.security_automation import SecurityAutomationAgent
from app.agents.soc_analyst import SOCAnalystAgent
from app.agents.threat_intelligence import ThreatIntelligenceAgent
from app.agents.vulnerability_analyst import VulnerabilityAnalystAgent
from app.agents.web_security_analyst import WebSecurityAnalystAgent
from app.api.deps import get_current_user
from app.core.exceptions import AppError, NotFoundError
from app.db.base import get_db
from app.db.models.conversation import Conversation, Message
from app.db.models.user import User
from app.schemas.assistant import ConversationDetail, ConversationRead, MessageRead

router = APIRouter(prefix="/agents", tags=["agents"])

_AGENTS = {
    "master": MasterSecurityAgent,
    "vulnerability_analyst": VulnerabilityAnalystAgent,
    "threat_intelligence": ThreatIntelligenceAgent,
    "soc_analyst": SOCAnalystAgent,
    "pentest_assistant": PentestAssistantAgent,
    "security_automation": SecurityAutomationAgent,
    "web_security_analyst": WebSecurityAnalystAgent,
    "reconnaissance": ReconnaissanceAgent,
}

_AGENT_NAMES = {
    "master": "ZeroDay AI",
    "vulnerability_analyst": "Vulnerability Analyst",
    "threat_intelligence": "Threat Intelligence",
    "soc_analyst": "SOC Analyst",
    "pentest_assistant": "Pentest Assistant",
    "security_automation": "Security Automation",
    "web_security_analyst": "Web Security Analyst",
    "reconnaissance": "Reconnaissance",
}


class AgentRequest(BaseModel):
    agent: str = Field(default="master", description="Agent ID to invoke")
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(
        default=None,
        description="Resume an existing conversation; omit to start a new one",
    )


class AgentResponse(BaseModel):
    agent: str
    agent_name: str
    reply: str
    tool_calls_made: int
    conversation_id: str


@router.get("/")
async def list_agents() -> dict:
    return {
        "agents": [
            {
                "id": "master",
                "name": "ZeroDay AI",
                "description": (
                    "Unified security intelligence covering all domains: vulnerability analysis, "
                    "web security, OSINT/recon, threat intelligence, SOC, incident response, "
                    "exploit chaining, compliance, red team, and report writing."
                ),
                "category": "unified",
                "capabilities": [
                    "CVE risk scoring (NVD/EPSS/CISA KEV)",
                    "Web application security 26 attack classes",
                    "OSINT & attack surface mapping",
                    "Threat intelligence & IOC analysis",
                    "SOC alert triage & incident response",
                    "Exploit chain building",
                    "7-Question Gate finding validation",
                    "Security report writing (H1/Bugcrowd/Intigriti)",
                    "Compliance assessment (CERT-In, DPDP, NIST, ISO 27001)",
                    "Red team methodology (AD, cloud, mobile, Web3)",
                ],
            },
            {"id": "vulnerability_analyst", "name": "Vulnerability Analyst", "description": "CVE risk scoring, exploitability assessment, remediation timelines", "category": "specialist"},
            {"id": "threat_intelligence", "name": "Threat Intelligence", "description": "IOC analysis, malware families, threat actor TTPs, ATT&CK mapping", "category": "specialist"},
            {"id": "soc_analyst", "name": "SOC Analyst", "description": "Alert triage, incident severity, correlation and response playbooks", "category": "specialist"},
            {"id": "pentest_assistant", "name": "Pentest Assistant", "description": "Methodology guidance, scope prioritization, engagement planning", "category": "specialist"},
            {"id": "web_security_analyst", "name": "Web Security Analyst", "description": "OWASP Top 10, injection attacks, auth bypass, SSRF, XSS, GraphQL", "category": "specialist"},
            {"id": "reconnaissance", "name": "Reconnaissance", "description": "OSINT, subdomain enumeration, JS bundle mining, cloud asset discovery", "category": "specialist"},
            {"id": "security_automation", "name": "Security Automation", "description": "Compliance scanning, detection rules, remediation roadmaps", "category": "specialist"},
        ]
    }


@router.get("/conversations", response_model=list[ConversationRead])
async def list_agent_conversations(
    agent: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id, Conversation.agent_id == agent)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_agent_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation is None:
        raise NotFoundError("Conversation not found")
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        agent_id=conversation.agent_id,
        created_at=conversation.created_at.isoformat(),
        messages=[MessageRead(role=m.role, content=m.content, created_at=m.created_at.isoformat()) for m in messages],
    )


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    agent_cls = _AGENTS.get(request.agent)
    if agent_cls is None:
        raise AppError(
            f"Unknown agent: {request.agent}. Available: {', '.join(_AGENTS.keys())}",
            code="UNKNOWN_AGENT",
            status_code=400,
        )

    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user.id,
                Conversation.agent_id == request.agent,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise NotFoundError("Conversation not found")
    else:
        conversation = Conversation(
            user_id=user.id,
            agent_id=request.agent,
            title=request.message[:60] or "New conversation",
        )
        db.add(conversation)
        await db.flush()

    history_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.asc())
    )
    history = []
    for m in history_result.scalars().all():
        content = m.content
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        history.append({"role": m.role, "content": content})

    user_content = [{"type": "text", "text": request.message}]
    db.add(Message(conversation_id=conversation.id, role="user", content=user_content))

    try:
        agent = agent_cls()
        result = await agent.run_with_history(request.message, history, db)
    except Exception as exc:
        raise AppError(str(exc), code="AGENT_ERROR", status_code=503) from exc

    tool_calls_made = 0
    for turn in result.raw_turns:
        content = turn["content"]
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        db.add(Message(conversation_id=conversation.id, role=turn["role"], content=content))
        if turn["role"] == "assistant" and isinstance(turn["content"], list):
            tool_calls_made += sum(1 for b in turn["content"] if isinstance(b, dict) and b.get("type") == "tool_use")

    await db.commit()

    return AgentResponse(
        agent=result.agent,
        agent_name=_AGENT_NAMES.get(request.agent, request.agent),
        reply=result.reply,
        tool_calls_made=tool_calls_made,
        conversation_id=conversation.id,
    )
