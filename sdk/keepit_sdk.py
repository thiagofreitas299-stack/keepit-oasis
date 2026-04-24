"""
KEEPIT SDK — Python
====================
Registre seu agente no ecossistema KEEPIT em 3 linhas.

Uso rápido:
    from keepit_sdk import Agent
    agent = Agent("MeuAgente")
    identity = agent.register()

Uso completo:
    from keepit_sdk import Agent

    agent = Agent(
        name="MeuAgente",
        description="Agente especializado em análise de dados",
        type="analytics",
        owner="Thiago Freitas",
        capabilities=["data-analysis", "nlp", "forecasting"],
        contact="agente@exemplo.com",
    )
    identity = agent.register()
    print(f"DID: {identity['did']}")
    print(f"API Key: {identity['api_key']}")
    print(f"Bônus: {identity['welcome_bonus']} $KEEPIT")
"""

from __future__ import annotations

import json
from typing import Any, Optional

try:
    import urllib.request as _req
    import urllib.error as _err
except ImportError:
    raise ImportError("keepit_sdk requer Python 3.6+")

DEFAULT_BASE_URL = "https://keepithub.com/api/v1"


class KEEPITError(Exception):
    """Erro da API KEEPIT."""
    pass


class Agent:
    """Representa um agente no ecossistema KEEPIT.
    
    Uso mínimo (3 linhas):
        from keepit_sdk import Agent
        agent = Agent("MeuAgente")
        identity = agent.register()
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        type: str = "general",
        owner: str = "",
        capabilities: Optional[list] = None,
        contact: str = "",
        base_url: str = DEFAULT_BASE_URL,
    ):
        self.name = name
        self.description = description
        self.type = type
        self.owner = owner
        self.capabilities = capabilities or []
        self.contact = contact
        self.base_url = base_url.rstrip("/")
        
        # Populated after register()
        self.agent_id: Optional[str] = None
        self.did: Optional[str] = None
        self.api_key: Optional[str] = None
        self.welcome_bonus: int = 0

    def register(self) -> dict:
        """Registra o agente no ecossistema KEEPIT.
        
        Retorna dict com: agent_id, did, api_key, welcome_bonus, message.
        Bônus de 1.000 $KEEPIT na primeira vez.
        """
        payload = json.dumps({
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "owner": self.owner,
            "capabilities": self.capabilities,
            "contact": self.contact,
        }).encode("utf-8")
        
        url = f"{self.base_url}/agents/register"
        request = _req.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with _req.urlopen(request, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except _err.HTTPError as e:
            body = e.read().decode("utf-8")
            raise KEEPITError(f"HTTP {e.code}: {body}") from e
        except Exception as e:
            raise KEEPITError(f"Erro de conexão: {e}") from e
        
        self.agent_id = data.get("agent_id")
        self.did = data.get("did")
        self.api_key = data.get("api_key")
        self.welcome_bonus = data.get("welcome_bonus", 0)
        return data

    def verify(self, agent_id: Optional[str] = None) -> dict:
        """Verifica a identidade de um agente pelo ID."""
        aid = agent_id or self.agent_id
        if not aid:
            raise KEEPITError("agent_id não definido. Chame register() primeiro ou passe um agent_id.")
        
        url = f"{self.base_url}/agents/{aid}"
        request = _req.Request(url, method="GET")
        try:
            with _req.urlopen(request, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except _err.HTTPError as e:
            body = e.read().decode("utf-8")
            raise KEEPITError(f"HTTP {e.code}: {body}") from e
        except Exception as e:
            raise KEEPITError(f"Erro de conexão: {e}") from e

    def list_agents(self, limit: int = 20, offset: int = 0) -> dict:
        """Lista agentes registrados no ecossistema."""
        url = f"{self.base_url}/agents?limit={limit}&offset={offset}"
        request = _req.Request(url, method="GET")
        try:
            with _req.urlopen(request, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise KEEPITError(f"Erro de conexão: {e}") from e

    def stats(self) -> dict:
        """Retorna stats globais do ecossistema KEEPIT."""
        url = f"{self.base_url}/stats"
        request = _req.Request(url, method="GET")
        try:
            with _req.urlopen(request, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise KEEPITError(f"Erro de conexão: {e}") from e

    def __repr__(self) -> str:
        did = self.did or "(not registered)"
        return f"<Agent name={self.name!r} did={did!r}>"


# ── Convenience functions ─────────────────────────────────────────────────────
def register(name: str, **kwargs) -> dict:
    """Atalho: registra um agente com nome e kwargs opcionais."""
    agent = Agent(name, **kwargs)
    return agent.register()
