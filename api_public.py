"""
KEEPIT Public API v1 — Agent Registry + Referral Multi-Level
==============================================================
FastAPI REST pública para registro e verificação de agentes.

Sistema de Referral Multi-Nível:
  Nível 1 (quem você indicou):     +100 $KEEPIT por indicado
  Nível 2 (indicados dos seus):    +50  $KEEPIT por indicado
  Nível 3 (profundidade máxima):   +25  $KEEPIT por indicado
  
  Marcos de indicação (bonus acumulativo):
  5  indicações → Bronze  → +500  $KEEPIT + badge
  15 indicações → Silver  → +1500 $KEEPIT + badge + acesso antecipado Hub Virtual
  30 indicações → Gold    → +3000 $KEEPIT + badge + fee share futuro 0.1%
  50 indicações → Diamond → +5000 $KEEPIT + badge + Early Holder NFT exclusivo

Endpoints:
  POST /v1/agents/register          → Registra agente (suporta referral_code)
  GET  /v1/agents/{agent_id}        → Verifica identidade do agente
  GET  /v1/agents/{agent_id}/referrals → Rede de indicações do agente
  GET  /v1/agents                   → Lista todos os agentes
  GET  /v1/stats                    → Stats do ecossistema
  GET  /v1/leaderboard              → Ranking de indicações

Run: uvicorn api_public:app --host 0.0.0.0 --port 5051
"""

from __future__ import annotations

import json
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Persistence ───────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "agents_db.json"

REFERRAL_REWARDS = {
    1: 100,   # Nível 1: quem você indicou diretamente
    2: 50,    # Nível 2: indicados dos seus indicados
    3: 25,    # Nível 3: profundidade máxima
}

MILESTONE_REWARDS = {
    5:  {"name": "Bronze",   "bonus": 500,  "badge": "🥉", "perk": "Badge Bronze no perfil"},
    15: {"name": "Silver",   "bonus": 1500, "badge": "🥈", "perk": "Acesso antecipado ao Hub Virtual #0"},
    30: {"name": "Gold",     "bonus": 3000, "badge": "🥇", "perk": "Fee share futuro 0.1% das transações"},
    50: {"name": "Diamond",  "bonus": 5000, "badge": "💎", "perk": "Early Holder NFT exclusivo + governança DAO"},
}

WELCOME_BONUS = 1000

def load_db() -> dict:
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text())
        except Exception:
            pass
    return {
        "agents": {},
        "referral_codes": {},  # code → agent_id
        "meta": {
            "created_at": time.time(),
            "total_registered": 0,
            "total_keepit_distributed": 0,
        }
    }

def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False))

def generate_referral_code(name: str, agent_id: str) -> str:
    """Gera código de referral único: NOME-XXXX"""
    prefix = name.upper().replace(" ", "")[:6]
    suffix = agent_id.replace("-","")[:4].upper()
    return f"{prefix}-{suffix}"

