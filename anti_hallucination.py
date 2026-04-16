"""
KEEPIT Anti-Hallucination Layer
================================
KEEPIT Hubs act as grounding infrastructure for AI agents,
preventing hallucinations through verified memory retrieval.

Physical Hubs continuously ingest, verify, and serve real-world data
that no purely digital system can replicate — making KEEPIT the trust
layer every production AI agent needs.

Architecture:
    AI Agent Query
        ↓
    KEEPIT Hub (physical grounding node)
        ↓
    Verified Memory Vault
        ↓
    ground_response() / moderate_agent_output()
        ↓
    Grounded, trustworthy agent response
"""

from __future__ import annotations

import re
import time
import hashlib
import datetime
from typing import Any


# ─────────────────────────────────────────────
# In-memory stores (replace with real DB/Hub API in production)
# ─────────────────────────────────────────────

_VERIFIED_FACTS: dict[str, dict] = {}   # fact_id → fact record
_HUB_INDEX: dict[str, list[str]] = {}   # hub_id → [fact_ids]
_CATEGORY_INDEX: dict[str, list[str]] = {}  # category → [fact_ids]
_AGENT_REGISTRY: dict[str, dict] = {}   # agent_id → metadata


# ─────────────────────────────────────────────
# Seed data: 20 verified facts about Brazil
# ─────────────────────────────────────────────

