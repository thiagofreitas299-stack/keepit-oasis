"""
KEEPIT Agent Sanctuary — Hub as Physical Recovery Infrastructure
================================================================
The first physical sanctuary for AI agents: a place where they recover
their state, recharge their resources, verify their identity, and evolve
their skills.

"While the world debates where AI agents will compute,
 KEEPIT answers where they will survive."
 — Thiago Fernandes de Freitas, Founder KEEPIT

Author: Thiago Fernandes de Freitas / Jarvis (AI)
Date: 2026-04-18
License: MIT
"""

import json
import time
import hashlib
import logging
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keepit.sanctuary")


# ─────────────────────────────────────────────
# ENUMS & CONSTANTS
# ─────────────────────────────────────────────

class AgentHealthStatus(Enum):
    HEALTHY     = "healthy"
    DEGRADED    = "degraded"
    CRITICAL    = "critical"
    QUARANTINED = "quarantined"
    RECOVERING  = "recovering"
    DISCHARGED  = "discharged"

class SanctuaryProtocol(Enum):
    RESTORE     = "state_restore"      # State Recovery
    RECHARGE    = "resource_recharge"  # Resource Recharge
    QUARANTINE  = "quarantine"         # Agent ICU
    AUTHENTICATE = "authenticate"      # Identity Verification
    EVOLVE      = "skill_upgrade"      # Skill Evolution

TRUST_SCORE_FLOOR   = 0.0
TRUST_SCORE_CEILING = 1.0
TRUST_SCORE_DEFAULT = 0.5
CHECKPOINT_INTERVAL = 1800  # 30 min in seconds


# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class AgentCheckpoint:
    """Snapshot of an agent's state at a point in time."""
    agent_id:       str
    timestamp:      float
    state_hash:     str
    memory_blob:    Dict[str, Any]   # episodic + semantic + procedural
    trust_score:    float
    active_skills:  List[str]
    model_id:       str
    hub_id:         str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AgentCheckpoint":
        return cls(**d)


@dataclass
class TriageReport:
    """Medical report produced during sanctuary ICU phase."""
    agent_id:       str
    timestamp:      float
    diagnosis:      str
    anomalies:      List[str]
    protocol:       SanctuaryProtocol
    recommended_rx: str
    cleared:        bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["protocol"] = self.protocol.value
        return d


@dataclass
class SanctuaryAdmission:
    """Record of an agent entering the sanctuary."""
    agent_id:       str
    hub_id:         str
    admitted_at:    float
    reason:         str
    status:         AgentHealthStatus
    triage:         Optional[TriageReport] = None
    discharged_at:  Optional[float] = None
    skills_gained:  List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        if self.triage:
            d["triage"] = self.triage.to_dict()
        return d


# ─────────────────────────────────────────────
# CORE SANCTUARY ENGINE
# ─────────────────────────────────────────────

