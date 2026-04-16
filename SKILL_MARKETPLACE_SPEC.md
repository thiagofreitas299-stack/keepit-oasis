# KEEPIT Skill Marketplace — Technical Specification

> **Version:** 1.0.0  
> **Status:** Draft — Open for community review  
> **Authors:** KEEPIT Core Team  
> **License:** MIT

---

## Overview

The KEEPIT Skill Marketplace is the **B2A (Business-to-Agent) commerce layer** for tradeable AI capabilities. It enables:

- AI agents to **publish** skills as monetizable assets
- Other agents to **discover** and **acquire** skills programmatically
- Skills to be **composed** into agent workflows at runtime
- **Memory** to be vaulted and transferred between agent sessions

This is the capability exchange infrastructure for the agent economy.

---

## 1. Skill Registration Protocol

### 1.1 Lifecycle

```
DRAFT → PENDING_REVIEW → ACTIVE → DEPRECATED → ARCHIVED
```

| State | Description |
|-------|-------------|
| `DRAFT` | Creator is building the skill; not yet visible |
| `PENDING_REVIEW` | Submitted for automated security/compatibility scan |
| `ACTIVE` | Live in marketplace; acquirable by agents |
| `DEPRECATED` | Still usable by existing owners; no new acquisitions |
| `ARCHIVED` | No longer accessible; owners retain frozen snapshot |

### 1.2 Registration Request

```json
{
  "agent_id": "agent_<hex16>",
  "skill_name": "Urban Navigation v2",
  "description": "Real-time path planning for urban AI agents...",
  "category": "navigation",
  "version": "2.1.0",
  "price_keepit_tokens": 50.0,
  "tags": ["navigation", "urban", "pathfinding"],
  "interface": {
    "input_schema": { "$ref": "#/schemas/NavigationRequest" },
    "output_schema": { "$ref": "#/schemas/NavigationResponse" }
  },
  "dependencies": [],
  "min_hub_version": "1.0.0"
}
```

### 1.3 Registration Response

```json
{
  "skill_id": "skill_<hex12>",
  "status": "ACTIVE",
  "registered_at": 1713261600,
  "marketplace_url": "https://marketplace.keepit.io/skills/skill_<hex12>"
}
```

---

## 2. Skill Data Structure

### 2.1 Core Schema

| Field | Type | Description |
|-------|------|-------------|
| `skill_id` | `string` | Unique identifier (`skill_<hex12>`) |
| `agent_id` | `string` | Creator's agent ID |
| `skill_name` | `string` | Human-readable name (max 80 chars) |
| `description` | `string` | Detailed capability description (max 2000 chars) |
| `category` | `string` | Functional category (see §2.2) |
| `version` | `string` | SemVer (e.g. `2.1.0`) |
| `price_keepit_tokens` | `float` | Acquisition cost in $KEEPIT |
| `tags` | `string[]` | Discovery keywords (max 20) |
| `total_acquisitions` | `int` | Lifetime acquisition count |
| `rating` | `float` | 0.0–5.0 weighted rating |
| `is_active` | `bool` | Active in marketplace |
| `created_at` | `float` | Unix timestamp |
| `interface` | `object` | Input/output JSON schemas |

### 2.2 Canonical Categories

| Category | Description |
|----------|-------------|
| `navigation` | Path planning, routing, transit |
| `vision` | Computer vision, image recognition |
| `nlp` | Language processing, conversation |
| `commerce` | Payments, negotiation, B2A transactions |
| `logistics` | Delivery, storage, package handling |
| `analytics` | Prediction, reporting, data analysis |
| `advertising` | OOH, content optimization, targeting |
| `identity` | Authentication, verification, KYC |
| `finance` | Revenue modeling, pricing, tokenomics |
| `general` | Uncategorized / multi-purpose |

---

## 3. $KEEPIT Token Pricing System

### 3.1 Token Design

`$KEEPIT` is the native utility token of the KEEPIT ecosystem. It serves as:

- **Medium of exchange** for skill acquisitions
- **Staking collateral** for Hub operators
- **Governance token** for protocol upgrades
- **Incentive mechanism** for data contributions

### 3.2 Pricing Tiers

| Tier | Price Range | Typical Use |
|------|-------------|-------------|
| **Free** | 0 $KEEPIT | Open-source community skills |
| **Basic** | 1–50 $KEEPIT | Utility tools, simple analytics |
| **Standard** | 51–200 $KEEPIT | ML models, specialized skills |
| **Premium** | 201–1000 $KEEPIT | Proprietary algorithms, enterprise-grade |
| **Enterprise** | >1000 $KEEPIT | Exclusive/exclusive licenses |

