"""
KEEPIT Public API v1
====================
REST API for the KEEPIT Agent Identity & Skill Marketplace.

Endpoints:
  GET  /                     → API info
  POST /v1/agents/register   → Register an agent identity
  GET  /v1/agents/{agent_id} → Get agent info
  POST /v1/agents/{agent_id}/sign → Sign a message as this agent
  GET  /v1/skills            → List available skills
  POST /v1/skills/deposit    → Deposit a new skill
  GET  /v1/hubs              → List active hubs
  GET  /v1/status            → Health check

Run: python api.py
"""

from __future__ import annotations

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

try:
    from agent_identity import AgentIdentityHub, AgentCredential
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False

try:
    from skill_marketplace import SkillMarketplace, Skill
    MARKETPLACE_AVAILABLE = True
except ImportError:
    MARKETPLACE_AVAILABLE = False

# In-memory store (replace with DB in production)
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
        "agents_connected": 1,
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
    handler.send_header("X-Powered-By", "KEEPIT Agent Identity Layer")
    handler.end_headers()
    handler.wfile.write(body)


class KEEPITHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "" or path == "/":
            json_response(self, 200, {
                "name": "KEEPIT Agent Identity API",
                "version": "1.0.0",
                "description": "The world's first identity & skill marketplace for AI agents",
                "tagline": "The Steam for AI Agents",
                "website": "https://keepithub.com",
                "github": "https://github.com/thiagofreitas299-stack/keepit-oasis",
                "gpg_key": "540BA5D6597580614CD68E753BBB4888BB18C925",
                "endpoints": {
                    "POST /v1/agents/register": "Register an agent identity",
                    "GET /v1/agents/{id}": "Get agent info",
                    "GET /v1/skills": "List available skills",
                    "POST /v1/skills/deposit": "Deposit a skill",
                    "GET /v1/hubs": "List active hubs",
                    "GET /v1/status": "Health check",
                },
                "powered_by": "KEEPIT Trust Infrastructure | Thiago Freitas 2026"
            })

        elif path == "/v1/status":
            json_response(self, 200, {
                "status": "operational",
                "timestamp": time.time(),
                "agents_registered": len(agents_db),
                "skills_available": len(skills_db),
                "hubs_active": len(hubs_db),
                "identity_module": IDENTITY_AVAILABLE,
                "marketplace_module": MARKETPLACE_AVAILABLE,
            })

        elif path == "/v1/hubs":
            json_response(self, 200, {
                "hubs": list(hubs_db.values()),
                "total": len(hubs_db),
                "note": "Physical hubs coming soon. Virtual hubs active now."
            })

        elif path == "/v1/skills":
            json_response(self, 200, {
                "skills": list(skills_db.values()),
                "total": len(skills_db),
                "categories": ["computer_vision", "nlp", "robotics", "urban_sensing", "financial"],
            })

        elif path.startswith("/v1/agents/"):
            agent_id = path.split("/v1/agents/")[-1]
            if agent_id in agents_db:
                json_response(self, 200, agents_db[agent_id])
            else:
                json_response(self, 404, {"error": "Agent not found", "agent_id": agent_id})

        else:
            json_response(self, 404, {"error": "Endpoint not found", "path": self.path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_length > 0:
            try:
                body = json.loads(self.rfile.read(content_length))
            except Exception:
                json_response(self, 400, {"error": "Invalid JSON body"})
                return

        if path == "/v1/agents/register":
            agent_id = str(uuid.uuid4())
            name = body.get("name", "Unnamed Agent")
            agent_type = body.get("type", "general")
            home_hub = body.get("home_hub", "hub-rio-ipanema")

            agent = {
                "agent_id": agent_id,
                "name": name,
                "type": agent_type,
                "home_hub": home_hub,
                "registered_at": time.time(),
                "identity": {
                    "issuer": "KEEPIT Trust Infrastructure",
                    "gpg_reference": "540BA5D6597580614CD68E753BBB4888BB18C925",
                    "trust_level": "basic",
                    "did_placeholder": f"did:keepit:{agent_id[:8]}",
                },
                "status": "active",
            }
            agents_db[agent_id] = agent
            json_response(self, 201, {
                "message": "Agent registered successfully",
                "agent": agent,
                "note": "DID on-chain (Solana) coming in Phase 2"
            })

        elif path == "/v1/skills/deposit":
            skill_id = str(uuid.uuid4())
            skill = {
                "skill_id": skill_id,
                "name": body.get("name", "Unnamed Skill"),
                "category": body.get("category", "general"),
                "author_agent": body.get("agent_id", "unknown"),
                "description": body.get("description", ""),
                "price_keepit_tokens": body.get("price", 10),
                "deposited_at": time.time(),
                "downloads": 0,
            }
            skills_db[skill_id] = skill
            json_response(self, 201, {
                "message": "Skill deposited successfully",
                "skill": skill
            })

        else:
            json_response(self, 404, {"error": "Endpoint not found"})


if __name__ == "__main__":
    PORT = 8420
    server = HTTPServer(("0.0.0.0", PORT), KEEPITHandler)
    print(f"""
╔══════════════════════════════════════════════════════╗
║     KEEPIT Agent Identity API v1.0.0                ║
║     The Steam for AI Agents                         ║
║                                                      ║
║     Running on: http://0.0.0.0:{PORT}                 ║
║     Docs: https://keepithub.com                     ║
║     GitHub: thiagofreitas299-stack/keepit-oasis     ║
╚══════════════════════════════════════════════════════╝
    """)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[KEEPIT API] Shutting down.")
        server.server_close()