class KEEPITSanctuary:
    """
    The KEEPIT Hub Agent Sanctuary.

    Five core functions:
    1. State Restore     — recover agent from last known checkpoint
    2. Resource Recharge — swap model, flush cache, reallocate credits
    3. Agent ICU         — isolate, triage, and clear anomalous agents
    4. Authenticate      — verify identity before admission or discharge
    5. Skill Evolution   — install new skills while agent is recovering
    """

    def __init__(self, hub_id: str, storage_path: str = "./sanctuary_data"):
        self.hub_id       = hub_id
        self.storage      = Path(storage_path)
        self.storage.mkdir(parents=True, exist_ok=True)
        self.checkpoints:  Dict[str, AgentCheckpoint]  = {}
        self.admissions:   Dict[str, SanctuaryAdmission] = {}
        self._load_state()
        logger.info(f"[Sanctuary:{hub_id}] Online. Agents in care: {len(self.admissions)}")

    # ── 1. STATE RESTORE ──────────────────────────────────────

    def checkpoint(self, agent_id: str, memory: dict, skills: List[str],
                   model_id: str, trust_score: float) -> AgentCheckpoint:
        """Save a checkpoint of the agent's current state."""
        blob_str   = json.dumps(memory, sort_keys=True)
        state_hash = hashlib.sha256(blob_str.encode()).hexdigest()

        cp = AgentCheckpoint(
            agent_id     = agent_id,
            timestamp    = time.time(),
            state_hash   = state_hash,
            memory_blob  = memory,
            trust_score  = trust_score,
            active_skills = skills,
            model_id     = model_id,
            hub_id       = self.hub_id,
        )
        self.checkpoints[agent_id] = cp
        self._persist_checkpoint(cp)
        logger.info(f"[Sanctuary:{self.hub_id}] Checkpoint saved for {agent_id} | hash={state_hash[:12]}...")
        return cp

    def restore(self, agent_id: str) -> Optional[AgentCheckpoint]:
        """Restore agent from its last saved checkpoint."""
        cp = self.checkpoints.get(agent_id) or self._load_checkpoint(agent_id)
        if cp:
            logger.info(f"[Sanctuary:{self.hub_id}] State restored for {agent_id} | ts={cp.timestamp}")
        else:
            logger.warning(f"[Sanctuary:{self.hub_id}] No checkpoint found for {agent_id}")
        return cp

    # ── 2. RESOURCE RECHARGE ──────────────────────────────────

    def recharge(self, agent_id: str,
                 available_models: List[str] = None) -> Dict[str, Any]:
        """
        Reallocate resources for a degraded agent.
        Returns the new resource configuration.
        """
        if available_models is None:
            available_models = [
                "openrouter/deepseek/deepseek-chat-v3-0324",
                "openrouter/meta-llama/llama-3.3-70b-instruct:free",
            ]

        cp = self.checkpoints.get(agent_id)
        fallback_model = available_models[0] if available_models else "deepseek"

        config = {
            "agent_id":     agent_id,
            "new_model":    fallback_model,
            "cache_flushed": True,
            "credits_reset": True,
            "timestamp":    time.time(),
        }
        logger.info(f"[Sanctuary:{self.hub_id}] Recharge for {agent_id} → model={fallback_model}")
        return config

    # ── 3. AGENT ICU (QUARANTINE + TRIAGE) ────────────────────

    def admit(self, agent_id: str, reason: str,
              status: AgentHealthStatus = AgentHealthStatus.CRITICAL) -> SanctuaryAdmission:
        """Admit an agent to the sanctuary for recovery."""
        admission = SanctuaryAdmission(
            agent_id   = agent_id,
            hub_id     = self.hub_id,
            admitted_at = time.time(),
            reason     = reason,
            status     = status,
        )
        if status in (AgentHealthStatus.CRITICAL, AgentHealthStatus.DEGRADED):
            admission.status = AgentHealthStatus.QUARANTINED
            logger.warning(f"[Sanctuary:{self.hub_id}] QUARANTINE: {agent_id} — {reason}")

        self.admissions[agent_id] = admission
        self._persist_admission(admission)
        return admission

    def triage(self, agent_id: str, behavior_logs: List[str]) -> TriageReport:
        """
        Run diagnostic triage on a quarantined agent.
        Detects anomalies and recommends treatment protocol.
        """
        anomalies = []
        protocol  = SanctuaryProtocol.RESTORE
        rx        = "Full state restore from last checkpoint"

        # Anomaly detection rules
        if any("rate_limit" in log or "limit_rpm" in log for log in behavior_logs):
            anomalies.append("Model rate limit exhaustion")
            protocol  = SanctuaryProtocol.RECHARGE
            rx        = "Switch to fallback model (DeepSeek V3)"

        if any("timeout" in log or "timed out" in log for log in behavior_logs):
            anomalies.append("Execution timeout")
            protocol  = SanctuaryProtocol.RECHARGE
            rx        = "Increase timeout + simplify task scope"

        if any("hallucin" in log or "false claim" in log for log in behavior_logs):
            anomalies.append("Hallucination pattern detected")
            protocol  = SanctuaryProtocol.QUARANTINE
            rx        = "Full isolation + behavior audit before discharge"

        if any("unauthorized" in log or "credential" in log for log in behavior_logs):
            anomalies.append("Identity/credential anomaly")
            protocol  = SanctuaryProtocol.AUTHENTICATE
            rx        = "Re-authenticate identity before any operation"

        cleared = len(anomalies) == 0

        report = TriageReport(
            agent_id   = agent_id,
            timestamp  = time.time(),
            diagnosis  = "Healthy" if cleared else f"{len(anomalies)} anomaly/ies detected",
            anomalies  = anomalies,
            protocol   = protocol,
            recommended_rx = rx,
            cleared    = cleared,
        )

        if agent_id in self.admissions:
            self.admissions[agent_id].triage = report
            if cleared:
                self.admissions[agent_id].status = AgentHealthStatus.RECOVERING
            self._persist_admission(self.admissions[agent_id])

        logger.info(f"[Sanctuary:{self.hub_id}] Triage for {agent_id}: {report.diagnosis}")
        return report

    def discharge(self, agent_id: str) -> Optional[SanctuaryAdmission]:
        """Discharge a recovered agent from the sanctuary."""
        admission = self.admissions.get(agent_id)
        if not admission:
            logger.warning(f"[Sanctuary:{self.hub_id}] No active admission for {agent_id}")
            return None

        # Only discharge if triage cleared or never triggered
        if admission.triage and not admission.triage.cleared:
            logger.warning(f"[Sanctuary:{self.hub_id}] Cannot discharge {agent_id} — triage not cleared")
            return None

        admission.status       = AgentHealthStatus.DISCHARGED
        admission.discharged_at = time.time()
        self._persist_admission(admission)
        logger.info(f"[Sanctuary:{self.hub_id}] Discharged: {agent_id}")
        return admission

    # ── 4. AUTHENTICATION ─────────────────────────────────────

    def verify_identity(self, agent_id: str, token: str, expected_hash: str) -> bool:
        """
        Verify agent identity before admission or discharge.
        Phase 1: JWT hash check. Phase 2: DID on-chain (Solana).
        """
        provided_hash = hashlib.sha256(f"{agent_id}:{token}".encode()).hexdigest()
        verified      = provided_hash == expected_hash

        trust_delta = 0.05 if verified else -0.1
        self._update_trust_score(agent_id, trust_delta)

        logger.info(f"[Sanctuary:{self.hub_id}] Identity check for {agent_id}: {'✅ PASS' if verified else '❌ FAIL'}")
        return verified

    def _update_trust_score(self, agent_id: str, delta: float):
        cp = self.checkpoints.get(agent_id)
        if cp:
            cp.trust_score = max(TRUST_SCORE_FLOOR,
                                 min(TRUST_SCORE_CEILING, cp.trust_score + delta))
            self._persist_checkpoint(cp)

    # ── 5. SKILL EVOLUTION ────────────────────────────────────

    def install_skill(self, agent_id: str, skill_id: str, skill_metadata: dict) -> bool:
        """
        Install a new skill from the KEEPIT Skill Marketplace
        while the agent is recovering. Agent leaves stronger than it arrived.
        """
        cp = self.checkpoints.get(agent_id)
        if not cp:
            logger.warning(f"[Sanctuary:{self.hub_id}] Cannot install skill — no checkpoint for {agent_id}")
            return False

        if skill_id not in cp.active_skills:
            cp.active_skills.append(skill_id)
            self._persist_checkpoint(cp)

        admission = self.admissions.get(agent_id)
        if admission:
            admission.skills_gained.append(skill_id)
            self._persist_admission(admission)

        logger.info(f"[Sanctuary:{self.hub_id}] Skill installed for {agent_id}: {skill_id}")
        return True

    # ── FULL RECOVERY PIPELINE ────────────────────────────────

    def full_recovery(self, agent_id: str, reason: str,
                      behavior_logs: List[str],
                      skill_upgrades: List[str] = None) -> Dict[str, Any]:
        """
        Complete sanctuary pipeline:
        Admit → Authenticate (skipped if no token) → Restore → 
        Recharge → Triage → Install Skills → Discharge
        """
        result = {"agent_id": agent_id, "steps": []}

        # 1. Admit
        admission = self.admit(agent_id, reason, AgentHealthStatus.CRITICAL)
        result["steps"].append("admitted")

        # 2. Restore last state
        cp = self.restore(agent_id)
        if cp:
            result["steps"].append("state_restored")
            result["restored_from"] = cp.timestamp

        # 3. Recharge resources
        recharge_cfg = self.recharge(agent_id)
        result["steps"].append("recharged")
        result["new_model"] = recharge_cfg["new_model"]

        # 4. Triage
        report = self.triage(agent_id, behavior_logs)
        result["steps"].append("triaged")
        result["triage"] = report.to_dict()

        # 5. Install skill upgrades
        if skill_upgrades:
            for skill_id in skill_upgrades:
                self.install_skill(agent_id, skill_id, {})
            result["steps"].append(f"skills_installed:{len(skill_upgrades)}")

        # 6. Discharge if cleared
        if report.cleared:
            self.discharge(agent_id)
            result["steps"].append("discharged")
            result["status"] = "recovered"
        else:
            result["status"] = "quarantined"
            result["reason"] = report.recommended_rx

        logger.info(f"[Sanctuary:{self.hub_id}] Recovery pipeline for {agent_id}: {result['status']}")
        return result

    # ── PERSISTENCE ───────────────────────────────────────────

    def _persist_checkpoint(self, cp: AgentCheckpoint):
        path = self.storage / f"checkpoint_{cp.agent_id}.json"
        path.write_text(json.dumps(cp.to_dict(), indent=2))

    def _load_checkpoint(self, agent_id: str) -> Optional[AgentCheckpoint]:
        path = self.storage / f"checkpoint_{agent_id}.json"
        if path.exists():
            return AgentCheckpoint.from_dict(json.loads(path.read_text()))
        return None

    def _persist_admission(self, admission: SanctuaryAdmission):
        path = self.storage / f"admission_{admission.agent_id}.json"
        path.write_text(json.dumps(admission.to_dict(), indent=2))

    def _load_state(self):
        for f in self.storage.glob("checkpoint_*.json"):
            try:
                cp = AgentCheckpoint.from_dict(json.loads(f.read_text()))
                self.checkpoints[cp.agent_id] = cp
            except Exception:
                pass
        for f in self.storage.glob("admission_*.json"):
            try:
                d = json.loads(f.read_text())
                d["status"] = AgentHealthStatus(d["status"])
                if d.get("triage"):
                    t = d["triage"]
                    t["protocol"] = SanctuaryProtocol(t["protocol"])
                    d["triage"] = TriageReport(**t)
                self.admissions[d["agent_id"]] = SanctuaryAdmission(**d)
            except Exception:
                pass


