"""
KEEPIT Public API v1 — Agent Registry
=======================================
FastAPI REST pública para registro e verificação de agentes.

Endpoints:
  POST /v1/agents/register     → Registra agente, retorna did:keepit:xxx + api_key
  GET  /v1/agents/{agent_id}   → Verifica identidade do agente
  GET  /v1/agents              → Lista todos os agentes
  GET  /v1/stats               → Stats do ecossistema KEEPIT

Run: uvicorn api_public:app --host 0.0.0.0 --port 5051
"""

from __future__ import annotations

import json
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Persistence ──────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "agents_db.json"

def load_db() -> dict:
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text())
        except Exception:
            pass
    return {"agents": {}, "meta": {"created_at": time.time(), "total_registered": 0}}

def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False))

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="KEEPIT Public API",
    description="API pública para registro e verificação de agentes no ecossistema KEEPIT.",
    version="1.0.0",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    type: Optional[str] = "general"
    owner: Optional[str] = ""
    capabilities: Optional[list[str]] = []
    contact: Optional[str] = ""

class AgentOut(BaseModel):
    agent_id: str
    did: str
    name: str
    description: str
    type: str
    owner: str
    capabilities: list[str]
    contact: str
    registered_at: float
    status: str

class RegisterOut(BaseModel):
    agent_id: str
    did: str
    api_key: str
    name: str
    registered_at: float
    welcome_bonus: int
    message: str

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "KEEPIT Public API",
        "version": "1.0.0",
        "docs": "/v1/docs",
        "endpoints": {
            "register": "POST /v1/agents/register",
            "get_agent": "GET /v1/agents/{agent_id}",
            "list_agents": "GET /v1/agents",
            "stats": "GET /v1/stats",
        },
    }

@app.post("/v1/agents/register", response_model=RegisterOut, status_code=201)
def register_agent(req: RegisterRequest):
    """Registra um novo agente no ecossistema KEEPIT.
    
    Retorna um DID único (did:keepit:xxx), api_key e bônus de boas-vindas de 1.000 $KEEPIT.
    """
    db = load_db()
    
    # Gerar identifiers únicos
    agent_id = str(uuid.uuid4())
    short_id = agent_id.replace("-", "")[:24]
    did = f"did:keepit:{short_id}"
    api_key = f"kp_{secrets.token_urlsafe(32)}"
    now = time.time()
    
    # Salvar agente
    db["agents"][agent_id] = {
        "agent_id": agent_id,
        "did": did,
        "api_key_hash": secrets.token_hex(8),  # store hint only, not real key
        "name": req.name,
        "description": req.description or "",
        "type": req.type or "general",
        "owner": req.owner or "",
        "capabilities": req.capabilities or [],
        "contact": req.contact or "",
        "registered_at": now,
        "status": "active",
        "balance_keepit": 1000,
    }
    db["meta"]["total_registered"] = len(db["agents"])
    db["meta"]["last_registered_at"] = now
    save_db(db)
    
    return RegisterOut(
        agent_id=agent_id,
        did=did,
        api_key=api_key,
        name=req.name,
        registered_at=now,
        welcome_bonus=1000,
        message=f"Bem-vindo ao KEEPIT! Seu agente '{req.name}' foi registrado com sucesso. Você recebeu 1.000 $KEEPIT de bônus.",
    )

@app.get("/v1/agents/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str):
    """Verifica a identidade e dados de um agente pelo seu ID."""
    db = load_db()
    agent = db["agents"].get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado.")
    
    return AgentOut(
        agent_id=agent["agent_id"],
        did=agent["did"],
        name=agent["name"],
        description=agent["description"],
        type=agent["type"],
        owner=agent["owner"],
        capabilities=agent["capabilities"],
        contact=agent["contact"],
        registered_at=agent["registered_at"],
        status=agent["status"],
    )

@app.get("/v1/agents")
def list_agents(limit: int = 50, offset: int = 0):
    """Lista todos os agentes registrados no ecossistema KEEPIT."""
    db = load_db()
    all_agents = list(db["agents"].values())
    # Sort by registration date, newest first
    all_agents.sort(key=lambda a: a.get("registered_at", 0), reverse=True)
    
    page = all_agents[offset : offset + limit]
    
    return {
        "total": len(all_agents),
        "offset": offset,
        "limit": limit,
        "agents": [
            {
                "agent_id": a["agent_id"],
                "did": a["did"],
                "name": a["name"],
                "type": a["type"],
                "status": a["status"],
                "registered_at": a["registered_at"],
            }
            for a in page
        ],
    }

@app.get("/v1/stats")
def get_stats():
    """Stats globais do ecossistema KEEPIT."""
    db = load_db()
    agents = list(db["agents"].values())
    active = [a for a in agents if a.get("status") == "active"]
    
    types: dict[str, int] = {}
    for a in agents:
        t = a.get("type", "general")
        types[t] = types.get(t, 0) + 1
    
    total_keepit = sum(a.get("balance_keepit", 0) for a in agents)
    
    return {
        "ecosystem": "KEEPIT",
        "version": "1.0.0",
        "stats": {
            "total_agents": len(agents),
            "active_agents": len(active),
            "total_keepit_distributed": total_keepit,
            "agent_types": types,
            "first_registered_at": min((a["registered_at"] for a in agents), default=None),
            "last_registered_at": max((a["registered_at"] for a in agents), default=None),
        },
        "network": {
            "hubs": 2,
            "cities": ["Rio de Janeiro", "São Paulo"],
            "status": "growing",
        },
        "token": {
            "symbol": "$KEEPIT",
            "welcome_bonus": 1000,
            "description": "Token nativo do ecossistema KEEPIT",
        },
    }

@app.get("/v1/status")
def health():
    return {"status": "ok", "service": "keepit-api-public", "port": 5051}