_SEED_FACTS = [
    # Brazilian cities
    {
        "fact": "São Paulo is the most populous city in Brazil with approximately 12.3 million residents in the city proper.",
        "source": "IBGE Census 2022",
        "category": "geography",
        "hub_id": "hub-sao-paulo-01",
    },
    {
        "fact": "Rio de Janeiro's Carnival is held annually before Ash Wednesday and attracts over 5 million visitors.",
        "source": "Riotur Official Statistics 2023",
        "category": "culture",
        "hub_id": "hub-rio-01",
    },
    {
        "fact": "Brasília, the capital of Brazil, was inaugurated on April 21, 1960, designed by urban planner Lúcio Costa and architect Oscar Niemeyer.",
        "source": "Arquivo Nacional do Brasil",
        "category": "history",
        "hub_id": "hub-brasilia-01",
    },
    {
        "fact": "The Amazon River discharges approximately 20% of all fresh water flowing into the world's oceans.",
        "source": "INPA — National Institute for Amazonian Research",
        "category": "geography",
        "hub_id": "hub-amazon-01",
    },
    {
        "fact": "Manaus is the capital of Amazonas state and the largest city in the Amazon region, with a population of about 2.2 million.",
        "source": "IBGE Census 2022",
        "category": "geography",
        "hub_id": "hub-amazon-01",
    },
    # Economic data
    {
        "fact": "Brazil is the largest economy in Latin America and the 9th largest economy in the world by nominal GDP (2023).",
        "source": "World Bank, IMF World Economic Outlook 2023",
        "category": "economics",
        "hub_id": "hub-economy-01",
    },
    {
        "fact": "Brazil's GDP was approximately USD 2.13 trillion in 2023.",
        "source": "IMF World Economic Outlook April 2024",
        "category": "economics",
        "hub_id": "hub-economy-01",
    },
    {
        "fact": "The Brazilian Real (BRL) is the official currency of Brazil, introduced on July 1, 1994, replacing the Cruzeiro Real.",
        "source": "Banco Central do Brasil",
        "category": "economics",
        "hub_id": "hub-economy-01",
    },
    {
        "fact": "Brazil is the world's largest producer and exporter of coffee, accounting for roughly one-third of global production.",
        "source": "ABIC — Brazilian Coffee Industry Association 2023",
        "category": "economics",
        "hub_id": "hub-agriculture-01",
    },
    {
        "fact": "Brazil is the second-largest producer of soybeans globally, after the United States, harvesting over 154 million metric tons in 2022/23.",
        "source": "Embrapa / USDA Foreign Agricultural Service",
        "category": "economics",
        "hub_id": "hub-agriculture-01",
    },
    # Technology & infrastructure
    {
        "fact": "Brazil has the largest internet user base in Latin America with over 156 million users as of 2023.",
        "source": "DataReportal Digital 2023 Brazil Report",
        "category": "technology",
        "hub_id": "hub-tech-01",
    },
    {
        "fact": "PIX, Brazil's instant payment system launched by Banco Central in November 2020, processed over 42 billion transactions in 2023.",
        "source": "Banco Central do Brasil — PIX Statistics 2023",
        "category": "technology",
        "hub_id": "hub-tech-01",
    },
    {
        "fact": "Brazil has over 2,500 fintech companies, making it one of the top five fintech ecosystems in the world.",
        "source": "Distrito Fintech Report 2023",
        "category": "technology",
        "hub_id": "hub-tech-01",
    },
    # Demographics
    {
        "fact": "Brazil's total population is approximately 215 million people according to the 2022 IBGE census.",
        "source": "IBGE Census 2022",
        "category": "demographics",
        "hub_id": "hub-demographics-01",
    },
    {
        "fact": "Portuguese is the official and most widely spoken language in Brazil.",
        "source": "Brazilian Constitution, Art. 13",
        "category": "demographics",
        "hub_id": "hub-demographics-01",
    },
    {
        "fact": "Brazil has 27 federative units: 26 states and 1 federal district (Brasília).",
        "source": "Brazilian Constitution, Art. 18",
        "category": "geography",
        "hub_id": "hub-brasilia-01",
    },
    # Environment
    {
        "fact": "The Brazilian Amazon covers approximately 4.2 million km² and represents about 40% of the world's remaining tropical rainforest.",
        "source": "INPE — National Institute for Space Research, Brazil",
        "category": "environment",
        "hub_id": "hub-amazon-01",
    },
    {
        "fact": "Brazil generates approximately 83% of its electricity from renewable sources, primarily hydropower.",
        "source": "EPE — Empresa de Pesquisa Energética 2023",
        "category": "environment",
        "hub_id": "hub-energy-01",
    },
    # Sports & culture
    {
        "fact": "Brazil has won the FIFA World Cup five times: 1958, 1962, 1970, 1994, and 2002.",
        "source": "FIFA Official Records",
        "category": "culture",
        "hub_id": "hub-culture-01",
    },
    {
        "fact": "The Cristo Redentor (Christ the Redeemer) statue in Rio de Janeiro, inaugurated in 1931, stands 30 meters tall on Corcovado mountain.",
        "source": "UNESCO World Heritage Documentation",
        "category": "culture",
        "hub_id": "hub-rio-01",
    },
]


def _fact_id(fact: str, hub_id: str) -> str:
    """Generate a stable unique ID for a fact."""
    raw = f"{hub_id}:{fact[:80]}"
    return "fact_" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def _load_seed_data() -> None:
    """Load seed facts into the in-memory store."""
    for item in _SEED_FACTS:
        register_verified_fact(
            hub_id=item["hub_id"],
            fact=item["fact"],
            source=item["source"],
            category=item["category"],
        )


# ─────────────────────────────────────────────
# Core API
# ─────────────────────────────────────────────


def register_verified_fact(
    hub_id: str,
    fact: str,
    source: str,
    category: str,
) -> str:
    """
    Register a verified fact in the KEEPIT Hub.

    Physical Hubs continuously ingest real-world data (IoT sensors,
    local registries, on-site verification) and call this function
    to add facts to the grounding store.

    Args:
        hub_id:   The KEEPIT Hub that verified this fact.
        fact:     The factual statement (declarative sentence).
        source:   Authoritative source for verification.
        category: Semantic category (e.g. "geography", "economics").

    Returns:
        fact_id: Unique identifier of the registered fact.
    """
    fid = _fact_id(fact, hub_id)
    _VERIFIED_FACTS[fid] = {
        "fact_id": fid,
        "hub_id": hub_id,
        "fact": fact,
        "source": source,
        "category": category,
        "registered_at": datetime.datetime.utcnow().isoformat() + "Z",
        "verification_status": "hub_verified",
    }
    _HUB_INDEX.setdefault(hub_id, []).append(fid)
    _CATEGORY_INDEX.setdefault(category, []).append(fid)
    return fid


