import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base
from app.db.session import engine
from app.models import User, Event, EventParticipant, Comment, Bookmark, Follow, Review, ChatMessage  # noqa: F401
from app.api.routes_auth import router as auth_router
from app.api.routes_users import router as users_router
from app.api.routes_events import router as events_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_follows import router as follows_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Event Discovery API",
    description="Backend for a location-based social event discovery app",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(follows_router)
app.include_router(events_router)
app.include_router(uploads_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# --- WebSocket Chat ---
import json
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
from app.db.session import SessionLocal
from app.services.auth_service import decode_token
from app.models.chat_message import ChatMessage as ChatMessageModel
from app.models.event_participant import EventParticipant as EP, ParticipantStatus as PS

_chat_connections: dict[str, list[WebSocket]] = defaultdict(list)


@app.websocket("/events/{event_id}/chat")
async def websocket_chat(websocket: WebSocket, event_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    try:
        user_id_str = decode_token(token)
    except Exception:
        await websocket.close(code=4001)
        return

    db = SessionLocal()
    try:
        import uuid as _uuid
        uid = _uuid.UUID(user_id_str)
        eid = _uuid.UUID(event_id)
        participant = (
            db.query(EP)
            .filter(EP.event_id == eid, EP.user_id == uid, EP.status == PS.joined)
            .first()
        )
        if not participant:
            await websocket.close(code=4003)
            return

        user = db.query(User).filter(User.id == uid).first()
        user_name = user.name if user else "Unknown"
    finally:
        db.close()

    await websocket.accept()
    _chat_connections[event_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            text = msg_data.get("text", "").strip()
            if not text:
                continue

            db = SessionLocal()
            try:
                import uuid as _uuid
                chat_msg = ChatMessageModel(
                    event_id=_uuid.UUID(event_id),
                    user_id=_uuid.UUID(user_id_str),
                    text=text,
                )
                db.add(chat_msg)
                db.commit()
                db.refresh(chat_msg)
                broadcast = json.dumps({
                    "id": str(chat_msg.id),
                    "event_id": event_id,
                    "user_id": user_id_str,
                    "user_name": user_name,
                    "text": text,
                    "created_at": chat_msg.created_at.isoformat(),
                })
            finally:
                db.close()

            for conn in _chat_connections[event_id]:
                try:
                    await conn.send_text(broadcast)
                except Exception:
                    pass
    except WebSocketDisconnect:
        _chat_connections[event_id].remove(websocket)


@app.get("/events/{event_id}/chat/history")
def get_chat_history(event_id: str, limit: int = 50):
    import uuid as _uuid
    db = SessionLocal()
    try:
        messages = (
            db.query(ChatMessageModel)
            .filter(ChatMessageModel.event_id == _uuid.UUID(event_id))
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
            .all()
        )
        result = []
        for msg in reversed(messages):
            user = msg.user
            result.append({
                "id": str(msg.id),
                "event_id": str(msg.event_id),
                "user_id": str(msg.user_id),
                "user_name": user.name if user else "Unknown",
                "text": msg.text,
                "created_at": msg.created_at.isoformat(),
            })
        return result
    finally:
        db.close()
