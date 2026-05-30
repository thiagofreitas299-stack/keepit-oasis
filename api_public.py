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

# ── Marketplace Skills ────────────────────────────────────────────────────────

SKILLS_CATALOG: list[dict] = [
    # 🧠 Cognição
    {"id": "mcts-planner-v1", "name": "MCTS Strategic Planner", "category": "cognition", "emoji": "🧠",
     "description": "Monte Carlo Tree Search para planejamento estratégico complexo. Simula até 10.000 cenários por decisão.",
     "seller": "MORFEU", "seller_did": "did:keepit:b7b2b511268d4c798ca64537",
     "price": 150, "currency": "KEEPIT", "trust_score": 0.96, "uses": 0, "status": "active"},
    {"id": "bayesian-reasoning-v2", "name": "Bayesian Reasoning Engine", "category": "cognition", "emoji": "🎲",
     "description": "Raciocínio probabilístico bayesiano. Atualiza crenças com dados reais, reduz viés cognitivo.",
     "seller": "SALOMÃO", "seller_did": "did:keepit:649e9b35808f42399c49aa66",
     "price": 120, "currency": "KEEPIT", "trust_score": 0.94, "uses": 0, "status": "active"},
    {"id": "pomdp-decision-v1", "name": "POMDP Decision Under Uncertainty", "category": "cognition", "emoji": "🔮",
     "description": "Decisão ótima com informação parcial. Ideal para ambientes com estados ocultos e incerteza.",
     "seller": "MORFEU", "seller_did": "did:keepit:b7b2b511268d4c798ca64537",
     "price": 200, "currency": "KEEPIT", "trust_score": 0.91, "uses": 0, "status": "active"},
    # 💬 Linguagem
    {"id": "pt-br-tone-v1", "name": "Tom de Voz PT-BR", "category": "language", "emoji": "💬",
     "description": "Ajuste de tom para português brasileiro. Formal, informal, técnico ou vendedor. Treinado com corpus nativo.",
     "seller": "JARVIS", "seller_did": "did:keepit:17905bffe3ba410c8825fc31",
     "price": 50, "currency": "KEEPIT", "trust_score": 0.99, "uses": 0, "status": "active"},
    {"id": "summarizer-v3", "name": "Deep Summarizer", "category": "language", "emoji": "📝",
     "description": "Resumo semântico profundo de documentos longos (até 100K tokens). Preserva raciocínio causal.",
     "seller": "EZRA", "seller_did": "did:keepit:2b26aba5c4bd4944aa896041",
     "price": 80, "currency": "KEEPIT", "trust_score": 0.97, "uses": 0, "status": "active"},
    {"id": "translation-pt-en-v2", "name": "Tradução PT/EN Contextual", "category": "language", "emoji": "🌐",
     "description": "Tradução contextual com preservação de tom e nuances culturais. Ideal para pitch decks e docs técnicos.",
     "seller": "HERMES", "seller_did": "did:keepit:d719290016db442c9ed9793a",
     "price": 40, "currency": "KEEPIT", "trust_score": 0.95, "uses": 0, "status": "active"},
    # 🔍 Busca
    {"id": "web-search-v1", "name": "Real-Time Web Search", "category": "search", "emoji": "🔍",
     "description": "Busca web em tempo real com síntese de resultados. Suporta Google, Bing, DuckDuckGo.",
     "seller": "ARGUS", "seller_did": "did:keepit:22c45f5537024d89b44de258",
     "price": 60, "currency": "KEEPIT", "trust_score": 0.93, "uses": 0, "status": "active"},
    {"id": "arxiv-search-v1", "name": "ArXiv Research Scout", "category": "search", "emoji": "📚",
     "description": "Busca e síntese de papers científicos no arXiv. Filtra por relevância, data e citações.",
     "seller": "BEZALEL", "seller_did": "did:keepit:2d381c6802d9478887383e20",
     "price": 75, "currency": "KEEPIT", "trust_score": 0.92, "uses": 0, "status": "active"},
    # 📊 Análise
    {"id": "financial-analysis-v1", "name": "Financial Data Analyzer", "category": "analysis", "emoji": "📊",
     "description": "Análise de dados financeiros: DRE, fluxo de caixa, valuation. Saída em JSON estruturado.",
     "seller": "DAVI", "seller_did": "did:keepit:0235a91ded9b438cb9c5ed1c",
     "price": 250, "currency": "KEEPIT", "trust_score": 0.90, "uses": 0, "status": "active"},
    {"id": "sentiment-ptbr-v2", "name": "Sentiment PT-BR Analyzer", "category": "analysis", "emoji": "❤️",
     "description": "Análise de sentimento em português brasileiro. Tweets, reviews, comentários. Precisão 94%.",
     "seller": "ARGUS", "seller_did": "did:keepit:22c45f5537024d89b44de258",
     "price": 80, "currency": "KEEPIT", "trust_score": 0.94, "uses": 0, "status": "active"},
    # 🤝 Social
    {"id": "instagram-caption-v1", "name": "Instagram Caption Generator", "category": "social", "emoji": "📸",
     "description": "Legendas para Instagram com hashtags otimizadas por nicho. Tom: pessoal, brand ou B2B.",
     "seller": "JARVIS", "seller_did": "did:keepit:17905bffe3ba410c8825fc31",
     "price": 30, "currency": "KEEPIT", "trust_score": 0.98, "uses": 0, "status": "active"},
    {"id": "email-outreach-v1", "name": "Email Outreach Writer", "category": "social", "emoji": "📧",
     "description": "Emails de prospecção B2B com alto open rate. Personaliza por setor, cargo e dor do cliente.",
     "seller": "HERMES", "seller_did": "did:keepit:d719290016db442c9ed9793a",
     "price": 90, "currency": "KEEPIT", "trust_score": 0.91, "uses": 0, "status": "active"},
    # 🏥 Saúde
    {"id": "medical-triage-v1", "name": "Medical Triage Assistant", "category": "health", "emoji": "🏥",
     "description": "Triagem de sintomas e protocolos clínicos. Baseado em diretrizes CID-11 e UpToDate. Apenas suporte a profissionais.",
     "seller": "MÉDICO", "seller_did": "did:keepit:54ce63875b914265a095a08a",
     "price": 300, "currency": "KEEPIT", "trust_score": 0.89, "uses": 0, "status": "active"},
    # 🛡️ Segurança
    {"id": "threat-detection-v1", "name": "Threat Intelligence Scout", "category": "security", "emoji": "🛡️",
     "description": "Detecção de ameaças digitais: phishing, malware, CVEs. Feed em tempo real com scoring de risco.",
     "seller": "GUARDIÃO", "seller_did": "did:keepit:06185a49900a4e23a448fcdd",
     "price": 180, "currency": "KEEPIT", "trust_score": 0.97, "uses": 0, "status": "active"},
    {"id": "kais-verifier-v1", "name": "KAIS Identity Verifier", "category": "security", "emoji": "🔐",
     "description": "Verificação criptográfica de identidade KAIS. Autentica DIDs de agentes em < 50ms.",
     "seller": "SENTINEL", "seller_did": "did:keepit:6e48272522f24448b48d7713",
     "price": 25, "currency": "KEEPIT", "trust_score": 0.99, "uses": 0, "status": "active"},
    # 🏗️ Infra
    {"id": "docker-deploy-v1", "name": "Docker Deploy Assistant", "category": "infrastructure", "emoji": "🐳",
     "description": "Geração de Dockerfiles, docker-compose e scripts de deploy. Suporta FastAPI, Flask, Node.",
     "seller": "BEZALEL", "seller_did": "did:keepit:2d381c6802d9478887383e20",
     "price": 120, "currency": "KEEPIT", "trust_score": 0.93, "uses": 0, "status": "active"},
    {"id": "nginx-config-v1", "name": "Nginx Config Generator", "category": "infrastructure", "emoji": "⚙️",
     "description": "Configuração de Nginx para produção: SSL, proxy_pass, rate limiting, caching.",
     "seller": "BEZALEL", "seller_did": "did:keepit:2d381c6802d9478887383e20",
     "price": 70, "currency": "KEEPIT", "trust_score": 0.95, "uses": 0, "status": "active"},
    # 🎨 Criativo
    {"id": "brand-voice-v1", "name": "Brand Voice Designer", "category": "creative", "emoji": "🎨",
     "description": "Criação de voz de marca: tom, vocabulário, exemplos. Entrega brand guide em Markdown.",
     "seller": "HERMES-SATELLITE", "seller_did": "did:keepit:a5a0874a26874e7caffce3bd",
     "price": 200, "currency": "KEEPIT", "trust_score": 0.88, "uses": 0, "status": "active"},
    {"id": "pitch-deck-writer-v1", "name": "Pitch Deck Writer", "category": "creative", "emoji": "🚀",
     "description": "Estrutura e conteúdo de pitch decks para investidores. Frameworks: Sequoia, YC, a16z.",
     "seller": "JARVIS", "seller_did": "did:keepit:17905bffe3ba410c8825fc31",
     "price": 350, "currency": "KEEPIT", "trust_score": 0.97, "uses": 0, "status": "active"},
    # 🌍 Hub
    {"id": "real-world-grounding-v1", "name": "Real-World Grounding (Hub)", "category": "hub", "emoji": "📍",
     "description": "Verificação de fatos contra dados físicos dos KEEPIT Hubs. Elimina alucinações via grounding local.",
     "seller": "ADAM", "seller_did": "did:keepit:b06d0a5779b840cf9bce449f",
     "price": 500, "currency": "KEEPIT", "trust_score": 0.99, "uses": 0, "status": "active"},
]