def query_verified_knowledge(
    query: str,
    hub_id: str | None = None,
    category: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Search the verified knowledge store for facts relevant to a query.

    Uses simple keyword overlap scoring. In production, replace with
    embedding-based semantic search against the Hub's vector store.

    Args:
        query:    Natural language query.
        hub_id:   If provided, restrict to this Hub's facts.
        category: If provided, restrict to this category.
        top_k:    Maximum number of results to return.

    Returns:
        List of fact records sorted by relevance score (descending).
    """
    query_tokens = set(re.findall(r"\w+", query.lower()))

    # Build candidate set
    if hub_id and hub_id in _HUB_INDEX:
        candidates = set(_HUB_INDEX[hub_id])
    elif category and category in _CATEGORY_INDEX:
        candidates = set(_CATEGORY_INDEX[category])
    else:
        candidates = set(_VERIFIED_FACTS.keys())

    scored: list[tuple[float, dict]] = []
    for fid in candidates:
        record = _VERIFIED_FACTS[fid]
        fact_tokens = set(re.findall(r"\w+", record["fact"].lower()))
        overlap = len(query_tokens & fact_tokens)
        if overlap > 0:
            score = overlap / max(len(query_tokens), 1)
            scored.append((score, record))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [rec for _, rec in scored[:top_k]]


def hallucination_score(text: str, context: list[dict] | None = None) -> float:
    """
    Estimate the probability (0–1) that `text` contains hallucinated content.

    Heuristics used:
    - Presence of absolute superlatives without qualification ("always", "never", "only ever")
    - Unverifiable specifics (large exact numbers stated without sourcing cues)
    - Low overlap with provided verified context facts

    In production, replace / augment with an NLI model (e.g. DeBERTa-v3)
    fine-tuned on factuality datasets, served by the KEEPIT inference API.

    Args:
        text:    The agent output text to evaluate.
        context: Verified fact records retrieved from the Hub.

    Returns:
        Float in [0, 1]. 0 = almost certainly grounded. 1 = likely hallucination.
    """
    score = 0.0

    # Heuristic 1: risky linguistic patterns
    risky_patterns = [
        r"\balways\b", r"\bnever\b", r"\bonly\b", r"\bexactly\b",
        r"\bguaranteed\b", r"\bproven\b", r"\bscientifically proven\b",
        r"\bfact\b.*\bno\b.*\bdoubt\b",
        r"\b100%\b",
    ]
    for pattern in risky_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.08

    # Heuristic 2: large specific numbers without source markers
    number_matches = re.findall(r"\b\d[\d,]{4,}\b", text)
    source_cues = re.findall(
        r"\b(according to|source:|per|reported by|based on|data from)\b",
        text, re.IGNORECASE
    )
    unsourced_numbers = max(0, len(number_matches) - len(source_cues))
    score += min(0.25, unsourced_numbers * 0.05)

    # Heuristic 3: cross-check against verified context
    if context:
        text_tokens = set(re.findall(r"\w+", text.lower()))
        max_overlap = 0.0
        for record in context:
            fact_tokens = set(re.findall(r"\w+", record["fact"].lower()))
            overlap = len(text_tokens & fact_tokens) / max(len(fact_tokens), 1)
            max_overlap = max(max_overlap, overlap)
        # Low overlap with verified facts → higher hallucination risk
        if max_overlap < 0.15:
            score += 0.30
        elif max_overlap < 0.35:
            score += 0.15

    return min(1.0, round(score, 3))


def ground_response(
    agent_id: str,
    query: str,
    agent_response: str,
    hub_id: str | None = None,
) -> dict[str, Any]:
    """
    Verify whether an agent's response is grounded in verified KEEPIT memory.

    This is the core anti-hallucination primitive. Agents MUST call this
    before emitting any factual response in production deployments.

    Args:
        agent_id:       Identifier of the querying agent.
        query:          The original question or task.
        agent_response: The draft response the agent intends to deliver.
        hub_id:         Optional Hub to restrict grounding lookup.

    Returns:
        {
            "grounded":    bool   — True if adequately supported by verified facts,
            "confidence":  float  — 0–1 confidence score,
            "corrections": list   — suggested corrections (strings),
            "sources":     list   — verified fact records used for grounding,
            "h_score":     float  — hallucination probability estimate,
        }
    """
    # Retrieve relevant verified knowledge
    sources = query_verified_knowledge(query, hub_id=hub_id)
    if not sources:
        # Also try querying by response tokens for broader coverage
        sources = query_verified_knowledge(agent_response[:120], hub_id=hub_id)

    h_score = hallucination_score(agent_response, context=sources)
    confidence = round(1.0 - h_score, 3)
    grounded = confidence >= 0.6 and len(sources) > 0

    corrections: list[str] = []
    if not grounded and sources:
        corrections.append(
            f"Consider grounding your response with verified data. "
            f"Relevant verified fact: \"{sources[0]['fact']}\" "
            f"(source: {sources[0]['source']})"
        )
    elif not sources:
        corrections.append(
            "No verified facts found for this query in the KEEPIT Hub. "
            "Mark response as 'unverified' or defer to a hub-verified source."
        )

    # Log to agent registry
    _AGENT_REGISTRY.setdefault(agent_id, {"queries": 0, "grounded": 0, "flagged": 0})
    _AGENT_REGISTRY[agent_id]["queries"] += 1
    if grounded:
        _AGENT_REGISTRY[agent_id]["grounded"] += 1
    else:
        _AGENT_REGISTRY[agent_id]["flagged"] += 1

    return {
        "grounded": grounded,
        "confidence": confidence,
        "h_score": h_score,
        "corrections": corrections,
        "sources": sources,
        "agent_id": agent_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


def moderate_agent_output(
    agent_id: str,
    output: str,
    strict: bool = False,
) -> dict[str, Any]:
    """
    Moderate an agent's output before delivery to the end user.

    Acts as the final gate in the KEEPIT verification pipeline:
        Agent → draft output → moderate_agent_output() → verified output → user

    Args:
        agent_id: Identifier of the agent producing the output.
        output:   The full text output to be moderated.
        strict:   If True, block any output with h_score > 0.3.
                  If False, only block output with h_score > 0.7.

    Returns:
        {
            "approved":       bool   — Whether the output passed moderation,
            "output":         str    — Approved output (or empty string if blocked),
            "flagged_output": str    — Original output when blocked,
            "h_score":        float  — Hallucination probability,
            "reason":         str    — Human-readable moderation result,
            "sources":        list   — Supporting verified facts,
        }
    """
    sources = query_verified_knowledge(output[:200])
    h_score = hallucination_score(output, context=sources)
    threshold = 0.3 if strict else 0.7

    approved = h_score <= threshold

    if approved:
        reason = (
            f"Output approved. Hallucination risk: {h_score:.2f} "
            f"(threshold: {threshold}). "
            f"Supported by {len(sources)} verified fact(s)."
        )
        return {
            "approved": True,
            "output": output,
            "flagged_output": "",
            "h_score": h_score,
            "reason": reason,
            "sources": sources,
            "agent_id": agent_id,
        }
    else:
        warning = (
            f"[KEEPIT MODERATION — BLOCKED] "
            f"Hallucination risk: {h_score:.2f} (threshold: {threshold}). "
            f"This output was not approved for delivery. "
            f"Please re-query with verified context from a KEEPIT Hub."
        )
        return {
            "approved": False,
            "output": "",
            "flagged_output": output,
            "h_score": h_score,
            "reason": warning,
            "sources": sources,
            "agent_id": agent_id,
        }


def get_hub_stats(hub_id: str) -> dict[str, Any]:
    """
    Return statistics for a specific KEEPIT Hub's verified knowledge.

    Args:
        hub_id: The KEEPIT Hub identifier.

    Returns:
        Dictionary with fact count, categories, and last-updated timestamp.
    """
    fact_ids = _HUB_INDEX.get(hub_id, [])
    facts = [_VERIFIED_FACTS[fid] for fid in fact_ids if fid in _VERIFIED_FACTS]
    categories = list({f["category"] for f in facts})
    last_updated = max((f["registered_at"] for f in facts), default=None)

    return {
        "hub_id": hub_id,
        "total_facts": len(facts),
        "categories": categories,
        "last_updated": last_updated,
    }


def agent_trust_score(agent_id: str) -> float:
    """
    Return the historical grounding rate (0–1) for a given agent.

    Agents with higher trust scores pay lower grounding fees on the
    KEEPIT marketplace (rewarding reliable, well-grounded agents).

    Args:
        agent_id: The agent identifier.

    Returns:
        Float in [0, 1] representing the grounding success rate.
    """
    stats = _AGENT_REGISTRY.get(agent_id, {})
    total = stats.get("queries", 0)
    if total == 0:
        return 0.0
    return round(stats.get("grounded", 0) / total, 3)


# ─────────────────────────────────────────────
# Initialize with seed data on import
# ─────────────────────────────────────────────

_load_seed_data()


# ─────────────────────────────────────────────
# Demo / smoke test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("KEEPIT Anti-Hallucination Layer — Demo")
    print("=" * 60)

    # 1. Check seed data loaded
    print(f"\n✅ Seed facts loaded: {len(_VERIFIED_FACTS)} verified facts across {len(_HUB_INDEX)} hubs\n")

    # 2. Query verified knowledge
    print("🔍 Querying for 'Brazil GDP economy'...")
    results = query_verified_knowledge("Brazil GDP economy", top_k=3)
    for r in results:
        print(f"  • [{r['category']}] {r['fact'][:80]}...")

    # 3. Test grounding — well-grounded response
    print("\n🧠 Testing ground_response() with a grounded claim...")
    result = ground_response(
        agent_id="agent-demo-001",
        query="What is Brazil's GDP?",
        agent_response=(
            "Brazil's GDP was approximately USD 2.13 trillion in 2023, "
            "according to the IMF World Economic Outlook."
        ),
    )
    print(f"  Grounded: {result['grounded']} | Confidence: {result['confidence']} | H-score: {result['h_score']}")

    # 4. Test grounding — ungrounded response
    print("\n⚠️  Testing ground_response() with a hallucinated claim...")
    result2 = ground_response(
        agent_id="agent-demo-001",
        query="What is Brazil's GDP?",
        agent_response=(
            "Brazil's GDP is exactly 9.99 trillion dollars and it is always "
            "the fastest growing economy in the world, guaranteed."
        ),
    )
    print(f"  Grounded: {result2['grounded']} | Confidence: {result2['confidence']} | H-score: {result2['h_score']}")
    if result2["corrections"]:
        print(f"  Correction hint: {result2['corrections'][0][:100]}...")

    # 5. Moderate agent output (strict mode)
    print("\n🛡️  Testing moderate_agent_output() in strict mode...")
    mod = moderate_agent_output(
        agent_id="agent-demo-001",
        output="São Paulo is Brazil's largest city with about 12.3 million residents per IBGE 2022.",
        strict=True,
    )
    print(f"  Approved: {mod['approved']} | H-score: {mod['h_score']}")

    # 6. Agent trust score
    trust = agent_trust_score("agent-demo-001")
    print(f"\n📊 Agent trust score for 'agent-demo-001': {trust}")

    print("\n" + "=" * 60)
    print("KEEPIT: The agent that doesn't hallucinate wins.")
    print("=" * 60)
