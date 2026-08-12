"""Specialized agent dispatch API.

ZeroDay Security AI provides a unified master agent that covers all security
domains, plus focused specialist agents for specific workflows.

ZeroDay Security Services — Vijay Ishan Chowdhury
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Master unified agent — covers all domains
from app.agents.master import MasterSecurityAgent

# Specialist agents
from app.agents.pentest_assistant import PentestAssistantAgent
from app.agents.reconnaissance import ReconnaissanceAgent
from app.agents.security_automation import SecurityAutomationAgent
from app.agents.soc_analyst import SOCAnalystAgent
from app.agents.threat_intelligence import ThreatIntelligenceAgent
from app.agents.vulnerability_analyst import VulnerabilityAnalystAgent
from app.agents.web_security_analyst import WebSecurityAnalystAgent
from app.api.deps import get_current_user
from app.core.exceptions import AppError
from app.db.base import get_db
from app.db.models.user import User

router = APIRouter(prefix="/agents", tags=["agents"])

# ─────────────────────────────────────────────────────────────────────────────
# Agent registry — master agent is the default; specialists available by ID
# ─────────────────────────────────────────────────────────────────────────────
_AGENTS = {
    # Primary: unified master agent covering all security domains
    "master": MasterSecurityAgent,
    # Specialists: focused agents for specific workflows
    "vulnerability_analyst": VulnerabilityAnalystAgent,
    "threat_intelligence": ThreatIntelligenceAgent,
    "soc_analyst": SOCAnalystAgent,
    "pentest_assistant": PentestAssistantAgent,
    "security_automation": SecurityAutomationAgent,
    "web_security_analyst": WebSecurityAnalystAgent,
    "reconnaissance": ReconnaissanceAgent,
}


class AgentRequest(BaseModel):
    agent: str = Field(default="master", description="Agent ID to invoke")
    message: str = Field(min_length=1, max_length=8000)


class AgentResponse(BaseModel):
    agent: str
    reply: str
    tool_calls_made: int


@router.get("/")
async def list_agents() -> dict:
    """List all available ZeroDay Security AI agents."""
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
                    "Web application security — 26 attack classes",
                    "OSINT & attack surface mapping",
                    "Threat intelligence & IOC analysis",
                    "SOC alert triage & incident response",
                    "Exploit chain building (A→B signal table)",
                    "7-Question Gate finding validation",
                    "Security report writing (H1/Bugcrowd/Intigriti)",
                    "Compliance assessment (CERT-In, DPDP, NIST, ISO 27001)",
                    "Red team methodology (AD, cloud, mobile, Web3)",
                ],
            },
            {
                "id": "vulnerability_analyst",
                "name": "Vulnerability Analyst",
                "description": "CVE risk scoring, exploitability assessment, remediation timelines",
                "category": "specialist",
            },
            {
                "id": "threat_intelligence",
                "name": "Threat Intelligence",
                "description": "IOC analysis, malware families, threat actor TTPs, ATT&CK mapping",
                "category": "specialist",
            },
            {
                "id": "soc_analyst",
                "name": "SOC Analyst",
                "description": "Alert triage, incident severity, correlation and response playbooks",
                "category": "specialist",
            },
            {
                "id": "pentest_assistant",
                "name": "Pentest Assistant",
                "description": "Methodology guidance, scope prioritization, engagement planning",
                "category": "specialist",
            },
            {
                "id": "web_security_analyst",
                "name": "Web Security Analyst",
                "description": "OWASP Top 10, injection attacks, auth bypass, SSRF, XSS, GraphQL",
                "category": "specialist",
            },
            {
                "id": "reconnaissance",
                "name": "Reconnaissance",
                "description": "OSINT, subdomain enumeration, JS bundle mining, cloud asset discovery",
                "category": "specialist",
            },
            {
                "id": "security_automation",
                "name": "Security Automation",
                "description": "Compliance scanning, detection rules, remediation roadmaps",
                "category": "specialist",
            },
        ]
    }


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Invoke a ZeroDay Security AI agent."""
    agent_cls = _AGENTS.get(request.agent)
    if agent_cls is None:
        raise AppError(
            f"Unknown agent: {request.agent}. Available: {', '.join(_AGENTS.keys())}",
            code="UNKNOWN_AGENT",
            status_code=400,
        )

    try:
        agent = agent_cls()
        result = await agent.run(request.message, db)
    except Exception as exc:
        raise AppError(str(exc), code="AGENT_ERROR", status_code=503) from exc

    return AgentResponse(
        agent=result.agent, reply=result.reply, tool_calls_made=result.tool_calls_made
    )
