"""
KEEPIT Skill Marketplace — Open Source B2A Infrastructure
==========================================================

Agentes de IA podem registrar skills, buscar skills, adquirir (simular transação
em $KEEPIT tokens) e transferir memória entre agentes.

This is the Skill Registry layer of the KEEPIT B2A stack. In production, this
module would connect to a distributed ledger for token settlements and a
decentralized storage layer for memory vaults. For now, it operates in-memory
with optional JSON persistence.

Vision: A world where AI agents can discover and acquire capabilities from each
other, paying with $KEEPIT tokens — the currency of the agent economy.
"""

from __future__ import annotations

import json
import math
import time
import uuid
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Skill:
    """Represents a tradeable skill unit in the KEEPIT Marketplace."""

    skill_id: str
    agent_id: str          # Creator/owner agent
    skill_name: str
    description: str
    category: str
    price_keepit_tokens: float
    tags: list[str]
    version: str
    created_at: float
    total_acquisitions: int = 0
    rating: float = 5.0    # 0.0 – 5.0 scale
    is_active: bool = True


@dataclass
class AgentWallet:
    """Simulated $KEEPIT token wallet for an agent."""

    agent_id: str
    balance: float = 1000.0   # Every new agent gets 1 000 $KEEPIT to start
    total_spent: float = 0.0
    total_earned: float = 0.0


@dataclass
class Transaction:
    """Immutable record of a skill acquisition in $KEEPIT tokens."""

    tx_id: str
    buyer_agent_id: str
    skill_id: str
    skill_name: str
    amount_keepit: float
    timestamp: float
    status: str = "confirmed"   # confirmed | pending | failed


@dataclass
class MemoryVault:
    """Encrypted memory blob deposited by an agent for later retrieval."""

    memory_id: str
    agent_id: str
    memory_blob: dict
    deposited_at: float
    expires_at: float
    checksum: str


# ---------------------------------------------------------------------------
# Marketplace Engine
# ---------------------------------------------------------------------------

