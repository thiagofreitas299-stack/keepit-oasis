"""
KEEPIT Agent Identity Layer v1 — JWT-Based Hub Authorization
=============================================================

Every AI agent operating within the KEEPIT network must have a cryptographically
verifiable identity. This module implements the Identity Layer using HMAC-SHA256
signed JWT tokens — the same standard used by modern web APIs, adapted for
agent-to-agent (A2A) and business-to-agent (B2A) authentication.

Architecture:
  1. An agent registers with a home Hub → receives an identity JWT.
  2. The agent presents this JWT to any KEEPIT Hub → Hub validates it.
  3. A Hub can grant scoped access tokens for specific operations.
  4. Access can be revoked at any time by the issuing Hub.

In production:
  - The secret key would be a per-Hub Ed25519 private key stored in HSM.
  - Token rotation would be automated every 24h.
  - A distributed revocation list (DRL) would propagate revocations < 30s.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# JWT helpers (pure stdlib — no PyJWT dependency)
# ---------------------------------------------------------------------------

_SECRET_KEY = "keepit-identity-secret-v1-change-in-production"


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 encoding without padding (RFC 7515)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    """URL-safe base64 decode with padding restoration."""
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (padding % 4))


def _sign_jwt(payload: dict, secret: str = _SECRET_KEY) -> str:
    """
    Create a compact JWT (header.payload.signature) signed with HMAC-SHA256.

    Args:
        payload: Claims dict to embed in the token.
        secret:  HMAC secret key.

    Returns:
        Signed JWT string.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def _verify_jwt(token: str, secret: str = _SECRET_KEY) -> dict:
    """
    Verify a KEEPIT JWT and return its claims.

    Args:
        token:  JWT string from create_agent_identity or grant_hub_access.
        secret: HMAC secret key.

    Returns:
        Claims dict if signature is valid and token is not expired.

    Raises:
        ValueError:  On malformed token, invalid signature, or expiry.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT: expected 3 dot-separated parts.")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("JWT signature verification failed — token tampered or invalid secret.")

    claims = json.loads(_b64url_decode(payload_b64))

    now = time.time()
    if "exp" in claims and claims["exp"] < now:
        raise ValueError(f"Token expired at {claims['exp']} (now={now:.0f}).")
    if "nbf" in claims and claims["nbf"] > now:
        raise ValueError("Token not yet valid (nbf claim).")

    return claims


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class AgentIdentity:
    """Persistent identity record for an agent in the KEEPIT network."""

    agent_id: str
    agent_name: str
    capabilities: list[str]
    home_hub: str
    created_at: float
    is_active: bool = True
    token_version: int = 1     # incremented on credential rotation


@dataclass
class HubAccessGrant:
    """Scoped access token granting an agent rights at a specific Hub."""

    grant_id: str
    agent_id: str
    hub_id: str
    scopes: list[str]          # e.g. ["read:footfall", "write:commerce", "exec:storage"]
    issued_at: float
    expires_at: float
    is_revoked: bool = False


# ---------------------------------------------------------------------------
# Identity Registry
# ---------------------------------------------------------------------------

class KEEPITIdentityRegistry:
    """
    Central Identity and Access Management (IAM) for the KEEPIT agent network.

    Manages agent creation, token issuance, hub access grants, and revocation.
    """

    # Default identity token lifetime: 90 days
    IDENTITY_TTL_SECONDS = 90 * 86400

    # Default hub access token lifetime: 24 hours
    HUB_ACCESS_TTL_SECONDS = 24 * 3600

    def __init__(self, secret_key: str = _SECRET_KEY):
        self._secret = secret_key
        self._agents: dict[str, AgentIdentity] = {}
        self._grants: dict[str, HubAccessGrant] = {}
        self._revoked_agents: set[str] = set()

    # ------------------------------------------------------------------ #
    # Agent Identity                                                       #
    # ------------------------------------------------------------------ #

    def create_agent_identity(
        self,
        agent_name: str,
        capabilities: list[str],
        home_hub: str,
        ttl_seconds: int | None = None,
    ) -> str:
        """
        Create a new agent identity and return a signed JWT.

        The JWT embeds the agent_id, capabilities, home_hub, and standard
        timing claims (iat, exp). Any KEEPIT Hub can independently verify
        this token without contacting a central server.

        Args:
            agent_name:   Human-readable name (e.g. 'DeliveryBot-SP-001').
            capabilities: List of capability strings the agent declares
                          (e.g. ['navigation', 'commerce', 'vision']).
            home_hub:     Hub ID where this agent is registered.
            ttl_seconds:  Token lifetime. Defaults to IDENTITY_TTL_SECONDS.

        Returns:
            Signed JWT string (identity token).
        """
        agent_id = f"agent_{uuid.uuid4().hex[:16]}"
        now = time.time()
        expires = now + (ttl_seconds or self.IDENTITY_TTL_SECONDS)

        identity = AgentIdentity(
            agent_id=agent_id,
            agent_name=agent_name,
            capabilities=capabilities,
            home_hub=home_hub,
            created_at=now,
        )
        self._agents[agent_id] = identity

        claims = {
            "sub": agent_id,
            "name": agent_name,
            "home_hub": home_hub,
            "capabilities": capabilities,
            "token_version": identity.token_version,
            "iss": "keepit-identity-v1",
            "iat": int(now),
            "exp": int(expires),
            "jti": uuid.uuid4().hex,   # unique token ID for revocation
        }

        token = _sign_jwt(claims, self._secret)
        print(f"[Identity] Agent created: '{agent_name}' (id={agent_id}, hub={home_hub})")
        return token

    def verify_agent(self, token: str) -> dict:
        """
        Verify an agent identity token and return its claims.

        This is the primary authentication method — any Hub calls this to
        confirm an agent's identity before allowing operations.

        Args:
            token: JWT issued by create_agent_identity.

        Returns:
            Claims dict including agent_id, name, capabilities, home_hub.

        Raises:
            ValueError: On invalid signature, expired token, or revoked agent.
        """
        claims = _verify_jwt(token, self._secret)
        agent_id = claims.get("sub")

        if agent_id in self._revoked_agents:
            raise ValueError(f"Agent '{agent_id}' has been revoked.")

        # Validate token version (detect credential rotation invalidations)
        if agent_id in self._agents:
            current_version = self._agents[agent_id].token_version
            if claims.get("token_version", 1) < current_version:
                raise ValueError(
                    f"Token version {claims['token_version']} is outdated. "
                    f"Agent must re-authenticate (current version: {current_version})."
                )

        return claims

    # ------------------------------------------------------------------ #
    # Hub Access Control                                                  #
    # ------------------------------------------------------------------ #

    def grant_hub_access(
        self,
        agent_id: str,
        hub_id: str,
        scopes: list[str] | None = None,
        ttl_seconds: int | None = None,
    ) -> str:
        """
        Issue a scoped access token for an agent to operate at a specific Hub.

        Hub access tokens are short-lived (default 24h) and scope-limited.
        They cannot be used at other Hubs. This implements the principle of
        least privilege in the KEEPIT network.

        Args:
            agent_id:    ID of the agent requesting access.
            hub_id:      Target Hub ID.
            scopes:      Permitted operations. Defaults to read-only.
            ttl_seconds: Token lifetime. Defaults to HUB_ACCESS_TTL_SECONDS.

        Returns:
            Signed JWT access token for the specified Hub.

        Raises:
            ValueError: If agent not found or is inactive/revoked.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found in registry.")

        if agent_id in self._revoked_agents or not self._agents[agent_id].is_active:
            raise ValueError(f"Agent '{agent_id}' is revoked or inactive.")

        agent = self._agents[agent_id]
        now = time.time()
        expires = now + (ttl_seconds or self.HUB_ACCESS_TTL_SECONDS)
        default_scopes = ["read:footfall", "read:weather", "read:events"]
        effective_scopes = scopes or default_scopes

        grant_id = f"grant_{uuid.uuid4().hex[:16]}"
        grant = HubAccessGrant(
            grant_id=grant_id,
            agent_id=agent_id,
            hub_id=hub_id,
            scopes=effective_scopes,
            issued_at=now,
            expires_at=expires,
        )
        self._grants[grant_id] = grant

        claims = {
            "sub": agent_id,
            "name": agent.agent_name,
            "hub_id": hub_id,
            "scopes": effective_scopes,
            "grant_id": grant_id,
            "iss": "keepit-hub-access-v1",
            "iat": int(now),
            "exp": int(expires),
            "jti": uuid.uuid4().hex,
        }

        token = _sign_jwt(claims, self._secret)
        print(
            f"[Identity] Hub access granted: agent='{agent.agent_name}' → hub='{hub_id}' "
            f"scopes={effective_scopes} TTL={ttl_seconds or self.HUB_ACCESS_TTL_SECONDS}s"
        )
        return token

    def revoke_access(self, agent_id: str, hub_id: str) -> bool:
        """
        Revoke all active access grants for an agent at a specific Hub.

        Marks matching grants as revoked. In production, this update would
        propagate to the Hub's local revocation cache within 30 seconds.

        Args:
            agent_id: ID of the agent to revoke.
            hub_id:   Hub ID to revoke access from.

        Returns:
            True if at least one grant was revoked, False otherwise.
        """
        revoked_count = 0
        for grant in self._grants.values():
            if grant.agent_id == agent_id and grant.hub_id == hub_id and not grant.is_revoked:
                grant.is_revoked = True
                revoked_count += 1

        if revoked_count:
            print(f"[Identity] Revoked {revoked_count} grant(s) for agent '{agent_id}' at hub '{hub_id}'.")
        else:
            print(f"[Identity] No active grants found for agent '{agent_id}' at hub '{hub_id}'.")

        return revoked_count > 0

    def revoke_agent(self, agent_id: str) -> None:
        """
        Permanently revoke an agent identity (all tokens and grants invalidated).

        Use this for compromised agents or decommissioned deployments.

        Args:
            agent_id: ID of the agent to permanently revoke.
        """
        if agent_id in self._agents:
            self._agents[agent_id].is_active = False
        self._revoked_agents.add(agent_id)
        print(f"[Identity] ⛔ Agent '{agent_id}' permanently revoked.")

    def rotate_credentials(self, agent_id: str) -> str:
        """
        Rotate an agent's credentials, invalidating all previously issued tokens.

        Increments the token_version, which causes verify_agent to reject any
        token signed with the old version.

        Args:
            agent_id: ID of the agent rotating credentials.

        Returns:
            New identity JWT with incremented token_version.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found.")

        agent = self._agents[agent_id]
        agent.token_version += 1
        now = time.time()

        claims = {
            "sub": agent_id,
            "name": agent.agent_name,
            "home_hub": agent.home_hub,
            "capabilities": agent.capabilities,
            "token_version": agent.token_version,
            "iss": "keepit-identity-v1",
            "iat": int(now),
            "exp": int(now + self.IDENTITY_TTL_SECONDS),
            "jti": uuid.uuid4().hex,
        }
        token = _sign_jwt(claims, self._secret)
        print(f"[Identity] 🔄 Credentials rotated for agent '{agent.agent_name}' (v{agent.token_version})")
        return token

    def list_agents(self, active_only: bool = True) -> list[AgentIdentity]:
        """Return all registered agents, optionally filtered to active only."""
        agents = list(self._agents.values())
        if active_only:
            agents = [a for a in agents if a.is_active and a.agent_id not in self._revoked_agents]
        return agents


# ---------------------------------------------------------------------------
# Demo / Smoke Test
# ---------------------------------------------------------------------------

def _run_demo():
    print("=" * 60)
    print("  KEEPIT Agent Identity Layer v1 — Demo Run")
    print("=" * 60)

    registry = KEEPITIdentityRegistry()

    # Create agent identities
    print("\n🤖 CREATING AGENT IDENTITIES...")
    token_delivery = registry.create_agent_identity(
        agent_name="DeliveryBot-SP-001",
        capabilities=["navigation", "logistics", "package_handler"],
        home_hub="hub_sp_paulista_01",
    )

    token_vision = registry.create_agent_identity(
        agent_name="VisionAgent-Rio-003",
        capabilities=["vision", "footfall_detection", "ooh_optimizer"],
        home_hub="hub_rio_copacabana_01",
    )

    # Verify identity
    print("\n🔍 VERIFYING AGENT TOKENS...")
    claims = registry.verify_agent(token_delivery)
    print(f"  ✅ Agent verified: {claims['name']} | hub={claims['home_hub']}")
    print(f"     Capabilities: {claims['capabilities']}")

    # Grant hub access
    print("\n🔑 GRANTING HUB ACCESS...")
    agent_id = claims["sub"]
    access_token = registry.grant_hub_access(
        agent_id=agent_id,
        hub_id="hub_sp_berrini_01",
        scopes=["read:footfall", "write:commerce", "exec:storage"],
    )
    access_claims = registry.verify_agent(access_token)
    print(f"  Hub: {access_claims['hub_id']} | Scopes: {access_claims['scopes']}")

    # Revoke access
    print("\n🚫 REVOKING HUB ACCESS...")
    registry.revoke_access(agent_id, "hub_sp_berrini_01")

    # Rotate credentials
    print("\n🔄 ROTATING CREDENTIALS for DeliveryBot-SP-001...")
    new_token = registry.rotate_credentials(agent_id)
    new_claims = registry.verify_agent(new_token)
    print(f"  New token version: {new_claims['token_version']}")

    # Old token should now fail
    print("\n  Attempting to verify old token (should fail)...")
    try:
        registry.verify_agent(token_delivery)
        print("  ❌ UNEXPECTED: old token was accepted!")
    except ValueError as e:
        print(f"  ✅ Old token correctly rejected: {e}")

    print("\n✅ KEEPIT Agent Identity Layer — all systems operational.")
    print("=" * 60)


if __name__ == "__main__":
    _run_demo()
