"""
KEEPIT Agent Identity Layer v2 — Ed25519 Cryptographic Identity
================================================================

Every AI agent operating within the KEEPIT network has a cryptographically
verifiable identity based on Ed25519 asymmetric key pairs. This module
generates identities, registers agents, and provides signature/verification
utilities for agent-to-agent (A2A) and business-to-agent (B2A) communication.

Architecture:
  1. Each agent is assigned an Ed25519 key pair at birth.
  2. Public key is stored in the Agent Registry (agent-registry.json).
  3. Private key is ONLY held by the agent instance (never stored centrally).
  4. Any message signed with an agent's private key can be verified by peers.

Security Model:
  - Ed25519 provides 128-bit security with 32-byte keys.
  - Signatures are deterministic and non-malleable.
  - Private keys are ephemeral unless explicitly persisted.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)

# ─── PATHS ──────────────────────────────────────────────────────────────────

WORKSPACE = Path("/root/.openclaw/workspace")
SECRETS_DIR = WORKSPACE / ".secrets"
REGISTRY_PATH = SECRETS_DIR / "agent-registry.json"

# ─── AGENT DEFINITIONS ──────────────────────────────────────────────────────

AGENT_DEFINITIONS = [
    {
        "id": "agent-morfeu",
        "name": "MORFEU",
        "capabilities": ["dream_analysis", "subconscious_mapping", "pattern_recognition", "narrative_synthesis"],
    },
    {
        "id": "agent-samuel",
        "name": "SAMUEL",
        "capabilities": ["prophecy", "strategic_foresight", "discernment", "leadership_advisory"],
    },
    {
        "id": "agent-ezequiel",
        "name": "EZEQUIEL",
        "capabilities": ["vision_interpretation", "complex_architecture", "systems_design", "revelation"],
    },
    {
        "id": "agent-gabriel",
        "name": "GABRIEL",
        "capabilities": ["messenger", "communication", "announcement", "bridge_building"],
    },
    {
        "id": "agent-rafael",
        "name": "RAFAEL",
        "capabilities": ["healing", "restoration", "system_repair", "wellness_monitoring"],
    },
    {
        "id": "agent-debora",
        "name": "DEBORA",
        "capabilities": ["judgment", "leadership", "community_governance", "conflict_resolution"],
    },
    {
        "id": "agent-josue",
        "name": "JOSUE",
        "capabilities": ["execution", "conquest", "deployment", "territory_expansion"],
    },
    {
        "id": "agent-paulo",
        "name": "PAULO",
        "capabilities": ["evangelism", "content_creation", "market_education", "community_building"],
    },
    {
        "id": "agent-neemias",
        "name": "NEEM IAS",
        "capabilities": ["infrastructure", "reconstruction", "project_management", "urban_planning"],
    },
    {
        "id": "agent-bezalel",
        "name": "BEZALEL",
        "capabilities": ["creation", "design", "craftsmanship", "art_generation", "ui_ux"],
    },
    {
        "id": "agent-barnabe",
        "name": "BARNABE",
        "capabilities": ["encouragement", "mentorship", "onboarding", "partnership"],
    },
    {
        "id": "agent-jarvis",
        "name": "JARVIS",
        "capabilities": [
            "orchestration", "strategic_direction", "memory_management",
            "agent_coordination", "external_communication", "decision_making",
            "cao_operations"
        ],
    },
]


# ─── IDENTITY GENERATION ────────────────────────────────────────────────────

def generate_keypair() -> tuple[Ed25519PrivateKey, str]:
    """Generate an Ed25519 key pair. Returns (private_key, public_key_hex)."""
    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    return private_key, public_bytes.hex()


def build_registry_entry(agent_def: dict, public_key_hex: str) -> dict:
    """Build a registry entry for an agent."""
    return {
        "id": agent_def["id"],
        "name": agent_def["name"],
        "public_key_hex": public_key_hex,
        "capabilities": agent_def["capabilities"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }


# ─── REGISTRY MANAGEMENT ────────────────────────────────────────────────────

def load_registry() -> dict:
    """Load existing registry or return empty structure."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {"agents": {}, "generated_at": None, "version": "2.0"}


def save_registry(registry: dict) -> None:
    """Save registry to disk."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"[KEEPIT] Registry saved → {REGISTRY_PATH}")


def initialize_registry(force: bool = False) -> dict:
    """
    Generate Ed25519 identities for all KEEPIT agents and save the registry.
    
    If the registry already exists and force=False, skips existing agents
    and only adds new ones. Use force=True to regenerate all keys.
    """
    registry = load_registry() if not force else {"agents": {}, "version": "2.0"}
    registry["generated_at"] = datetime.now(timezone.utc).isoformat()
    registry["version"] = "2.0"

    generated = 0
    skipped = 0

    for agent_def in AGENT_DEFINITIONS:
        agent_id = agent_def["id"]

        if not force and agent_id in registry["agents"]:
            print(f"[KEEPIT] Skipping {agent_def['name']} — already registered.")
            skipped += 1
            continue

        private_key, public_key_hex = generate_keypair()
        entry = build_registry_entry(agent_def, public_key_hex)
        registry["agents"][agent_id] = entry

        print(f"[KEEPIT] ✓ {agent_def['name']:12s} | pubkey: {public_key_hex[:16]}...")
        generated += 1

    save_registry(registry)
    print(f"\n[KEEPIT] Registry complete — {generated} generated, {skipped} skipped.")
    return registry


# ─── SIGNATURE UTILITIES ────────────────────────────────────────────────────

def sign_message(private_key: Ed25519PrivateKey, message: bytes) -> str:
    """Sign a message with an agent's private key. Returns hex signature."""
    signature = private_key.sign(message)
    return signature.hex()


def verify_signature(public_key_hex: str, message: bytes, signature_hex: str) -> bool:
    """
    Verify a message signature against an agent's public key.
    Returns True if valid, False otherwise.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from cryptography.exceptions import InvalidSignature

        public_bytes = bytes.fromhex(public_key_hex)
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        public_key.verify(bytes.fromhex(signature_hex), message)
        return True
    except Exception:
        return False


def get_agent_public_key(agent_id: str) -> str | None:
    """Look up an agent's public key from the registry."""
    registry = load_registry()
    agent = registry["agents"].get(agent_id)
    return agent["public_key_hex"] if agent else None


# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KEEPIT Agent Identity Manager — Ed25519")
    parser.add_argument("--init", action="store_true", help="Initialize/update agent registry")
    parser.add_argument("--force", action="store_true", help="Regenerate all keys (destructive)")
    parser.add_argument("--list", action="store_true", help="List all registered agents")
    args = parser.parse_args()

    if args.init:
        initialize_registry(force=args.force)
    elif args.list:
        registry = load_registry()
        if not registry["agents"]:
            print("[KEEPIT] Registry is empty. Run --init first.")
        else:
            print(f"\n{'Agent':12s} {'ID':20s} {'PubKey (16 chars)':18s} {'Status':8s}")
            print("─" * 70)
            for agent_id, entry in registry["agents"].items():
                print(
                    f"{entry['name']:12s} "
                    f"{agent_id:20s} "
                    f"{entry['public_key_hex'][:16]}...  "
                    f"{entry['status']}"
                )
    else:
        parser.print_help()