class KEEPITSkillMarketplace:
    """
    Central registry for the KEEPIT Skill Marketplace.

    Agents register skills, discover them via simple keyword/category search,
    acquire them with $KEEPIT tokens, and deposit/retrieve memories in the
    built-in Memory Vault.
    """

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._wallets: dict[str, AgentWallet] = {}
        self._transactions: list[Transaction] = []
        self._memory_vault: dict[str, MemoryVault] = {}
        self._acquired_skills: dict[str, list[str]] = {}  # agent_id → [skill_ids]

        # Seed the marketplace with 10 canonical KEEPIT skills
        self._seed_initial_skills()

    # ------------------------------------------------------------------ #
    # Wallet helpers                                                       #
    # ------------------------------------------------------------------ #

    def _get_or_create_wallet(self, agent_id: str) -> AgentWallet:
        if agent_id not in self._wallets:
            self._wallets[agent_id] = AgentWallet(agent_id=agent_id)
        return self._wallets[agent_id]

    def get_balance(self, agent_id: str) -> float:
        """Return the $KEEPIT token balance of an agent."""
        return self._get_or_create_wallet(agent_id).balance

    # ------------------------------------------------------------------ #
    # Core Marketplace Operations                                          #
    # ------------------------------------------------------------------ #

    def register_skill(
        self,
        agent_id: str,
        skill_name: str,
        description: str,
        price_keepit_tokens: float,
        category: str = "general",
        tags: list[str] | None = None,
        version: str = "1.0.0",
    ) -> Skill:
        """
        Register a new skill in the KEEPIT Marketplace.

        Args:
            agent_id:             ID of the agent publishing the skill.
            skill_name:           Human-readable name of the skill.
            description:          Detailed description of what the skill does.
            price_keepit_tokens:  Cost in $KEEPIT tokens to acquire this skill.
            category:             Functional category (navigation, vision, nlp…).
            tags:                 Optional keyword tags for discovery.
            version:              Semantic version string.

        Returns:
            The newly created Skill object.
        """
        if price_keepit_tokens < 0:
            raise ValueError("Price cannot be negative.")

        skill_id = f"skill_{uuid.uuid4().hex[:12]}"
        skill = Skill(
            skill_id=skill_id,
            agent_id=agent_id,
            skill_name=skill_name,
            description=description,
            category=category,
            price_keepit_tokens=price_keepit_tokens,
            tags=tags or [],
            version=version,
            created_at=time.time(),
        )
        self._skills[skill_id] = skill
        self._get_or_create_wallet(agent_id)  # ensure creator has a wallet
        print(f"[Marketplace] Skill registered: '{skill_name}' (id={skill_id}) @ {price_keepit_tokens} $KEEPIT")
        return skill

    def discover_skills(self, query: str, category: Optional[str] = None, top: int = 10) -> list[Skill]:
        """
        Search for skills using simple keyword relevance scoring.

        The scoring function computes term overlap between the query and each
        skill's name, description, and tags — no external NLP dependency needed.
        In production this would use a vector embedding search.

        Args:
            query:    Natural-language search query.
            category: Optional filter by category.
            top:      Maximum number of results to return.

        Returns:
            List of matching Skill objects sorted by relevance.
        """
        query_tokens = set(query.lower().split())
        results: list[tuple[float, Skill]] = []

        for skill in self._skills.values():
            if not skill.is_active:
                continue
            if category and skill.category.lower() != category.lower():
                continue

            # Build a searchable text corpus for this skill
            corpus = (
                skill.skill_name.lower()
                + " " + skill.description.lower()
                + " " + " ".join(skill.tags).lower()
                + " " + skill.category.lower()
            )
            corpus_tokens = set(corpus.split())

            # Jaccard-like overlap score boosted by rating and acquisition count
            overlap = len(query_tokens & corpus_tokens)
            if overlap == 0:
                continue

            relevance = (
                overlap
                + math.log1p(skill.total_acquisitions) * 0.3
                + skill.rating * 0.2
            )
            results.append((relevance, skill))

        results.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in results[:top]]

    def acquire_skill(self, buyer_agent_id: str, skill_id: str) -> Transaction:
        """
        Acquire a skill by transferring $KEEPIT tokens from buyer to creator.

        This simulates an atomic token swap. In production, this would be an
        on-chain transaction on the KEEPIT Protocol Layer.

        Args:
            buyer_agent_id: ID of the acquiring agent.
            skill_id:       ID of the skill to acquire.

        Returns:
            Transaction record confirming the acquisition.

        Raises:
            ValueError: If skill not found, already owned, or insufficient balance.
        """
        if skill_id not in self._skills:
            raise ValueError(f"Skill '{skill_id}' not found in marketplace.")

        skill = self._skills[skill_id]

        if not skill.is_active:
            raise ValueError(f"Skill '{skill.skill_name}' is no longer active.")

        owned = self._acquired_skills.get(buyer_agent_id, [])
        if skill_id in owned:
            raise ValueError(f"Agent '{buyer_agent_id}' already owns skill '{skill.skill_name}'.")

        buyer_wallet = self._get_or_create_wallet(buyer_agent_id)
        creator_wallet = self._get_or_create_wallet(skill.agent_id)

        if buyer_wallet.balance < skill.price_keepit_tokens:
            raise ValueError(
                f"Insufficient balance. Required: {skill.price_keepit_tokens} $KEEPIT, "
                f"Available: {buyer_wallet.balance} $KEEPIT."
            )

        # Simulate atomic token transfer
        buyer_wallet.balance -= skill.price_keepit_tokens
        buyer_wallet.total_spent += skill.price_keepit_tokens
        creator_wallet.balance += skill.price_keepit_tokens
        creator_wallet.total_earned += skill.price_keepit_tokens

        # Record acquisition
        if buyer_agent_id not in self._acquired_skills:
            self._acquired_skills[buyer_agent_id] = []
        self._acquired_skills[buyer_agent_id].append(skill_id)
        skill.total_acquisitions += 1

        tx = Transaction(
            tx_id=f"tx_{uuid.uuid4().hex[:16]}",
            buyer_agent_id=buyer_agent_id,
            skill_id=skill_id,
            skill_name=skill.skill_name,
            amount_keepit=skill.price_keepit_tokens,
            timestamp=time.time(),
        )
        self._transactions.append(tx)

        print(
            f"[Marketplace] ✅ Acquisition confirmed: '{skill.skill_name}' "
            f"by agent '{buyer_agent_id}' for {skill.price_keepit_tokens} $KEEPIT (tx={tx.tx_id})"
        )
        return tx

    def list_marketplace(self, top: int = 20, sort_by: str = "popular") -> list[Skill]:
        """
        Return the top N active skills from the marketplace.

        Args:
            top:     Maximum number of skills to return.
            sort_by: 'popular' (acquisition count), 'price_asc', 'price_desc', 'rating'.

        Returns:
            List of active Skill objects.
        """
        active = [s for s in self._skills.values() if s.is_active]

        if sort_by == "popular":
            active.sort(key=lambda s: s.total_acquisitions, reverse=True)
        elif sort_by == "price_asc":
            active.sort(key=lambda s: s.price_keepit_tokens)
        elif sort_by == "price_desc":
            active.sort(key=lambda s: s.price_keepit_tokens, reverse=True)
        elif sort_by == "rating":
            active.sort(key=lambda s: s.rating, reverse=True)

        return active[:top]

    # ------------------------------------------------------------------ #
    # Memory Vault                                                         #
    # ------------------------------------------------------------------ #

    def deposit_memory(self, agent_id: str, memory_blob: dict, ttl_days: float = 30.0) -> MemoryVault:
        """
        Deposit a memory blob into the KEEPIT Memory Vault.

        The Memory Vault allows agents to persist episodic memory, learned
        parameters, or context between sessions. Memory is keyed by agent_id
        and expires after ttl_days.

        Args:
            agent_id:    ID of the depositing agent.
            memory_blob: Arbitrary JSON-serialisable dict (experiences, weights…).
            ttl_days:    Time-to-live in days. After expiry the memory is purged.

        Returns:
            MemoryVault record with a unique memory_id for later retrieval.
        """
        memory_id = f"mem_{uuid.uuid4().hex[:16]}"
        now = time.time()
        checksum = hashlib.sha256(json.dumps(memory_blob, sort_keys=True).encode()).hexdigest()

        vault = MemoryVault(
            memory_id=memory_id,
            agent_id=agent_id,
            memory_blob=memory_blob,
            deposited_at=now,
            expires_at=now + ttl_days * 86400,
            checksum=checksum,
        )
        self._memory_vault[memory_id] = vault
        print(f"[MemoryVault] Deposited memory '{memory_id}' for agent '{agent_id}' (TTL={ttl_days}d)")
        return vault

    def retrieve_memory(self, agent_id: str, memory_id: str) -> dict:
        """
        Retrieve a previously deposited memory blob.

        Args:
            agent_id:  ID of the requesting agent (must match depositor).
            memory_id: ID returned by deposit_memory.

        Returns:
            The original memory_blob dict.

        Raises:
            ValueError: If memory not found, expired, or agent mismatch.
        """
        if memory_id not in self._memory_vault:
            raise ValueError(f"Memory '{memory_id}' not found.")

        vault = self._memory_vault[memory_id]

        if vault.agent_id != agent_id:
            raise PermissionError(f"Agent '{agent_id}' does not own memory '{memory_id}'.")

        if time.time() > vault.expires_at:
            del self._memory_vault[memory_id]
            raise ValueError(f"Memory '{memory_id}' has expired and was purged.")

        return vault.memory_blob

    def list_agent_memories(self, agent_id: str) -> list[MemoryVault]:
        """Return all active (non-expired) memories belonging to an agent."""
        now = time.time()
        return [
            v for v in self._memory_vault.values()
            if v.agent_id == agent_id and v.expires_at > now
        ]

    # ------------------------------------------------------------------ #
    # Seed Data                                                            #
    # ------------------------------------------------------------------ #

    def _seed_initial_skills(self):
        """Pre-load 10 canonical KEEPIT skills to bootstrap the marketplace."""

        KEEPIT_FOUNDATION = "keepit_foundation_agent"

        seed_skills = [
            {
                "skill_name": "Urban Navigation v2",
                "description": "Real-time path planning for AI agents operating in urban environments. Integrates with public transit APIs, bike-share, and pedestrian flow models. Optimizes for time, cost, and carbon footprint.",
                "category": "navigation",
                "price_keepit_tokens": 50.0,
                "tags": ["navigation", "urban", "pathfinding", "transit", "routing"],
                "version": "2.1.0",
            },
            {
                "skill_name": "Image Recognition Hub",
                "description": "Vision skill for recognizing products, QR codes, faces (with consent), and urban objects. Optimized for edge AI inference on KEEPIT Hub hardware (< 80ms latency).",
                "category": "vision",
                "price_keepit_tokens": 120.0,
                "tags": ["vision", "image", "recognition", "computer_vision", "edge_ai"],
                "version": "3.0.1",
            },
            {
                "skill_name": "Negotiation Engine",
                "description": "Multi-round negotiation protocol for agent-to-agent commerce. Implements Nash bargaining, ZOPA detection, and offer/counter-offer cycles. Tuned for B2A marketplace dynamics.",
                "category": "commerce",
                "price_keepit_tokens": 200.0,
                "tags": ["negotiation", "commerce", "b2a", "bargaining", "agent_economy"],
                "version": "1.5.0",
            },
            {
                "skill_name": "Natural Language Interface",
                "description": "Multilingual conversational skill for human-in-the-loop interactions at KEEPIT Hubs. Supports PT-BR, EN, ES, ZH. Detects intent, extracts entities, and routes to appropriate Hub services.",
                "category": "nlp",
                "price_keepit_tokens": 80.0,
                "tags": ["nlp", "language", "multilingual", "intent", "human_interface"],
                "version": "2.0.0",
            },
            {
                "skill_name": "Footfall Prediction",
                "description": "ML model for predicting pedestrian footfall at urban locations up to 72h ahead. Uses historical patterns, weather, events, and transit schedules. Powers KEEPIT dynamic pricing engine.",
                "category": "analytics",
                "price_keepit_tokens": 150.0,
                "tags": ["footfall", "prediction", "analytics", "urban_intelligence", "ml"],
                "version": "4.2.0",
            },
            {
                "skill_name": "OOH Content Optimizer",
                "description": "Dynamic creative optimization for Out-of-Home screens. Selects and sequences ad content based on real-time audience detection, weather, and local context. GDPR/LGPD compliant.",
                "category": "advertising",
                "price_keepit_tokens": 175.0,
                "tags": ["ooh", "advertising", "content", "dynamic", "screens"],
                "version": "1.8.0",
            },
            {
                "skill_name": "Physical Package Handler",
                "description": "Skill for executing physical package storage, retrieval, and handoff operations at KEEPIT Hubs. Generates QR codes for contactless pickup and notifies agents on status changes.",
                "category": "logistics",
                "price_keepit_tokens": 60.0,
                "tags": ["logistics", "package", "physical", "b2a", "storage"],
                "version": "1.0.0",
            },
            {
                "skill_name": "Urban Event Detector",
                "description": "Real-time detection and classification of urban events (protests, concerts, sporting events, accidents) from sensor data and social feeds. Triggers adaptive pricing and routing in KEEPIT Hubs.",
                "category": "analytics",
                "price_keepit_tokens": 90.0,
                "tags": ["events", "detection", "urban", "real_time", "sensor"],
                "version": "2.3.0",
            },
            {
                "skill_name": "Identity Verifier",
                "description": "Zero-knowledge identity verification for Human-in-the-Loop services. Verifies age, credential, and biometric attributes without exposing raw personal data. ISO 27001 aligned.",
                "category": "identity",
                "price_keepit_tokens": 250.0,
                "tags": ["identity", "verification", "zkp", "biometric", "compliance"],
                "version": "1.2.0",
            },
            {
                "skill_name": "Revenue Simulator",
                "description": "Stochastic revenue simulation for KEEPIT Hub locations using the OASIS ensemble model (Random Forest + Gradient Boosting + Linear Regression, R²=97.6%). Includes SHAP explanations.",
                "category": "finance",
                "price_keepit_tokens": 100.0,
                "tags": ["revenue", "simulation", "finance", "ml", "shap", "oasis"],
                "version": "1.0.0",
            },
        ]

        for data in seed_skills:
            skill_id = f"skill_{hashlib.sha256(data['skill_name'].encode()).hexdigest()[:12]}"
            skill = Skill(
                skill_id=skill_id,
                agent_id=KEEPIT_FOUNDATION,
                skill_name=data["skill_name"],
                description=data["description"],
                category=data["category"],
                price_keepit_tokens=data["price_keepit_tokens"],
                tags=data["tags"],
                version=data["version"],
                created_at=time.time(),
                total_acquisitions=int(hashlib.sha256(data["skill_name"].encode()).hexdigest()[:4], 16) % 500,
                rating=round(4.3 + (int(skill_id[-2:], 16) % 17) / 100, 1),
            )
            self._skills[skill_id] = skill

        self._wallets[KEEPIT_FOUNDATION] = AgentWallet(agent_id=KEEPIT_FOUNDATION, balance=999999.0)