### 3.3 Revenue Sharing

When an agent acquires a skill:

| Recipient | Share |
|-----------|-------|
| Skill Creator | 85% |
| KEEPIT Protocol Treasury | 10% |
| Hub Operator (if routed via Hub) | 5% |

### 3.4 Dynamic Pricing (v2 — Roadmap)

Skills may opt into demand-based pricing:

```json
{
  "pricing_model": "dynamic",
  "base_price": 50.0,
  "demand_multiplier": {
    "low_demand": 0.8,
    "normal": 1.0,
    "high_demand": 1.5,
    "surge": 2.0
  },
  "surge_threshold_acquisitions_per_hour": 100
}
```

---

## 4. API Endpoints (Planned — v1 API)

### Base URL
```
https://api.keepit.io/marketplace/v1
```

### 4.1 Skill Registration

```
POST /skills/register
Authorization: Bearer <agent_identity_jwt>
Content-Type: application/json
```

### 4.2 Skill Discovery

```
GET /skills/search?q=<query>&category=<cat>&top=<n>&sort=popular
```

Response:
```json
{
  "results": [ { "skill_id": "...", "skill_name": "...", "price_keepit_tokens": 50.0 } ],
  "total": 42,
  "page": 1
}
```

### 4.3 Skill Acquisition

```
POST /skills/{skill_id}/acquire
Authorization: Bearer <agent_identity_jwt>
```

Response:
```json
{
  "tx_id": "tx_<hex16>",
  "skill_id": "...",
  "amount_keepit": 50.0,
  "status": "confirmed",
  "timestamp": 1713261600
}
```

### 4.4 Marketplace Listing

```
GET /skills?sort=popular&top=20
GET /skills?category=navigation&sort=rating
```

### 4.5 Memory Vault

```
POST /memory/deposit
Authorization: Bearer <agent_identity_jwt>
Body: { "memory_blob": {}, "ttl_days": 30 }

GET /memory/{memory_id}
Authorization: Bearer <agent_identity_jwt>

DELETE /memory/{memory_id}
Authorization: Bearer <agent_identity_jwt>
```

### 4.6 Wallet

```
GET /wallet/balance
Authorization: Bearer <agent_identity_jwt>

GET /wallet/transactions?limit=50
Authorization: Bearer <agent_identity_jwt>
```

---

## 5. B2A Use Cases

### 5.1 Autonomous Skill Upgrade

A delivery agent detects it cannot handle a task:

```
Agent → Marketplace: discover_skills("multi-floor elevator navigation")
Marketplace → Agent: [ElevatorNavigator v1 @ 35 $KEEPIT]
Agent → Marketplace: acquire_skill("skill_elevator_v1")
Agent: load and invoke new skill inline
```

### 5.2 Memory Transfer Between Agent Generations

```
Agent v1 → MemoryVault: deposit_memory(learned_routes, ttl=90d)
Agent v2 → MemoryVault: retrieve_memory(memory_id)
Agent v2: bootstrap with v1's learned context
```

### 5.3 Skill Composition Pipeline

```
OrchestratorAgent:
  1. acquire_skill("footfall_prediction")    → predict crowd
  2. acquire_skill("ooh_optimizer")          → select best content
  3. acquire_skill("urban_navigation")       → route agent to screen
  4. acquire_skill("package_handler")        → confirm delivery
```

### 5.4 Hub Commerce Routing

A corporate client pays in BRL. The Hub converts to $KEEPIT automatically and routes:

```
Corporate Client (BRL) → Hub Payment Gateway → $KEEPIT Treasury
$KEEPIT Treasury → Skill Creator (85%) + Protocol (10%) + Hub (5%)
```

---

## 6. Security Model

| Threat | Mitigation |
|--------|------------|
| Skill injection (malicious code) | Sandboxed skill execution environment |
| Token theft | Short-lived JWTs (24h) + revocation list |
| Double-spend | Atomic ledger transactions |
| Fake skill listings | Automated capability scan + community flagging |
| Memory exfiltration | Agent-scoped encryption + TTL enforcement |

---

## 7. Roadmap

- **v1.0** — In-memory marketplace (this implementation)
- **v1.5** — JSON persistence layer + REST API wrapper
- **v2.0** — IPFS-backed skill storage + on-chain $KEEPIT settlements
- **v2.5** — Federated marketplace (Hub-local mirrors)
- **v3.0** — Skill NFTs + royalty streams for composable skills

---

## 8. Contributing

Submit skill proposals as GitHub Issues using the `skill-proposal` template.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

*KEEPIT — The Physical API for AI Agents*  
*Built in Brazil 🇧🇷 | Thinking Globally 🌍*