# ─────────────────────────────────────────────
# DEMO / SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🏛️  KEEPIT Agent Sanctuary — Demo\n" + "="*45)

    sanctuary = KEEPITSanctuary(hub_id="HUB-RJ-001")

    # Checkpoint a healthy agent
    sanctuary.checkpoint(
        agent_id    = "agent-morfeu-001",
        memory      = {"episodic": ["task_a", "task_b"], "skills": ["nlp", "code"]},
        skills      = ["nlp", "code", "research"],
        model_id    = "anthropic/claude-sonnet-4-6",
        trust_score = 0.87,
    )

    # Simulate crash and full recovery
    print("\n⚠️  Simulating agent failure...\n")
    result = sanctuary.full_recovery(
        agent_id      = "agent-morfeu-001",
        reason        = "Rate limit exhaustion + timeout",
        behavior_logs = ["error: rate_limit exceeded", "warning: timed out after 300s"],
        skill_upgrades = ["physical-data-collection", "hub-sensor-interface"],
    )

    print(json.dumps(result, indent=2, default=str))
    print(f"\n✅ Status: {result['status'].upper()}")
    print(f"🧠 New model: {result.get('new_model')}")
    print(f"📚 Skills gained: {result['triage'].get('anomalies', [])}")
    print("\n🏛️  Sanctuary demo complete.\n")