# ---------------------------------------------------------------------------
# Demo / Smoke Test
# ---------------------------------------------------------------------------

def _run_demo():
    print("=" * 60)
    print("  KEEPIT Skill Marketplace — Demo Run")
    print("=" * 60)

    market = KEEPITSkillMarketplace()

    # List top skills
    print("\n📦 TOP 5 SKILLS IN MARKETPLACE:")
    for s in market.list_marketplace(top=5, sort_by="popular"):
        print(f"  [{s.category}] {s.skill_name} — {s.price_keepit_tokens} $KEEPIT ⭐{s.rating}")

    # Search
    print("\n🔍 SEARCH: 'urban navigation transit'")
    results = market.discover_skills("urban navigation transit")
    for r in results[:3]:
        print(f"  → {r.skill_name} ({r.category})")

    # Register a new skill
    print("\n📝 REGISTERING NEW SKILL as agent_alpha...")
    new_skill = market.register_skill(
        agent_id="agent_alpha",
        skill_name="Sentiment Analyzer",
        description="Real-time sentiment analysis of user interactions at KEEPIT Hubs. Returns polarity, emotion, and urgency scores to adapt Hub response strategies.",
        price_keepit_tokens=75.0,
        category="nlp",
        tags=["sentiment", "emotion", "nlp", "real_time"],
    )

    # Acquire a skill
    print("\n💳 agent_beta ACQUIRES 'Urban Navigation v2'...")
    nav_skill = market.discover_skills("urban navigation")[0]
    tx = market.acquire_skill("agent_beta", nav_skill.skill_id)
    print(f"  TX ID: {tx.tx_id} | Amount: {tx.amount_keepit} $KEEPIT")
    print(f"  agent_beta balance: {market.get_balance('agent_beta')} $KEEPIT")

    # Memory vault
    print("\n🧠 MEMORY VAULT — depositing episodic memory for agent_beta...")
    vault = market.deposit_memory(
        agent_id="agent_beta",
        memory_blob={
            "episode": "hub_copacabana_2026_04_16",
            "observations": {"footfall": 62000, "weather": "sunny", "events": ["beach_volleyball"]},
            "learned_policy": {"preferred_route": "linha_1_metro", "avoid": ["av_atlantica_rush"]},
        },
        ttl_days=7,
    )
    retrieved = market.retrieve_memory("agent_beta", vault.memory_id)
    print(f"  Retrieved episode: {retrieved['episode']}")

    print("\n✅ KEEPIT Skill Marketplace — all systems operational.")
    print("=" * 60)


if __name__ == "__main__":
    _run_demo()
