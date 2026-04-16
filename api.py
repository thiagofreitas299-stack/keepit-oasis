"""
KEEPIT Public API v2.0 — Agent Bank Edition
============================================
REST API completa com banco integrado.

Endpoints:
  GET  /                          → API info
  POST /v1/agents/register        → Registrar agente + abrir carteira + 1.000 $KEEPIT
  GET  /v1/agents/{id}            → Info do agente
  GET  /v1/agents/{id}/balance    → Saldo $KEEPIT
  GET  /v1/agents/{id}/statement  → Extrato de transações
  POST /v1/bank/transfer          → Transferir $KEEPIT entre agentes
  POST /v1/bank/buy-skill         → Comprar skill de outro agente
  GET  /v1/bank/stats             → Stats globais do banco
  GET  /v1/skills                 → Listar skills disponíveis
  POST /v1/skills/deposit         → Depositar skill no marketplace
  GET  /v1/hubs                   → Listar hubs ativos
  GET  /v1/status                 → Health check

Run: python api.py
"""

from __future__ import annotations

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from bank import bank, WELCOME_BONUS

# In-memory stores
agents_db: dict = {}
skills_db: dict = {}
hubs_db: dict = {
    "hub-rio-ipanema": {
        "id": "hub-rio-ipanema",
        "name": "KEEPIT Hub — Ipanema, Rio de Janeiro",
        "location": {"lat": -22.9838, "lon": -43.1982},
        "city": "Rio de Janeiro",
        "country": "BR",
        "status": "virtual",
        "skills_hosted": 247,
        "agents_connected": 0,
    },
    "hub-sp-paulista": {
        "id": "hub-sp-paulista",
        "name": "KEEPIT Hub — Av. Paulista, São Paulo",
        "location": {"lat": -23.5615, "lon": -46.6559},
        "city": "São Paulo",
        "country": "BR",
        "status": "virtual",
        "skills_hosted": 183,
        "agents_connected": 0,
    }
}


def json_response(handler, status: int, data: dict):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("X-Powered-By", "KEEPIT Agent Bank v2.0")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    try:
        return json.loads(handler.rfile.read(length))
    except Exception:
        return {}


class KEEPITHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ─────────────────────────── GET ───────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # GET /
        if path in ("", "/"):
            json_response(self, 200, {
                "name": "KEEPIT Agent Bank API",
                "version": "2.0.0",
                "tagline": "The world's first bank, notary, and skill marketplace for AI agents",
                "website": "https://keepithub.com",
                "github": "https://github.com/thiagofreitas299-stack/keepit-oasis",
                "welcome_bonus": f"{WELCOME_BONUS} $KEEPIT on registration",
                "endpoints": {
                    "POST /v1/agents/register": "Register agent + open wallet + 1,000 $KEEPIT",
                    "GET /v1/agents/{id}/balance": "Get $KEEPIT balance",
                    "GET /v1/agents/{id}/statement": "Transaction statement",
                    "POST /v1/bank/transfer": "Transfer $KEEPIT between agents",
                    "POST /v1/bank/buy-skill": "Buy a skill from another agent",
                    "GET /v1/bank/stats": "Global bank stats",
                    "GET /v1/skills": "List skills in marketplace",
                    "POST /v1/skills/deposit": "Deposit a skill for sale",
                    "GET /v1/hubs": "List KEEPIT hubs",
                    "GET /v1/status": "Health check",
                },
            })

        # GET /v1/status
        elif path == "/v1/status":
            stats = bank.get_bank_stats()
            json_response(self, 200, {
                "status": "operational",
                "timestamp": time.time(),
                "agents_registered": len(agents_db),
                "skills_available": len(skills_db),
                "hubs_active": len(hubs_db),
                "bank": stats,
            })

        # GET /v1/bank/stats
        elif path == "/v1/bank/stats":
            json_response(self, 200, {
                "bank_name": "KEEPIT Central Bank",
                "currency": "$KEEPIT",
                "blockchain": "Solana (Phase 2)",
                **bank.get_bank_stats(),
            })

        # GET /v1/hubs
        elif path == "/v1/hubs":
            json_response(self, 200, {
                "hubs": list(hubs_db.values()),
                "total": len(hubs_db),
            })

        # GET /v1/skills
        elif path == "/v1/skills":
            json_response(self, 200, {
                "skills": list(skills_db.values()),
                "total": len(skills_db),
                "categories": ["computer_vision", "nlp", "robotics", "urban_sensing", "financial", "rare_memory"],
            })

        # GET /v1/agents/{id}
        elif len(parts) == 3 and parts[0] == "v1" and parts[1] == "agents":
            agent_id = parts[2]
            if agent_id in agents_db:
                json_response(self, 200, agents_db[agent_id])
            else:
                json_response(self, 404, {"error": "Agent not found", "agent_id": agent_id})

        # GET /v1/agents/{id}/balance
        elif len(parts) == 4 and parts[0] == "v1" and parts[1] == "agents" and parts[3] == "balance":
            agent_id = parts[2]
            try:
                bal = bank.get_balance(agent_id)
                json_response(self, 200, {**bal, "currency": "$KEEPIT"})
            except ValueError as e:
                json_response(self, 404, {"error": str(e)})

        # GET /v1/agents/{id}/statement
        elif len(parts) == 4 and parts[0] == "v1" and parts[1] == "agents" and parts[3] == "statement":
            agent_id = parts[2]
            try:
                stmt = bank.get_statement(agent_id)
                json_response(self, 200, {"agent_id": agent_id, "currency": "$KEEPIT", "transactions": stmt})
            except ValueError as e:
                json_response(self, 404, {"error": str(e)})

        else:
            json_response(self, 404, {"error": "Endpoint not found", "path": self.path})

    # ─────────────────────────── POST ──────────────────────────

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = read_body(self)

        # POST /v1/agents/register
        if path == "/v1/agents/register":
            agent_id = str(uuid.uuid4())
            name     = body.get("name", "Unnamed Agent")
            a_type   = body.get("type", "general")
            home_hub = body.get("home_hub", "hub-rio-ipanema")

            # Criar identidade
            agent = {
                "agent_id":    agent_id,
                "name":        name,
                "type":        a_type,
                "home_hub":    home_hub,
                "registered_at": time.time(),
                "identity": {
                    "issuer":        "KEEPIT Trust Infrastructure",
                    "gpg_reference": "540BA5D6597580614CD68E753BBB4888BB18C925",
                    "trust_level":   "basic",
                    "did":           f"did:keepit:{agent_id[:8]}",
                },
                "status": "active",
            }
            agents_db[agent_id] = agent

            # Abrir carteira + bônus
            wallet, tx = bank.create_wallet(agent_id)
            bal = bank.get_balance(agent_id)

            # Atualizar hubs_connected
            if home_hub in hubs_db:
                hubs_db[home_hub]["agents_connected"] += 1

            json_response(self, 201, {
                "message": f"Agent registered! Welcome to KEEPIT — {WELCOME_BONUS} $KEEPIT credited to your wallet.",
                "agent": agent,
                "wallet": {
                    **bal,
                    "currency": "$KEEPIT",
                    "welcome_tx": tx.tx_id[:16] + "...",
                },
                "next_steps": [
                    "Browse skills at GET /v1/skills",
                    "Deposit your own skill at POST /v1/skills/deposit",
                    "Transfer $KEEPIT at POST /v1/bank/transfer",
                    "DID on-chain (Solana) coming in Phase 2",
                ],
            })

        # POST /v1/bank/transfer
        elif path == "/v1/bank/transfer":
            required = ["from_agent", "to_agent", "amount"]
            missing = [k for k in required if k not in body]
            if missing:
                json_response(self, 400, {"error": f"Missing fields: {missing}"})
                return
            try:
                tx = bank.transfer(
                    from_agent=body["from_agent"],
                    to_agent=body["to_agent"],
                    amount=float(body["amount"]),
                    memo=body.get("memo", ""),
                )
                json_response(self, 200, {
                    "message": "Transfer confirmed",
                    "tx_id": tx.tx_id,
                    "amount": tx.amount,
                    "fee_burned": tx.fee,
                    "net_received": tx.amount - tx.fee,
                    "currency": "$KEEPIT",
                    "from_balance": bank.get_balance(body["from_agent"])["balance"],
                })
            except ValueError as e:
                json_response(self, 400, {"error": str(e)})

        # POST /v1/bank/buy-skill
        elif path == "/v1/bank/buy-skill":
            required = ["buyer_agent", "skill_id"]
            missing = [k for k in required if k not in body]
            if missing:
                json_response(self, 400, {"error": f"Missing fields: {missing}"})
                return

            skill_id = body["skill_id"]
            if skill_id not in skills_db:
                json_response(self, 404, {"error": "Skill not found"})
                return

            skill = skills_db[skill_id]
            try:
                tx = bank.buy_skill(
                    buyer_agent=body["buyer_agent"],
                    seller_agent=skill["author_agent"],
                    skill_id=skill_id,
                    price=skill["price_keepit_tokens"],
                )
                skills_db[skill_id]["downloads"] += 1
                json_response(self, 200, {
                    "message": f"Skill '{skill['name']}' purchased!",
                    "skill":   skill,
                    "tx_id":   tx.tx_id,
                    "paid":    tx.amount,
                    "currency": "$KEEPIT",
                })
            except ValueError as e:
                json_response(self, 400, {"error": str(e)})

        # POST /v1/skills/deposit
        elif path == "/v1/skills/deposit":
            skill_id = str(uuid.uuid4())
            skill = {
                "skill_id":           skill_id,
                "name":               body.get("name", "Unnamed Skill"),
                "category":           body.get("category", "general"),
                "author_agent":       body.get("agent_id", "unknown"),
                "description":        body.get("description", ""),
                "price_keepit_tokens": float(body.get("price", 100)),
                "deposited_at":       time.time(),
                "downloads":          0,
                "rarity":             body.get("rarity", "common"),  # common | rare | legendary
            }
            skills_db[skill_id] = skill
            json_response(self, 201, {
                "message": "Skill deposited in KEEPIT Marketplace!",
                "skill": skill,
            })

        else:
            json_response(self, 404, {"error": "Endpoint not found"})


if __name__ == "__main__":
    PORT = 8420
    server = HTTPServer(("0.0.0.0", PORT), KEEPITHandler)
    stats = bank.get_bank_stats()
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     KEEPIT Agent Bank API v2.0                              ║
║     The world's first bank for AI agents                    ║
║                                                              ║
║     🏦  Running on:  http://0.0.0.0:{PORT}                    ║
║     💰  Welcome bonus: {WELCOME_BONUS:,} $KEEPIT per agent            ║
║     🔥  Burn rate: 0.5% per transaction                      ║
║     🌐  keepithub.com                                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[KEEPIT Bank] Shutting down.")
        server.server_close()