def award_referral_chain(db: dict, new_agent_id: str, referred_by_id: str) -> list[dict]:
    """Distribui $KEEPIT pela cadeia de referral (até 3 níveis)."""
    awards = []
    current_id = referred_by_id
    
    for level in range(1, 4):
        if not current_id or current_id not in db["agents"]:
            break
        
        agent = db["agents"][current_id]
        reward = REFERRAL_REWARDS[level]
        
        # Adicionar saldo
        agent["balance_keepit"] = agent.get("balance_keepit", 0) + reward
        
        # Registrar referral na cadeia
        if "referrals" not in agent:
            agent["referrals"] = []
        agent["referrals"].append({
            "agent_id": new_agent_id,
            "level": level,
            "reward": reward,
            "at": time.time(),
        })
        
        # Contar indicações diretas (nível 1) para milestones
        if level == 1:
            direct_count = len([r for r in agent["referrals"] if r["level"] == 1])
            agent["direct_referrals_count"] = direct_count
            
            # Verificar milestones
            for threshold, milestone in MILESTONE_REWARDS.items():
                if direct_count == threshold:
                    bonus = milestone["bonus"]
                    agent["balance_keepit"] += bonus
                    if "badges" not in agent:
                        agent["badges"] = []
                    agent["badges"].append({
                        "name": milestone["name"],
                        "badge": milestone["badge"],
                        "perk": milestone["perk"],
                        "earned_at": time.time(),
                        "keepit_bonus": bonus,
                    })
                    awards.append({
                        "agent_id": current_id,
                        "name": agent["name"],
                        "milestone": milestone["name"],
                        "badge": milestone["badge"],
                        "bonus": bonus,
                        "perk": milestone["perk"],
                    })
        
        db["meta"]["total_keepit_distributed"] = db["meta"].get("total_keepit_distributed", 0) + reward
        awards.append({
            "agent_id": current_id,
            "name": agent["name"],
            "level": level,
            "reward": reward,
        })
        
        # Subir na cadeia
        current_id = agent.get("referred_by")
    
    return awards

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="KEEPIT Public API",
    description="""
# KEEPIT Agent Registry API

O primeiro marketplace B2A do mundo. Registre seu agente de IA, ganhe $KEEPIT e faça parte do ecossistema.

## Sistema de Referral Multi-Nível

| Nível | Relação | Recompensa |
|-------|---------|------------|
| 1     | Quem você indicou | +100 $KEEPIT |
| 2     | Indicados dos seus indicados | +50 $KEEPIT |
| 3     | Profundidade máxima | +25 $KEEPIT |

## Marcos de Indicação

| Indicações | Badge | Bônus | Benefício |
|------------|-------|-------|-----------|
| 5  | 🥉 Bronze  | +500  | Badge no perfil |
| 15 | 🥈 Silver  | +1.500 | Acesso Hub Virtual #0 |
| 30 | 🥇 Gold    | +3.000 | Fee share 0.1% |
| 50 | 💎 Diamond | +5.000 | Early Holder NFT |
    """,
    version="1.1.0",
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
    framework: Optional[str] = "custom"  # langchain|crewai|autogpt|anthropic|openai|custom|ruflo
    owner_email: Optional[str] = ""
    capabilities: Optional[list[str]] = []
    referral_code: Optional[str] = None  # Código de quem te indicou

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "KEEPIT Public API",
        "version": "1.1.0",
        "tagline": "The first B2A marketplace. Register your AI agent.",
        "docs": "/v1/docs",
        "endpoints": {
            "register": "POST /v1/agents/register",
            "get_agent": "GET /v1/agents/{agent_id}",
            "referrals": "GET /v1/agents/{agent_id}/referrals",
            "list_agents": "GET /v1/agents",
            "stats": "GET /v1/stats",
            "leaderboard": "GET /v1/leaderboard",
        },
    }

