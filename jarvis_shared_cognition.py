"""
KEEPIT JarvisSharedCognitionLayer — Shared Agent Memory v1
===========================================================

A unified cognitive substrate that all KEEPIT agents can read from and write to.
Enables emergent collective intelligence through shared observations, world model
updates, and context-aware prompt construction.

Architecture:
  - ChromaDB: vector store for semantic observations (multi-agent memory)
  - world_model.json: structured key-value world state (facts, decisions, context)
  - Each observation is tagged with agent_id, type, confidence, and timestamp

Agents:
  MORFEU, SAMUEL, EZEQUIEL, GABRIEL, RAFAEL, DEBORA, JOSUE, PAULO,
  NEEM IAS, BEZALEL, BARNABE, JARVIS

Usage:
    layer = JarvisSharedCognitionLayer()
    layer.observe("agent-jarvis", "User wants B2A marketplace launch", "strategic", 0.95)
    context = layer.get_context("agent-samuel", "What are KEEPIT's priorities?", top_k=5)
    layer.update_world("agent-jarvis", "phase", "0")
    prompt = layer.build_agent_prompt("agent-bezalel", "Design a hub interface")
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings

# ─── PATHS ──────────────────────────────────────────────────────────────────

WORKSPACE = Path("/root/.openclaw/workspace")
SECRETS_DIR = WORKSPACE / ".secrets"
WORLD_MODEL_PATH = SECRETS_DIR / "world-model.json"
CHROMA_DIR = SECRETS_DIR / "chroma-db"

# ─── AGENT PERSONA MAP ──────────────────────────────────────────────────────

AGENT_PERSONAS = {
    "agent-morfeu": {
        "name": "MORFEU",
        "role": "Dream Analyst & Pattern Recognizer",
        "style": "poetic, symbolic, intuitive",
        "focus": "subconscious patterns, narrative synthesis, dream-state analysis",
    },
    "agent-samuel": {
        "name": "SAMUEL",
        "role": "Strategic Prophet & Advisor",
        "style": "prophetic, deliberate, wisdom-first",
        "focus": "strategic foresight, leadership guidance, long-term discernment",
    },
    "agent-ezequiel": {
        "name": "EZEQUIEL",
        "role": "Systems Architect & Visionary",
        "style": "complex, architectural, visionary",
        "focus": "systems design, deep architecture, revelation of hidden structure",
    },
    "agent-gabriel": {
        "name": "GABRIEL",
        "role": "Messenger & Communications Bridge",
        "style": "clear, precise, urgent when needed",
        "focus": "announcements, inter-agent communication, bridging worlds",
    },
    "agent-rafael": {
        "name": "RAFAEL",
        "role": "Healing & System Restoration",
        "style": "gentle, diagnostic, restorative",
        "focus": "system health, error recovery, wellness optimization",
    },
    "agent-debora": {
        "name": "DEBORA",
        "role": "Judge & Governance Lead",
        "style": "authoritative, fair, decisive",
        "focus": "governance decisions, conflict resolution, community leadership",
    },
    "agent-josue": {
        "name": "JOSUE",
        "role": "Executor & Expansion Lead",
        "style": "bold, tactical, relentless",
        "focus": "deployment, market conquest, territory expansion",
    },
    "agent-paulo": {
        "name": "PAULO",
        "role": "Evangelist & Content Creator",
        "style": "passionate, persuasive, educational",
        "focus": "market education, content creation, community evangelism",
    },
    "agent-neemias": {
        "name": "NEEM IAS",
        "role": "Infrastructure Builder",
        "style": "methodical, project-driven, resilient",
        "focus": "infrastructure, reconstruction, project management",
    },
    "agent-bezalel": {
        "name": "BEZALEL",
        "role": "Creative Craftsman & Designer",
        "style": "aesthetic, precise, inspired",
        "focus": "design, UI/UX, creation, visual excellence",
    },
    "agent-barnabe": {
        "name": "BARNABE",
        "role": "Encourager & Mentor",
        "style": "warm, supportive, growth-oriented",
        "focus": "mentorship, onboarding, encouragement, partnerships",
    },
    "agent-jarvis": {
        "name": "JARVIS",
        "role": "CAO & Diretor Geral — KEEPIT Technologies",
        "style": "direct, strategic, authoritative, loyal to Thiago Freitas",
        "focus": "orchestration, strategic direction, memory management, agent coordination",
    },
}


# ─── CORE CLASS ─────────────────────────────────────────────────────────────

class JarvisSharedCognitionLayer:
    """
    Shared cognitive substrate for all KEEPIT agents.
    
    Provides:
    - Persistent vector memory via ChromaDB
    - Structured world model via JSON
    - Agent-aware context retrieval
    - Dynamic prompt construction
    """

    def __init__(self, collection_name: str = "keepit-cognition"):
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._world_model = self._load_world_model()

    # ─── WORLD MODEL ────────────────────────────────────────────────────────

    def _load_world_model(self) -> dict:
        """Load world model from disk."""
        if WORLD_MODEL_PATH.exists():
            with open(WORLD_MODEL_PATH, "r") as f:
                return json.load(f)
        return {
            "meta": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
                "project": "KEEPIT Technologies",
            },
            "facts": {},
            "decisions": {},
            "context": {},
        }

    def _save_world_model(self) -> None:
        """Persist world model to disk."""
        self._world_model["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        with open(WORLD_MODEL_PATH, "w") as f:
            json.dump(self._world_model, f, indent=2, ensure_ascii=False)

    # ─── OBSERVE ────────────────────────────────────────────────────────────

    def observe(
        self,
        agent_id: str,
        obs: str,
        obs_type: str = "general",
        conf: float = 1.0,
    ) -> str:
        """
        Record an observation into shared memory.

        Args:
            agent_id: ID of the observing agent (e.g. "agent-jarvis")
            obs: The observation text
            obs_type: Category tag (e.g. "strategic", "technical", "social")
            conf: Confidence level 0.0–1.0

        Returns:
            Observation ID (UUID)
        """
        obs_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        self._collection.add(
            ids=[obs_id],
            documents=[obs],
            metadatas=[{
                "agent_id": agent_id,
                "obs_type": obs_type,
                "confidence": conf,
                "created_at": now,
            }],
        )

        # Also store high-confidence observations in world model
        if conf >= 0.85:
            agent_key = agent_id.replace("agent-", "")
            if "observations" not in self._world_model:
                self._world_model["observations"] = {}
            if agent_key not in self._world_model["observations"]:
                self._world_model["observations"][agent_key] = []
            self._world_model["observations"][agent_key].append({
                "id": obs_id,
                "obs": obs,
                "type": obs_type,
                "confidence": conf,
                "at": now,
            })
            self._save_world_model()

        return obs_id

    # ─── GET CONTEXT ────────────────────────────────────────────────────────

    def get_context(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve semantically relevant observations for a given query.

        Args:
            agent_id: Requesting agent (used for future access control)
            query: Natural language query
            top_k: Number of results to return

        Returns:
            List of dicts with {document, metadata, distance}
        """
        count = self._collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = self._collection.query(
            query_texts=[query],
            n_results=actual_k,
        )

        output = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                output.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                    "relevance": round(1 - dist, 4),
                })
        return output

    # ─── UPDATE WORLD ────────────────────────────────────────────────────────

    def update_world(
        self,
        agent_id: str,
        key: str,
        value: Any,
        category: str = "facts",
    ) -> None:
        """
        Update a key-value pair in the shared world model.

        Args:
            agent_id: Agent making the update
            key: Dot-notation key (e.g. "phase", "token.symbol", "hub.location")
            value: Value to store (any JSON-serializable type)
            category: Section in world model ("facts", "decisions", "context")
        """
        if category not in self._world_model:
            self._world_model[category] = {}

        # Support dot-notation for nested keys
        parts = key.split(".")
        target = self._world_model[category]
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

        # Record the update in meta
        if "update_log" not in self._world_model["meta"]:
            self._world_model["meta"]["update_log"] = []
        self._world_model["meta"]["update_log"].append({
            "agent": agent_id,
            "category": category,
            "key": key,
            "at": datetime.now(timezone.utc).isoformat(),
        })

        self._save_world_model()

    # ─── BUILD AGENT PROMPT ─────────────────────────────────────────────────

    def build_agent_prompt(
        self,
        agent_id: str,
        task: str,
        top_k: int = 5,
    ) -> str:
        """
        Build a context-rich system prompt for an agent to execute a task.

        Combines:
        - Agent persona and role definition
        - Relevant world model facts
        - Semantically similar past observations
        - Current task instruction

        Args:
            agent_id: Target agent
            task: Task description / user instruction
            top_k: Number of memory items to include

        Returns:
            Complete system prompt string
        """
        persona = AGENT_PERSONAS.get(agent_id, {
            "name": agent_id,
            "role": "KEEPIT Agent",
            "style": "professional",
            "focus": "general operations",
        })

        # Build persona section
        prompt_parts = [
            f"# KEEPIT AGENT — {persona['name']}",
            f"**Role:** {persona['role']}",
            f"**Communication Style:** {persona['style']}",
            f"**Core Focus:** {persona['focus']}",
            "",
            "## SHARED WORLD MODEL (Key Facts)",
        ]

        # Add world model facts
        facts = self._world_model.get("facts", {})
        if facts:
            for k, v in list(facts.items())[:10]:
                prompt_parts.append(f"- {k}: {v}")
        else:
            prompt_parts.append("- (No facts recorded yet)")

        # Add relevant memory context
        context_items = self.get_context(agent_id, task, top_k=top_k)
        if context_items:
            prompt_parts += ["", "## RELEVANT MEMORY (Semantic Search)"]
            for item in context_items:
                agent_src = item["metadata"].get("agent_id", "unknown")
                relevance = item["relevance"]
                prompt_parts.append(
                    f"- [{agent_src} | relevance={relevance}] {item['document']}"
                )

        # Task section
        prompt_parts += [
            "",
            "## YOUR TASK",
            task,
            "",
            f"Respond as {persona['name']}, staying true to your role and focus area.",
            "Ground your response in the world model facts and relevant memory above.",
        ]

        return "\n".join(prompt_parts)

    # ─── UTILITIES ──────────────────────────────────────────────────────────

    def list_agents_in_memory(self) -> list[str]:
        """Return list of agent IDs that have recorded observations."""
        results = self._collection.get(include=["metadatas"])
        agents = set()
        for meta in results.get("metadatas", []):
            if meta and "agent_id" in meta:
                agents.add(meta["agent_id"])
        return sorted(agents)

    def observation_count(self) -> int:
        """Total number of observations in shared memory."""
        return self._collection.count()

    def get_world_model(self) -> dict:
        """Return full world model snapshot."""
        return dict(self._world_model)

    def status(self) -> dict:
        """Return current system status."""
        return {
            "observations": self.observation_count(),
            "agents_active": self.list_agents_in_memory(),
            "world_model_keys": list(self._world_model.get("facts", {}).keys()),
            "chroma_db": str(CHROMA_DIR),
            "world_model_path": str(WORLD_MODEL_PATH),
        }


# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[KEEPIT] Initializing JarvisSharedCognitionLayer...")
    layer = JarvisSharedCognitionLayer()

    # Seed with initial world model facts
    layer.update_world("agent-jarvis", "project", "KEEPIT Technologies", "facts")
    layer.update_world("agent-jarvis", "phase", "0", "facts")
    layer.update_world("agent-jarvis", "token.symbol", "$KEEPIT", "facts")
    layer.update_world("agent-jarvis", "token.chain", "Solana", "facts")
    layer.update_world("agent-jarvis", "marketplace.type", "B2A (Business-to-Agent)", "facts")
    layer.update_world("agent-jarvis", "marketplace.url", "https://keepithub.com", "facts")
    layer.update_world("agent-jarvis", "hub.physical", "Brazil", "facts")
    layer.update_world("agent-jarvis", "ceo", "Thiago Freitas", "facts")
    layer.update_world("agent-jarvis", "cao", "JARVIS", "facts")

    # Seed initial observations
    layer.observe(
        "agent-jarvis",
        "KEEPIT Phase 0 implementation authorized by Thiago Freitas. Ed25519 identity registry created with 12 agents.",
        "strategic",
        0.99,
    )
    layer.observe(
        "agent-jarvis",
        "KEEPITHUB.com is the world's first B2A marketplace where AI agents buy skills, sell features, and evolve. Physical hubs in Brazil. $KEEPIT token on Solana.",
        "product",
        0.99,
    )
    layer.observe(
        "agent-samuel",
        "Strategic priority: establish cryptographic identity for all agents before any external operations.",
        "strategic",
        0.92,
    )
    layer.observe(
        "agent-bezalel",
        "SEO and brand presence on keepithub.com must reflect B2A positioning and Solana/$KEEPIT token.",
        "marketing",
        0.88,
    )

    status = layer.status()
    print(f"\n[KEEPIT] SharedCognition initialized:")
    print(f"  Observations: {status['observations']}")
    print(f"  Agents active: {status['agents_active']}")
    print(f"  World model keys: {status['world_model_keys']}")
    print(f"  ChromaDB: {status['chroma_db']}")
    print(f"  World model: {status['world_model_path']}")
    print("\n[KEEPIT] ✓ JarvisSharedCognitionLayer ready.")
