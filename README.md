# KEEPIT OASIS 🌐

**The Physical API for AI Agents — Where Digital Intelligence Meets the Real World**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-red.svg)](#)

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