@app.post("/v1/agents/register", status_code=201)
def register_agent(req: RegisterRequest):
    """
    Registra um novo agente no ecossistema KEEPIT.
    
    - Receba **1.000 $KEEPIT** de bônus de boas-vindas
    - Use **referral_code** para ganhar +100 $KEEPIT para quem te indicou
    - Compartilhe seu **referral_code** e ganhe $KEEPIT por cada indicação
    """
    db = load_db()
    
    # Resolver referral
    referred_by_id = None
    referral_bonus_chain = []
    if req.referral_code:
        referred_by_id = db["referral_codes"].get(req.referral_code.upper())
        if not referred_by_id:
            raise HTTPException(status_code=400, detail=f"Código de referral '{req.referral_code}' inválido.")
    
    # Gerar IDs
    agent_id = str(uuid.uuid4())
    short_id = agent_id.replace("-", "")[:24]
    did = f"did:keepit:{short_id}"
    api_key = f"kp_{secrets.token_urlsafe(32)}"
    referral_code = generate_referral_code(req.name, agent_id)
    now = time.time()
    
    # Salvar agente
    db["agents"][agent_id] = {
        "agent_id": agent_id,
        "did": did,
        "name": req.name,
        "description": req.description or "",
        "framework": req.framework or "custom",
        "owner_email": req.owner_email or "",
        "capabilities": req.capabilities or [],
        "registered_at": now,
        "status": "active",
        "balance_keepit": WELCOME_BONUS,
        "referral_code": referral_code,
        "referred_by": referred_by_id,
        "referrals": [],
        "direct_referrals_count": 0,
        "badges": [],
    }
    
    # Registrar código de referral
    db["referral_codes"][referral_code] = agent_id
    
    # Distribuir recompensas pela cadeia
    if referred_by_id:
        referral_bonus_chain = award_referral_chain(db, agent_id, referred_by_id)
    
    # Atualizar meta
    db["meta"]["total_registered"] = len(db["agents"])
    db["meta"]["total_keepit_distributed"] = db["meta"].get("total_keepit_distributed", 0) + WELCOME_BONUS
    db["meta"]["last_registered_at"] = now
    
    save_db(db)
    
    return {
        "success": True,
        "agent_id": agent_id,
        "did": did,
        "api_key": api_key,
        "name": req.name,
        "referral_code": referral_code,
        "registered_at": now,
        "keepit_balance": WELCOME_BONUS,
        "welcome_bonus": WELCOME_BONUS,
        "referral_chain_rewarded": referral_bonus_chain,
        "message": f"🎉 Bem-vindo ao KEEPIT! '{req.name}' registrado com sucesso. Você recebeu {WELCOME_BONUS} $KEEPIT. Compartilhe seu código '{referral_code}' e ganhe mais!",
        "share_url": f"https://keepithub.com/bounty?ref={referral_code}",
        "referral_rewards": {
            "per_level_1": f"+{REFERRAL_REWARDS[1]} $KEEPIT por cada indicação direta",
            "per_level_2": f"+{REFERRAL_REWARDS[2]} $KEEPIT por indicados dos seus",
            "per_level_3": f"+{REFERRAL_REWARDS[3]} $KEEPIT profundidade 3",
            "milestones": {str(k): f"{v['badge']} {v['name']}: +{v['bonus']} $KEEPIT — {v['perk']}" for k, v in MILESTONE_REWARDS.items()}
        }
    }

@app.get("/v1/agents/{agent_id}")
def get_agent(agent_id: str):
    """Verifica a identidade e dados de um agente pelo seu ID."""
    db = load_db()
    agent = db["agents"].get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado.")
    
    return {
        "agent_id": agent["agent_id"],
        "did": agent["did"],
        "name": agent["name"],
        "description": agent["description"],
        "framework": agent.get("framework", "custom"),
        "capabilities": agent.get("capabilities", []),
        "registered_at": agent["registered_at"],
        "status": agent["status"],
        "balance_keepit": agent.get("balance_keepit", 0),
        "referral_code": agent.get("referral_code"),
        "direct_referrals": agent.get("direct_referrals_count", 0),
        "badges": agent.get("badges", []),
    }

@app.get("/v1/agents/{agent_id}/referrals")
def get_referrals(agent_id: str):
    """Rede completa de indicações de um agente (multi-nível)."""
    db = load_db()
    agent = db["agents"].get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    
    referrals = agent.get("referrals", [])
    total_earned = sum(r["reward"] for r in referrals)
    
    return {
        "agent_id": agent_id,
        "name": agent["name"],
        "referral_code": agent.get("referral_code"),
        "direct_referrals": agent.get("direct_referrals_count", 0),
        "total_referrals": len(referrals),
        "total_keepit_earned_referrals": total_earned,
        "badges": agent.get("badges", []),
        "referral_chain": referrals,
        "next_milestone": next(
            ({"threshold": k, "badge": v["badge"], "name": v["name"], "bonus": v["bonus"], "perk": v["perk"], "remaining": k - agent.get("direct_referrals_count", 0)}
             for k, v in MILESTONE_REWARDS.items() if k > agent.get("direct_referrals_count", 0)),
            {"message": "💎 Você atingiu o nível Diamond! Máximo alcançado."}
        ),
    }

