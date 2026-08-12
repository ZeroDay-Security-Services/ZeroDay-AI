"""AI Assistant chat API -- the conversational entry point tying together
CVE risk scoring, compliance checks, threat intel, and behavioral
analytics via real tool-calling (see app/ai_core/)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.assistant import AssistantError, AssistantService, extract_text
from app.api.deps import get_current_user
from app.core.exceptions import AppError, NotFoundError
from app.db.base import get_db
from app.db.models.conversation import Conversation, Message
from app.db.models.user import User
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationRead,
    MessageRead,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    # ── Resolve or create conversation ────────────────────────────────────────
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise NotFoundError("Conversation not found")
    else:
        conversation = Conversation(
            user_id=user.id, title=request.message[:60] or "New conversation"
        )
        db.add(conversation)
        await db.flush()

    # ── Load history (normalize content: string → list for API compat) ────────
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    history = []
    for m in history_result.scalars().all():
        content = m.content
        # Stored as plain string for simple messages; wrap for API
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        history.append({"role": m.role, "content": content})

    # ── Save and send user turn ───────────────────────────────────────────────
    user_content = [{"type": "text", "text": request.message}]
    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=user_content,
        )
    )
    user_turn = {"role": "user", "content": user_content}

    # ── Run AI turn ──────────────────────────────────────────────────────────
    try:
        service = AssistantService()
        new_turns = await service.run_turn(history + [user_turn], db)
    except AssistantError as exc:
        raise AppError(
            str(exc),
            code="ASSISTANT_NOT_CONFIGURED",
            status_code=503,
        ) from exc

    # ── Persist new turns ────────────────────────────────────────────────────
    tool_calls_made = 0
    for turn in new_turns:
        content = turn["content"]
        # Ensure content is always JSON-serializable (list)
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        db.add(
            Message(
                conversation_id=conversation.id,
                role=turn["role"],
                content=content,
            )
        )
        if turn["role"] == "assistant" and isinstance(turn["content"], list):
            tool_calls_made += sum(
                1
                for b in turn["content"]
                if isinstance(b, dict) and b.get("type") == "tool_use"
            )

    await db.commit()

    # ── Extract final reply text ─────────────────────────────────────────────
    final_text = ""
    for turn in reversed(new_turns):
        if turn["role"] == "assistant":
            final_text = extract_text(turn["content"])
            break

    return ChatResponse(
        conversation_id=conversation.id,
        reply=final_text,
        tool_calls_made=tool_calls_made,
    )



@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user.id
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation is None:
        raise NotFoundError("Conversation not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        messages=[
            MessageRead(
                role=m.role, content=m.content, created_at=m.created_at.isoformat()
            )
            for m in messages
        ],
    )