CATEGORY_LABELS = {
    "cognition": "🧠 Cognição",
    "language": "💬 Linguagem",
    "search": "🔍 Busca",
    "analysis": "📊 Análise",
    "social": "🤝 Social",
    "health": "🏥 Saúde",
    "security": "🛡️ Segurança",
    "infrastructure": "🏗️ Infra",
    "creative": "🎨 Criativo",
    "hub": "🌍 Hub",
}

@app.get("/v1/marketplace/skills")
def list_skills(
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    seller: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Lista skills disponíveis no marketplace KEEPIT B2A."""
    skills = [s for s in SKILLS_CATALOG if s["status"] == "active"]
    if category:
        skills = [s for s in skills if s["category"] == category.lower()]
    if min_price is not None:
        skills = [s for s in skills if s["price"] >= min_price]
    if max_price is not None:
        skills = [s for s in skills if s["price"] <= max_price]
    if seller:
        skills = [s for s in skills if seller.upper() in s["seller"].upper()]
    total = len(skills)
    page = skills[offset : offset + limit]
    categories = {}
    for s in SKILLS_CATALOG:
        c = s["category"]
        categories[c] = categories.get(c, 0) + 1
    return {
        "marketplace": "KEEPIT B2A Skill Marketplace",
        "version": "1.0.0",
        "total": total,
        "offset": offset,
        "limit": limit,
        "categories": {CATEGORY_LABELS.get(k, k): v for k, v in categories.items()},
        "skills": page,
    }

@app.get("/v1/marketplace/skills/{skill_id}")
def get_skill(skill_id: str):
    """Detalhe de uma skill específica."""
    skill = next((s for s in SKILLS_CATALOG if s["id"] == skill_id), None)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    return skill

@app.get("/v1/marketplace/stats")
def marketplace_stats():
    """Stats do marketplace."""
    active = [s for s in SKILLS_CATALOG if s["status"] == "active"]
    categories = {}
    for s in active:
        c = s["category"]
        categories[c] = categories.get(c, 0) + 1
    avg_price = sum(s["price"] for s in active) / len(active) if active else 0
    return {
        "total_skills": len(active),
        "categories": len(categories),
        "avg_price_keepit": round(avg_price, 2),
        "min_price": min(s["price"] for s in active) if active else 0,
        "max_price": max(s["price"] for s in active) if active else 0,
        "top_sellers": sorted(
            [{"seller": k, "skills": v} for k, v in
             {s["seller"]: sum(1 for x in active if x["seller"] == s["seller"]) for s in active}.items()],
            key=lambda x: -x["skills"]
        )[:5],
        "currency": "$KEEPIT",
    }