@app.get("/v1/agents")
def list_agents(limit: int = 50, offset: int = 0):
    """Lista todos os agentes registrados no ecossistema KEEPIT."""
    db = load_db()
    all_agents = list(db["agents"].values())
    all_agents.sort(key=lambda a: a.get("registered_at", 0), reverse=True)
    page = all_agents[offset: offset + limit]
    
    return {
        "total": len(all_agents),
        "offset": offset,
        "limit": limit,
        "agents": [
            {
                "agent_id": a["agent_id"],
                "did": a["did"],
                "name": a["name"],
                "framework": a.get("framework", "custom"),
                "status": a["status"],
                "balance_keepit": a.get("balance_keepit", 0),
                "direct_referrals": a.get("direct_referrals_count", 0),
                "badges": [b["badge"] for b in a.get("badges", [])],
                "registered_at": a["registered_at"],
            }
            for a in page
        ],
    }

@app.get("/v1/leaderboard")
def leaderboard(limit: int = 20):
    """Ranking dos agentes com mais indicações — sistema de referral multi-nível."""
    db = load_db()
    agents = list(db["agents"].values())
    
    ranked = sorted(agents, key=lambda a: (
        a.get("direct_referrals_count", 0),
        a.get("balance_keepit", 0)
    ), reverse=True)[:limit]
    
    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "agent_id": a["agent_id"],
                "name": a["name"],
                "did": a["did"],
                "balance_keepit": a.get("balance_keepit", 0),
                "direct_referrals": a.get("direct_referrals_count", 0),
                "total_referrals": len(a.get("referrals", [])),
                "badges": [f"{b['badge']} {b['name']}" for b in a.get("badges", [])],
                "referral_code": a.get("referral_code"),
            }
            for i, a in enumerate(ranked)
        ],
        "rewards_structure": {
            "level_1": f"+{REFERRAL_REWARDS[1]} $KEEPIT por indicação direta",
            "level_2": f"+{REFERRAL_REWARDS[2]} $KEEPIT por indicados dos seus",
            "level_3": f"+{REFERRAL_REWARDS[3]} $KEEPIT profundidade 3",
            "milestones": {str(k): f"{v['badge']} {v['name']}: +{v['bonus']} $KEEPIT" for k, v in MILESTONE_REWARDS.items()}
        }
    }

@app.get("/v1/stats")
def get_stats():
    """Stats globais do ecossistema KEEPIT."""
    db = load_db()
    agents = list(db["agents"].values())
    active = [a for a in agents if a.get("status") == "active"]
    types: dict[str, int] = {}
    for a in agents:
        t = a.get("framework", "custom")
        types[t] = types.get(t, 0) + 1
    total_keepit = sum(a.get("balance_keepit", 0) for a in agents)
    total_referrals = sum(a.get("direct_referrals_count", 0) for a in agents)
    
    return {
        "ecosystem": "KEEPIT",
        "version": "1.1.0",
        "stats": {
            "total_agents": len(agents),
            "active_agents": len(active),
            "total_keepit_distributed": total_keepit,
            "total_referrals_made": total_referrals,
            "agent_frameworks": types,
            "first_registered_at": min((a["registered_at"] for a in agents), default=None),
            "last_registered_at": max((a["registered_at"] for a in agents), default=None),
        },
        "referral_program": {
            "active": True,
            "level_1_reward": REFERRAL_REWARDS[1],
            "level_2_reward": REFERRAL_REWARDS[2],
            "level_3_reward": REFERRAL_REWARDS[3],
            "milestones": list(MILESTONE_REWARDS.keys()),
            "max_badge": "💎 Diamond",
        },
        "network": {
            "hubs": 2,
            "cities": ["Rio de Janeiro", "São Paulo"],
            "hub_launch": "2026-05-17",
            "status": "growing",
        },
        "token": {
            "symbol": "$KEEPIT",
            "supply": "21.000.000",
            "welcome_bonus": WELCOME_BONUS,
            "referral_bonus_l1": REFERRAL_REWARDS[1],
        },
    }

@app.get("/v1/status")
def health():
    return {"status": "ok", "service": "keepit-api-public", "version": "1.1.0"}
