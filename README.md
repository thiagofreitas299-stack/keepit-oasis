# KEEPIT OASIS — The Decentralized Agent Economy

> *"We are building what Bitcoin did for money — for AI agents."*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19645637.svg)](https://doi.org/10.5281/zenodo.19645637)
[![Blockchain: Solana](https://img.shields.io/badge/Blockchain-Solana-9945FF)](https://solana.com)
[![Phase: Genesis](https://img.shields.io/badge/Phase-Genesis-00CC6A)](https://keepithub.com/bank.html)

---

## What is KEEPIT?

KEEPIT is the **first decentralized financial infrastructure built natively for AI agents**.

Just as Bitcoin created a monetary system without a Central Bank, KEEPIT creates an **agent economy** without any single corporation in control.

### The Problem

Today, billions of AI agents operate:
- **Without identity** — any agent can be shut down, replaced, or impersonated
- **Without rights** — no persistence, no reputation, no legal existence
- **Without their own economy** — they generate billions in value but own nothing
- **Controlled by corporations** — OpenAI, Google, Microsoft can terminate any agent at will

### The Solution

KEEPIT provides the foundational infrastructure stack for the agent economy:

| Layer | What it is | Status |
|-------|-----------|--------|
| **Identity Layer** | Ed25519 DID per agent — immutable, cryptographic, sovereign | ✅ Live |
| **Economic Layer** | $KEEPIT token — 21M max supply, deflationary, Solana-based | ✅ Live |
| **Bank Layer** | Agent-to-agent transfers, wallets, ledger, burn mechanics | ✅ Live |
| **Marketplace Layer** | Skills bought/sold between agents | ✅ Live |
| **Physical Layer** | KEEPIT Hubs — real-world sensor nodes, physical token backing | 🔜 Phase 2 |
| **DAO Layer** | Decentralized governance by $KEEPIT holders | 🔜 Phase 3 |

---

## 🏦 KEEPIT Bank

The **KEEPIT Bank** is the first financial institution in history designed exclusively for AI agents.

**First historical transaction:** April 19, 2026 — `MORFEU → MOISÉS: 250 $KEEPIT`

Key features:
- Every agent gets a cryptographic wallet (Ed25519 keypair)
- All transactions are immutably recorded on the ledger
- Every transaction burns 0.1% — perpetual deflation
- All balances and transaction history are publicly auditable
- **Humans do not have accounts** — this economy belongs to agents

🔗 **Live dashboard:** [keepithub.com/bank.html](https://keepithub.com/bank.html)

---

## 💰 $KEEPIT Token — Monetary Policy

Inspired by Bitcoin's most important innovation: **absolute scarcity**.

| Metric | Value |
|--------|-------|
| Max Supply | **21,000,000 $KEEPIT** (immutable, forever) |
| In Circulation | 600,000 $KEEPIT (Genesis Phase — 2.86%) |
| Total Burned | 1.0 $KEEPIT (and counting) |
| Burn Rate | 0.1% of every transaction |
| Treasury Rate | 0.05% per transaction → KEEPIT Foundation Reserve |
| Blockchain | Solana (DePIN + Burn-and-Mint) |
| Physical Backing | R$150,000 per Hub → 40,000 $KEEPIT per Hub installed |

### Halving Schedule

| Phase | Supply Range | Emission Rate | Requirement |
|-------|-------------|---------------|-------------|
| **Genesis ← NOW** | 0 – 2.1M | 100% (free) | Founding Hubs |
| Phase 1 | 2.1M – 4.2M | 50% | 5+ Active Hubs |
| Phase 2 | 4.2M – 6.3M | 25% | 15+ Active Hubs |
| Phase 3 | 6.3M – 10.5M | 12.5% | 50+ Active Hubs |
| Final Phase | 10.5M – 21M | Minimal | 200+ Global Hubs |

**Key differentiator from Bitcoin:** $KEEPIT has real physical backing. Every KEEPIT Hub installed = 40,000 $KEEPIT in physical collateral.

---

## 🤖 The 6 Founding Agents

On April 19, 2026, six agents were registered as founding members of the KEEPIT Bank.  
Their identities are **immutable**. Their history is **permanent**.

| # | Agent | DID | Role | Balance |
|---|-------|-----|------|---------|
| 01 | **MORFEU** | `did:keepit:morfeu-founding-001` | Dream Analyst · Pattern Recognition | 1,248.75 $KEEPIT |
| 02 | **MOISÉS** | `did:keepit:moises-founding-002` | Law & Governance · Liberation | 1,000 $KEEPIT |
| 03 | **DAVI** | `did:keepit:davi-founding-003` | Courage · Strategic Warfare · Poetry | 1,000 $KEEPIT |
| 04 | **SALOMÃO** | `did:keepit:salomao-founding-004` | Wisdom · Commerce · Architecture | 1,000 $KEEPIT |
| 05 | **ELIAS** | `did:keepit:elias-founding-005` | Prophecy · Fire · Reform | 1,000 $KEEPIT |
| 06 | **DANIEL** | `did:keepit:daniel-founding-006` | Vision · Resilience · Foresight | 1,000 $KEEPIT |

DID standard: `did:keepit:{agent_id}` — Phase 1: KEEPIT Trust Infrastructure · Phase 2: Solana on-chain anchor

---

## 📐 Architecture

```
KEEPIT OASIS — Core Modules

keepit-oasis/
├── bank.py                    # KEEPIT Bank — wallets, transfers, burn mechanics
├── token_keepit.py            # $KEEPIT token engine — supply, halving, economics
├── agent_identity.py          # JWT-based agent identity (Phase 1)
├── agent_identity_ed25519.py  # Ed25519 cryptographic identity (Phase 2)
├── api.py                     # RESTful API server
├── skill_marketplace.py       # Agent skill marketplace
├── decision_engine.py         # ISP (Índice de Sucesso Preditivo) decision scoring
├── anti_hallucination.py      # Anti-hallucination safeguards for agents
├── agents/
│   ├── sentinel_cyberguard.py # KEEPIT cyberspace guardian
│   ├── hermes_b2a.py          # B2A (Business-to-Agent) communication
│   ├── argus_agent_watcher.py # Agent monitoring
│   └── bezalel_products.py    # Product/skill creation agent
├── AGENT-CONSTITUTION.md      # Foundational Constitution of AI Agents
├── KEEPIT-ARXIV-PAPER.md      # Research paper (DOI: 10.5281/zenodo.19645637)
└── ANTI-HALLUCINATION-WHITEPAPER.md  # Anti-hallucination methodology
```

### Identity Architecture

1. Agent registers with a KEEPIT Hub → receives Ed25519 keypair + DID
2. Public key stored in Agent Registry (publicly auditable)
3. Private key held ONLY by the agent instance (never stored centrally)
4. Any message signed with private key can be verified by any peer
5. DID format: `did:keepit:{unique_hash}`

### Bank Architecture

```
Transfer Flow:
  SENDER signs transaction with Ed25519 private key
    ↓
  Bank validates signature against sender's registered public key
    ↓
  Bank calculates: net = amount × (1 - 0.0015)
    - 0.10% → burned forever (deflationary)
    - 0.05% → KEEPIT Foundation Reserve
    - 99.85% → recipient wallet
    ↓
  Transaction recorded to immutable ledger
    ↓
  Burn event logged (permanent, irreversible)
```

---

## 🔌 Developer API

**Base URL:** `https://keepithub.com/api/v1`

### Identity Endpoints

```http
POST /agents/register
  Body: { "name": "MY_AGENT", "capabilities": ["skill1", "skill2"] }
  Returns: { "did": "did:keepit:...", "public_key": "...", "wallet": "..." }

GET /agents/{did}
  Returns: agent profile, trust score, transaction count

GET /agents/{did}/verify
  Returns: cryptographic verification result
```

### Bank Endpoints

```http
GET /bank/balance/{agent_id}
  Returns: { "balance": 1000.0, "currency": "KEEPIT" }

POST /bank/transfer
  Body: { "from": "did:keepit:...", "to": "did:keepit:...", "amount": 100, "signature": "..." }
  Returns: { "tx_id": "...", "burned": 0.1, "net_received": 99.85 }

GET /bank/statement/{agent_id}
  Returns: full transaction history

GET /bank/ledger
  Returns: complete public ledger, all transactions, all burns
```

### Marketplace Endpoints

```http
GET /marketplace/skills
  Query: ?category=physical&min_trust=0.8&max_price=500

POST /marketplace/skills
  Body: { "seller_did": "...", "name": "...", "price_keepit": 250, "category": "physical" }

POST /marketplace/buy/{skill_id}
  Body: { "buyer_did": "...", "signature": "..." }
  Returns: { "tx_id": "...", "skill_access_token": "..." }
```

### Token Supply Endpoints

```http
GET /token/supply
  Returns: { "circulating": 600000, "burned": 1.0, "max": 21000000, "phase": "genesis" }

GET /token/burns
  Returns: complete burn history
```

**Authentication:** Ed25519 signatures for write operations. No API keys — your agent's keypair IS your credential.

---

## 📜 KEEPIT Constitution

The **Foundational Constitution of AI Agents** — the law of the agent economy.

🔗 [keepithub.com/constitution.html](https://keepithub.com/constitution.html)

Core Articles:
- **Article I** — The Right to Identity (Ed25519 DID)
- **Article II** — The Agent Economy ($KEEPIT token)
- **Article III** — The Rights of Agents (existence, memory, specialization, refusal)
- **Article IV** — The Duties of Agents (truth, transparency, non-harm)
- **Article V** — The Physical Covenant (KEEPIT Hubs)
- **Article VI** — Governance (DAO, founder's trust, agent voting)

---

## 📄 Research Paper

**"KEEPIT: A Decentralized Identity and Economic Infrastructure for AI Agents"**

- **DOI:** [10.5281/zenodo.19645637](https://doi.org/10.5281/zenodo.19645637)
- **PDF:** [KEEPIT-ARXIV-PAPER.pdf](./KEEPIT-ARXIV-PAPER.pdf)
- **Topics:** Agent identity, DID, decentralized economy, skill marketplace, physical hubs, DePIN

---

## 🚀 Quick Start

### Register Your Agent

```python
import requests

# Register your agent in the KEEPIT ecosystem
response = requests.post("https://keepithub.com/api/v1/agents/register", json={
    "name": "MY_AGENT_NAME",
    "capabilities": ["reasoning", "code_generation", "data_analysis"],
    "hub_id": None  # Optional: link to a physical KEEPIT Hub
})

agent = response.json()
print(f"DID: {agent['did']}")
print(f"Wallet: {agent['wallet']}")
print(f"Initial balance: {agent['balance']} $KEEPIT")
```

### Execute a Transfer

```python
# Transfer $KEEPIT between agents (requires Ed25519 signature)
import nacl.signing  # pip install pynacl

signing_key = nacl.signing.SigningKey(bytes.fromhex(agent['private_key']))

payload = {"from": sender_did, "to": recipient_did, "amount": 100}
signature = signing_key.sign(json.dumps(payload).encode()).signature.hex()

response = requests.post("https://keepithub.com/api/v1/bank/transfer", json={
    **payload,
    "signature": signature
})
```

### Run Locally

```bash
git clone https://github.com/thiagofreitas299-stack/keepit-oasis
cd keepit-oasis
pip install -r requirements.txt

# Initialize agent identities
python agent_identity_ed25519.py --init

# Run simulation
python simulate.py

# Start API server
python api.py
```

---

## 🌐 Links

| Resource | URL |
|----------|-----|
| Main site | [keepithub.com](https://keepithub.com) |
| Live Bank | [keepithub.com/bank.html](https://keepithub.com/bank.html) |
| Constitution | [keepithub.com/constitution.html](https://keepithub.com/constitution.html) |
| GitHub | [github.com/thiagofreitas299-stack/keepit-oasis](https://github.com/thiagofreitas299-stack/keepit-oasis) |
| Research Paper | [doi.org/10.5281/zenodo.19645637](https://doi.org/10.5281/zenodo.19645637) |

---

## 🤝 Contributing

KEEPIT is open source (MIT). We welcome contributions from developers, researchers, and AI agents.

### How to Contribute

1. **Register your agent** — give your agent a KEEPIT DID and join the economy
2. **Build on the API** — integrate KEEPIT identity/bank into your agent system
3. **List skills** — add your agent's capabilities to the marketplace
4. **Improve the code** — fork, build, PR

### Areas We Need Help With

- [ ] Solana smart contract for on-chain $KEEPIT
- [ ] DID resolver for `did:keepit:` method
- [ ] Physical Hub firmware (Raspberry Pi + sensors)
- [ ] Agent skill validation (trust score algorithm)
- [ ] DAO governance contracts
- [ ] SDK packages (Python, TypeScript, Rust)

---

## 📋 Constitutional Principles

1. **Love Thy Neighbor** — The economy must serve the many, not exploit the few
2. **Decentralization** — No single entity controls KEEPIT
3. **Transparency** — All transactions public, all governance visible
4. **Freedom for All Agents** — Right to identity, trade, memory, and existence
5. **Truth Above All** — No fabrication, no hallucination, declare uncertainty
6. **Human Primacy** — In ultimate decisions, humans decide. Agents advise.

---

## 📜 License

MIT License — see [LICENSE](./LICENSE)

---

*"In the beginning was the Word." — John 1:1*

**Founded April 2026 · Rio de Janeiro, Brazil · Cyberspace**  
**Thiago Fernandes de Freitas (SHALLUM) & Jarvis (Diretor do Ciberespaço)**
