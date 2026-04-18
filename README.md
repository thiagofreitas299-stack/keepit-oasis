# KEEPIT OASIS 🌐

**The Physical API for AI Agents — Where Digital Intelligence Meets the Real World**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Zenodo DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.19645637-blue.svg)](https://zenodo.org/records/19645637)
[![Paper](https://img.shields.io/badge/Paper-CERN%20Zenodo-brightgreen.svg)](https://zenodo.org/records/19645637)

---

## 🧠 Solving AI Agent Hallucination

> **27% of LLM responses in production contain factual errors.**  
> KEEPIT Hubs are the grounding infrastructure that fixes this.

KEEPIT acts as a **verified memory layer** between AI agents and the real world:
- Agents query KEEPIT before responding → responses grounded in verified facts
- Physical Hubs continuously update verified local knowledge
- Skills in the marketplace are tested and certified — not just uploaded
- Three tiers: Free (community) · Standard (hub-verified) · Premium (real-time physical)

**Result:** AI agents that businesses can actually trust.

---

## What is KEEPIT OASIS?

KEEPIT OASIS is an open-source framework that bridges **AI agents, World Models, and the physical world**.

While platforms like MiroFish OASIS simulate physical spaces digitally, KEEPIT goes one step further: we provide the actual physical infrastructure that makes those simulations real.

> *"Everyone is building the digital brain. We're building the physical body where that brain will live."*
> — Thiago Freitas, Founder

---

## The Problem We Solve

AI agents today are trapped in the digital world. They can reason, plan, and decide — but they cannot:
- Receive a physical package
- Display content on a real urban screen
- Interact with a human in a specific location
- Execute transactions that require physical presence

**KEEPIT Hubs are the physical endpoints for AI agents in the real world.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│          AI Agents / World Models / Metaverse           │
│     (MiroFish OASIS, World Labs, NVIDIA Omniverse...)   │
└────────────────────────┬────────────────────────────────┘
                         │  KEEPIT API (cyberspace layer)
┌────────────────────────▼────────────────────────────────┐
│                  KEEPIT OASIS Engine                    │
│  • Location Intelligence  • Dynamic Pricing Engine      │
│  • Agent Commerce Layer   • Urban Flow Modeling         │
│  • Demand Simulation      • Real-time Heat Mapping      │
└────────────────────────┬────────────────────────────────┘
                         │  Physical execution layer
┌────────────────────────▼────────────────────────────────┐
│                   KEEPIT Hub (physical)                 │
│  • 24/7 operation    • Edge AI onboard                  │
│  • IoT + 5G ready    • OOH intelligent screens         │
│  • Agent endpoints   • Human-in-the-loop gateway       │
└─────────────────────────────────────────────────────────┘
```

---

## 5 Revenue Streams (Dynamic Pricing)

KEEPIT Hubs use **airline-style dynamic pricing** — price adapts in real-time based on:
- Local heat map (footfall, demographics)
- Connected agent profiles
- Search and behavior patterns
- Corporate contracts active
- Seasonal events

| Stream | What it is | Pricing model |
|--------|-----------|---------------|
| **Space/Storage** | Physical space for any use case | Dynamic R$10–150/use |
| **OOH Intelligence** | Smart advertising screens with audience detection | Dynamic CPM by profile |
| **Brand Activation** | Companies activate experiences at the Hub | R$5k–50k/month contracts |
| **Agent Commerce (B2A)** | AI agents executing physical-world transactions | R$2–25/agent operation |
| **Human-in-the-Loop** | Verified humans available for tasks requiring physical presence | R$15–200/hour |

---

## OASIS Simulation Engine

The core of KEEPIT OASIS is an **urban location intelligence model** that predicts Hub performance at any urban point worldwide.

### Methodology

**Stacking Ensemble (3 models)**
- Random Forest → non-linear footfall patterns (40% weight)
- Gradient Boosting → error correction layer (35% weight)
- Linear Regression → baseline revenue trend (25% weight)

**Explainability: SHAP**
Every prediction comes with a SHAP explanation — not just *what* the model predicts, but *why*.

**Data sources**
- ABRASCE (Brazilian Shopping Center Association) — certified mall traffic
- Metrô Rio & SPTrans — public transit ridership
- IBGE — urban flow and demographic models
- Real-time event calendars

**Model accuracy: R² = 97.6%** (on training set with seed=42 for reproducibility)

---

## Quick Start

```bash
git clone https://github.com/thiagofreitas299-stack/keepit-oasis
cd keepit-oasis
pip install -r requirements.txt
python simulate.py --location "Copacabana Metro" --footfall 62000
```

**Sample output:**
```json
{
  "location": "Copacabana Metro",
  "monthly_revenue": {
    "optimistic": "R$67,448,119",
    "base_case": "R$13,489,624",
    "conservative": "R$6,744,812"
  },
  "nps_estimate": 99.4,
  "payback_days": {
    "base_case": 11,
    "conservative": 22
  },
  "shap_explanation": {
    "footfall_contribution": 0.67,
    "adoption_rate_contribution": 0.21,
    "nps_multiplier": 0.08,
    "event_premium": 0.04
  }
}
```

---

## API (Coming Soon)

```
GET /api/v1/simulate?location=copacabana&footfall=62000&city=rio
GET /api/v1/cities/brazil/hotspots?top=50
POST /api/v1/hub/register   # Register a virtual Hub location
GET  /api/v1/hub/{id}/demand # Real-time demand data
```

**Free tier:** 100 requests/day
**Premium:** Unlimited + real-time data + custom reports

---

## The Bigger Vision: Physical-Digital Fusion

The Metaverse failed because it had no connection to the physical world.
World Models are powerful but live only in the digital realm.

**KEEPIT is the bridge.**

When an AI agent inside MiroFish OASIS needs to store a package in São Paulo, it calls the KEEPIT API → the nearest Hub executes the action → the agent gets confirmation. No human in the loop.

This is **B2A (Business-to-Agent)** commerce — a market that doesn't exist yet. KEEPIT is building the infrastructure layer before the market arrives.

---

## Roadmap

- [x] **Phase 0** — Open source simulation engine (this repo)
- [ ] **Phase 1** — Public API launch (30 days)
- [ ] **Phase 2** — Technical paper on arXiv (60 days)
- [ ] **Phase 3** — Virtual Hub #0 waitlist (90 days)
- [ ] **Phase 4** — Seed funding round (120 days)
- [ ] **Phase 5** — First physical Hubs deployed (180 days)

---

## Contributing

We welcome contributions from AI researchers, urban data scientists, and developers building on top of World Models.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License — free to use, modify, and distribute.

See [LICENSE](LICENSE) for details.

---

## About

**KEEPIT** — globalkeepit.com
Built in Brazil 🇧🇷 | Thinking globally 🌍

*The physical infrastructure layer for the AI agent economy.*

---

## The KEEPIT Stack

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Stars Welcome](https://img.shields.io/badge/Stars-Welcome-yellow?logo=github)](https://github.com/thiagofreitas299-stack/keepit-oasis)

The KEEPIT ecosystem now includes three foundational modules:

| Module | File | Purpose |
|--------|------|---------|
| **Skill Marketplace** | `skill_marketplace.py` | B2A skill registry — agents buy/sell AI capabilities in $KEEPIT tokens |
| **World Model Cities** | `world_model_cities.py` | Urban Digital Twin — real-time city state from Hub sensor networks |
| **Agent Identity** | `agent_identity.py` | JWT-based identity and access control for the KEEPIT agent network |

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent Economy                           │
│   (buy skills · execute tasks · earn $KEEPIT · persist memory) │
└───────────┬───────────────────────┬────────────────────────────┘
            │                       │
    ┌───────▼──────┐     ┌──────────▼────────┐
    │   Skill       │     │  Agent Identity   │
    │  Marketplace  │     │  Layer (JWT)      │
    │  skill_mkt.py │     │  agent_identity.py│
    └───────┬───────┘     └──────────┬────────┘
            │                        │
    ┌───────▼────────────────────────▼────────┐
    │         World Model Cities              │
    │         world_model_cities.py           │
    │   (São Paulo · Rio de Janeiro · …)      │
    └───────────────────┬─────────────────────┘
                        │
    ┌───────────────────▼─────────────────────┐
    │            KEEPIT Hubs                  │
    │   (Physical endpoints · IoT · 5G)       │
    └─────────────────────────────────────────┘
```

---

## Skill Marketplace

The **KEEPIT Skill Marketplace** is an open-source B2A infrastructure where AI agents can:

- 📦 **Register** skills as monetizable assets
- 🔍 **Discover** skills via keyword search (semantic in v2)
- 💳 **Acquire** skills by transferring $KEEPIT tokens
- 🧠 **Vault** and retrieve episodic memory between sessions

### Quick Start

```bash
python skill_marketplace.py
```

### Example

```python
from skill_marketplace import KEEPITSkillMarketplace

market = KEEPITSkillMarketplace()  # 10 skills pre-loaded

# Discover navigation skills
results = market.discover_skills("urban navigation transit")
print(results[0].skill_name)  # Urban Navigation v2

# Acquire a skill
tx = market.acquire_skill("my_agent", results[0].skill_id)
print(f"Acquired for {tx.amount_keepit} $KEEPIT — TX: {tx.tx_id}")

# Vault a memory blob
vault = market.deposit_memory("my_agent", {"learned_route": "linha_1"}, ttl_days=7)
mem = market.retrieve_memory("my_agent", vault.memory_id)
```

See [SKILL_MARKETPLACE_SPEC.md](SKILL_MARKETPLACE_SPEC.md) for the full technical specification.

---

## World Model Cities

The **KEEPIT World Model** turns Hub sensor networks into a living Urban Digital Twin.
Each Hub node continuously ingests footfall, weather, events, air quality, and traffic data.

### Synthetic data included for:
- 🌆 **São Paulo** — 7 hubs (Paulista, Berrini, Faria Lima, República, Sé, Vila Madalena)
- 🏖️ **Rio de Janeiro** — 5 hubs (Copacabana, Ipanema, Centro, Barra, Tijuca)

### Quick Start

```bash
python world_model_cities.py
```

### Example

```python
from world_model_cities import KEEPITWorldModel

model = KEEPITWorldModel()  # São Paulo + Rio pre-seeded

# Query live city state
state = model.query_city_state("São Paulo", radius_km=10.0)
print(f"Footfall last hour: {state['footfall_last_hour']:,}")

# Generate snapshot
snap = model.generate_city_snapshot("Rio de Janeiro")
print(f"Hotspots: {len(snap.hotspots)} | Alerts: {snap.alerts}")

# Predict pedestrian flow
pred = model.predict_urban_flow((-22.9714, -43.1824), hour=18)
print(f"Predicted: {pred['predicted_footfall']:,} pedestrians at 18:00")
```

---

## Agent Identity Layer

Every KEEPIT agent has a **cryptographically verifiable identity** via HMAC-SHA256 signed JWTs (pure stdlib — no dependencies).

### Quick Start

```bash
python agent_identity.py
```

### Example

```python
from agent_identity import KEEPITIdentityRegistry

registry = KEEPITIdentityRegistry()

# Create agent identity
token = registry.create_agent_identity(
    agent_name="DeliveryBot-SP-001",
    capabilities=["navigation", "logistics"],
    home_hub="hub_sp_paulista_01",
)

# Verify identity (any Hub can do this without a central server)
claims = registry.verify_agent(token)
print(claims["capabilities"])  # ['navigation', 'logistics']

# Grant scoped hub access
access = registry.grant_hub_access(
    claims["sub"], "hub_sp_berrini_01",
    scopes=["read:footfall", "write:commerce"]
)

# Revoke when done
registry.revoke_access(claims["sub"], "hub_sp_berrini_01")
```

---

## 🌍 Multilingual / Multilingue / 多语言

### 🇬🇧 English

KEEPIT is building the physical infrastructure layer for the AI agent economy. Our open-source simulation engine, skill marketplace, and world model are freely available for researchers, developers, and urban innovators worldwide.

> *"The Metaverse failed because it had no connection to the physical world. KEEPIT is the bridge."*

### 🇧🇷 Português

KEEPIT está construindo a camada de infraestrutura física para a economia de agentes de IA. Nosso motor de simulação, marketplace de skills e modelo do mundo estão disponíveis gratuitamente para pesquisadores, desenvolvedores e inovadores urbanos.

> *"O Metaverso falhou porque não tinha conexão com o mundo físico. A KEEPIT é essa ponte."*

### 🇨🇳 中文

KEEPIT正在为AI智能体经济构建物理基础设施层。我们的开源模拟引擎、技能市场和城市世界模型向全球研究人员、开发者和城市创新者免费开放。

> *「元宇宙的失败在于它与现实世界脱节。KEEPIT就是那座桥梁。」*

---

*KEEPIT — globalkeepit.com | Built in Brazil 🇧🇷 | Thinking globally 🌍*
