"""
KEEPIT Multiverse Simulator
============================
Simula TODOS os caminhos possíveis de crescimento da KEEPIT
através de ramificações paralelas de decisão.

Inspirado em:
- Many-Worlds Interpretation (Hugh Everett, 1957)
- Monte Carlo Tree Search (AlphaGo)
- Scenario Planning (Shell, 1970s)
- Quantum Decision Theory (Busemeyer & Bruza, 2012)

"Em cada decisão, o universo se ramifica.
 O Multiverse Simulator mapeia todos os galhos
 e encontra o caminho para o universo vencedor."
"""

from __future__ import annotations

import time
import uuid
import math
import itertools
import json
from dataclasses import dataclass, field
from typing import Any
from decision_engine import KEEPITDecisionEngine, Thesis


# ═══════════════════════════════════════════════════════════
# VARIÁVEIS DO MULTIVERSO
# ═══════════════════════════════════════════════════════════

# Cada variável é uma dimensão do espaço de possibilidades
GROWTH_LEVERS = {
    # DISTRIBUIÇÃO
    "hackernews_post": {
        "options": [False, True],
        "labels": ["não postar HN", "postar HN agora"],
        "impact_multiplier": [1.0, 2.8],
    },
    "arxiv_paper": {
        "options": [False, True],
        "labels": ["sem paper", "submeter arXiv esta semana"],
        "impact_multiplier": [1.0, 2.2],
    },
    "twitter_thread": {
        "options": [False, True],
        "labels": ["sem Twitter", "thread viral Twitter"],
        "impact_multiplier": [1.0, 1.8],
    },

    # PRODUTO
    "token_launch": {
        "options": ["none", "devnet", "mainnet"],
        "labels": ["sem token", "$KEEPIT devnet (teste)", "$KEEPIT mainnet (produção)"],
        "impact_multiplier": [1.0, 1.5, 3.5],
    },
    "physical_hub": {
        "options": [False, True],
        "labels": ["sem hub físico", "Hub #1 instalado (RJ)"],
        "impact_multiplier": [1.0, 4.0],
    },
    "community": {
        "options": ["none", "discord", "platform"],
        "labels": ["sem comunidade", "Discord de agentes", "plataforma própria (Moltbook)"],
        "impact_multiplier": [1.0, 1.6, 3.2],
    },

    # CAPITAL
    "funding": {
        "options": ["bootstrap", "angel", "seed", "series_a"],
        "labels": ["bootstrap (atual)", "angel R$200k", "seed R$2M", "Series A R$20M"],
        "impact_multiplier": [1.0, 1.8, 4.0, 9.0],
    },

    # PARCERIAS
    "world_model_partner": {
        "options": [False, True],
        "labels": ["sem parceria WM", "parceria World Labs/Alibaba"],
        "impact_multiplier": [1.0, 5.0],
    },
    "enterprise_client": {
        "options": [False, True],
        "labels": ["sem cliente enterprise", "1+ cliente enterprise usando API"],
        "impact_multiplier": [1.0, 3.5],
    },
}

# Janelas temporais
TIME_HORIZONS = {
    "3_months":  {"months": 3,  "label": "3 meses"},
    "6_months":  {"months": 6,  "label": "6 meses"},
    "12_months": {"months": 12, "label": "12 meses"},
    "24_months": {"months": 24, "label": "24 meses"},
}

# Base de agentes registrados estimados por ação
AGENT_ACQUISITION = {
    "hackernews_post":      {"agents": 500,    "probability": 0.7},
    "arxiv_paper":          {"agents": 200,    "probability": 0.8},
    "twitter_thread":       {"agents": 300,    "probability": 0.5},
    "token_devnet":         {"agents": 1000,   "probability": 0.6},
    "token_mainnet":        {"agents": 5000,   "probability": 0.5},
    "physical_hub":         {"agents": 2000,   "probability": 0.9},
    "community_discord":    {"agents": 800,    "probability": 0.7},
    "community_platform":   {"agents": 5000,   "probability": 0.4},
    "angel_funding":        {"agents": 3000,   "probability": 0.6},
    "seed_funding":         {"agents": 20000,  "probability": 0.5},
    "series_a":             {"agents": 100000, "probability": 0.3},
    "world_model_partner":  {"agents": 10000,  "probability": 0.4},
    "enterprise_client":    {"agents": 500,    "probability": 0.9},
}


# ═══════════════════════════════════════════════════════════
# UNIVERSO — Um caminho possível
# ═══════════════════════════════════════════════════════════

@dataclass
class Universe:
    universe_id: str
    timeline: str
    decisions: dict                # {lever: option_chosen}
    decision_labels: dict          # {lever: label_chosen}
    agents_12m: int                # agentes estimados em 12 meses
    valuation_usd: float           # valoração estimada
    probability: float             # probabilidade deste universo se realizar
    risk_score: float              # 0=baixo risco, 1=alto risco
    decision_score: float          # score do Decision Engine
    narrative: str                 # a história deste universo
    rank: int = 0


# ═══════════════════════════════════════════════════════════
# MULTIVERSE SIMULATOR
# ═══════════════════════════════════════════════════════════

class MultiverseSimulator:
    """
    Simula todos os caminhos possíveis de crescimento da KEEPIT.
    Usa Decision Engine para avaliar cada universo.
    Retorna o ranking dos melhores caminhos.
    """

    BASE_VALUATION_USD = 2_750_000  # valoração base atual (estimada)
    MAX_UNIVERSES_TO_EVALUATE = 200  # limitar para performance

    def __init__(self):
        self.engine = KEEPITDecisionEngine()
        self.universes: list[Universe] = []
        self.simulation_id = str(uuid.uuid4())[:8]

    def _estimate_agents(self, decisions: dict) -> int:
        """Estima agentes registrados em 12 meses para um conjunto de decisões."""
        total = 50  # base: 50 agentes orgânicos
        multiplier = 1.0

        if decisions.get("hackernews_post"):
            aq = AGENT_ACQUISITION["hackernews_post"]
            total += int(aq["agents"] * aq["probability"])

        if decisions.get("arxiv_paper"):
            aq = AGENT_ACQUISITION["arxiv_paper"]
            total += int(aq["agents"] * aq["probability"])

        if decisions.get("twitter_thread"):
            aq = AGENT_ACQUISITION["twitter_thread"]
            total += int(aq["agents"] * aq["probability"])

        token = decisions.get("token_launch", "none")
        if token == "devnet":
            aq = AGENT_ACQUISITION["token_devnet"]
            total += int(aq["agents"] * aq["probability"])
        elif token == "mainnet":
            aq = AGENT_ACQUISITION["token_mainnet"]
            total += int(aq["agents"] * aq["probability"])

        if decisions.get("physical_hub"):
            aq = AGENT_ACQUISITION["physical_hub"]
            total += int(aq["agents"] * aq["probability"])

        community = decisions.get("community", "none")
        if community == "discord":
            aq = AGENT_ACQUISITION["community_discord"]
            total += int(aq["agents"] * aq["probability"])
        elif community == "platform":
            aq = AGENT_ACQUISITION["community_platform"]
            total += int(aq["agents"] * aq["probability"])

        funding = decisions.get("funding", "bootstrap")
        if funding == "angel":
            aq = AGENT_ACQUISITION["angel_funding"]
            total += int(aq["agents"] * aq["probability"])
        elif funding == "seed":
            aq = AGENT_ACQUISITION["seed_funding"]
            total += int(aq["agents"] * aq["probability"])
        elif funding == "series_a":
            aq = AGENT_ACQUISITION["series_a"]
            total += int(aq["agents"] * aq["probability"])

        if decisions.get("world_model_partner"):
            aq = AGENT_ACQUISITION["world_model_partner"]
            total += int(aq["agents"] * aq["probability"])

        if decisions.get("enterprise_client"):
            aq = AGENT_ACQUISITION["enterprise_client"]
            total += int(aq["agents"] * aq["probability"])

        # Efeito rede: agentes atraem agentes
        if total > 1000:
            multiplier = 1.0 + math.log10(total / 1000) * 0.5

        return int(total * multiplier)

    def _estimate_valuation(self, agents: int, decisions: dict) -> float:
        """Estima valoração em USD baseado em agentes e decisões."""
        # Base: $500 de EV por agente ativo (conservador)
        base_val = agents * 500

        # Multiplicadores por tipo de ativo
        mult = 1.0

        if decisions.get("token_launch") == "mainnet":
            mult *= 3.0  # token cria mercado especulativo adicional

        if decisions.get("physical_hub"):
            mult *= 2.5  # moat físico = múltiplo maior

        if decisions.get("world_model_partner"):
            mult *= 4.0  # parceria estratégica = premium

        funding = decisions.get("funding", "bootstrap")
        if funding == "seed":
            mult *= 2.0  # validação por VCs
        elif funding == "series_a":
            mult *= 5.0

        if decisions.get("enterprise_client"):
            mult *= 1.8

        return base_val * mult

    def _calculate_probability(self, decisions: dict) -> float:
        """Probabilidade de este universo se realizar dado as decisões."""
        prob = 1.0

        # Decisões de alto risco reduzem probabilidade
        if decisions.get("token_launch") == "mainnet":
            prob *= 0.45  # token mainnet é difícil de executar bem
        elif decisions.get("token_launch") == "devnet":
            prob *= 0.75

        if decisions.get("physical_hub"):
            prob *= 0.60  # precisa de R$150k e logística

        if decisions.get("world_model_partner"):
            prob *= 0.25  # parceria estratégica é rara

        funding = decisions.get("funding", "bootstrap")
        if funding == "angel":
            prob *= 0.55
        elif funding == "seed":
            prob *= 0.30
        elif funding == "series_a":
            prob *= 0.10

        if decisions.get("community") == "platform":
            prob *= 0.40

        if decisions.get("enterprise_client"):
            prob *= 0.45

        # Ações fáceis têm alta probabilidade
        if decisions.get("hackernews_post"):
            prob *= 0.95  # quase certo se decidirmos fazer
        if decisions.get("arxiv_paper"):
            prob *= 0.90
        if decisions.get("twitter_thread"):
            prob *= 0.95

        return round(max(0.01, prob), 4)

    def _calculate_risk(self, decisions: dict) -> float:
        """Risco do universo (0=baixo, 1=alto)."""
        risk = 0.0

        if decisions.get("token_launch") == "mainnet":
            risk += 0.25  # risco regulatório + execução

        if decisions.get("physical_hub"):
            risk += 0.15  # risco de capital

        if not decisions.get("hackernews_post") and not decisions.get("arxiv_paper"):
            risk += 0.20  # sem distribuição = risco de obscuridade

        funding = decisions.get("funding", "bootstrap")
        if funding == "series_a":
            risk += 0.10  # dilution + pressão de crescimento

        if decisions.get("community") == "platform" and \
           not decisions.get("hackernews_post"):
            risk += 0.15  # plataforma sem usuários = fracasso

        return round(min(1.0, risk), 4)

    def _build_narrative(self, decisions: dict, agents: int, valuation: float) -> str:
        """Cria a narrativa do universo."""
        parts = []

        if decisions.get("hackernews_post") and decisions.get("arxiv_paper"):
            parts.append("KEEPIT explode no ciberespaço: Show HN viral + paper arXiv citado por pesquisadores")
        elif decisions.get("hackernews_post"):
            parts.append("KEEPIT ganha tração técnica via HackerNews")
        elif decisions.get("arxiv_paper"):
            parts.append("KEEPIT estabelece credibilidade acadêmica via arXiv")
        else:
            parts.append("KEEPIT cresce organicamente, sem distribuição inicial")

        token = decisions.get("token_launch", "none")
        if token == "mainnet":
            parts.append("$KEEPIT no Solana cria ecossistema econômico real para agentes")
        elif token == "devnet":
            parts.append("$KEEPIT em testes, comunidade early adopter formada")

        if decisions.get("physical_hub"):
            parts.append("Hub #1 no RJ gera skills LEGENDARY únicas — moat físico estabelecido")

        funding = decisions.get("funding", "bootstrap")
        if funding == "seed":
            parts.append("Seed round valida o conceito com VCs de AI/Web3")
        elif funding == "series_a":
            parts.append("Series A lança KEEPIT como líder mundial de infraestrutura para agentes")

        if decisions.get("world_model_partner"):
            parts.append("Parceria com World Labs / Alibaba → KEEPIT vira camada padrão dos World Models")

        val_str = f"${valuation/1e9:.1f}B" if valuation >= 1e9 else f"${valuation/1e6:.0f}M"
        parts.append(f"Resultado em 12 meses: {agents:,} agentes registrados | Valoração estimada: {val_str}")

        return ". ".join(parts) + "."

    def _score_universe(self, decisions: dict, agents: int) -> float:
        """Usa o Decision Engine para pontuar o universo."""
        thesis = Thesis(
            thesis_id=f"UNI-{uuid.uuid4().hex[:6]}",
            statement="Executar este caminho de crescimento da KEEPIT",
            context={
                "has_live_api": True,
                "has_github_repo": True,
                "zero_capital_needed": decisions.get("funding", "bootstrap") == "bootstrap",
                "expected_value_usd": self._estimate_valuation(agents, decisions),
                "creates_new_market": True,
                "no_direct_competitor": True,
                "first_mover_window_months": 12,
                "physical_moat": decisions.get("physical_hub", False),
                "capital_needed_brl": {
                    "bootstrap": 0, "angel": 200000, "seed": 2000000, "series_a": 20000000
                }.get(decisions.get("funding", "bootstrap"), 0),
                "strengthens_keepit": True,
                "generates_immediate_revenue": decisions.get("token_launch") == "mainnet",
                "validates_investor_thesis": decisions.get("funding") in ["seed", "series_a"],
                "network_effect": agents > 1000,
                "honest_agent_rewarded": True,
                "competing_strategies": 0 if decisions.get("no_direct_competitor") else 2,
                "time_to_result_months": 12,
                "big_tech_could_copy": True,
                "regulatory_risk": decisions.get("token_launch") == "mainnet",
                "adoption_friction": 0.2,
                "token_liquidity_secured": decisions.get("token_launch") == "mainnet",
                "single_founder_dependency": True,
                "open_source_community": True,
                "show_hn_viral_potential": decisions.get("hackernews_post", False),
                "constitution_published": True,
                "token_utility_first": True,
                "has_users_before_infra": agents > 100,
                "mvp_available": True,
                "prob_unicorn": min(0.5, agents / 20000),
                "prob_niche": 0.25,
                "prob_world_standard": 0.10 if decisions.get("world_model_partner") else 0.05,
                "prob_acquisition": 0.10,
                "prob_failure": max(0.05, 0.5 - agents / 10000),
                "hackernews_posted": decisions.get("hackernews_post", False),
                "arxiv_submitted": decisions.get("arxiv_paper", False),
                "first_external_agent": agents > 0,
                "token_live": decisions.get("token_launch") == "mainnet",
                "physical_hub_installed": decisions.get("physical_hub", False),
                "agents_target_1y": agents,
                "deflationary_token": True,
                "tam_agents_billion": 10,
                "adoption_speed": 0.5 if decisions.get("hackernews_post") else 0.2,
            }
        )

        try:
            decision = self.engine.decide(thesis, verbose=False)
            return decision.final_score
        except Exception:
            return 0.5

    def generate_universes(self, max_universes: int = None) -> list[Universe]:
        """Gera todos os universos possíveis."""
        max_u = max_universes or self.MAX_UNIVERSES_TO_EVALUATE

        # Definir combinações de decisões
        lever_options = {
            "hackernews_post": [False, True],
            "arxiv_paper":     [False, True],
            "twitter_thread":  [False, True],
            "token_launch":    ["none", "devnet", "mainnet"],
            "physical_hub":    [False, True],
            "community":       ["none", "discord"],
            "funding":         ["bootstrap", "angel", "seed"],
            "world_model_partner": [False, True],
            "enterprise_client":   [False, True],
        }

        # Gerar combinações priorizadas (não força-bruta completa)
        # Total teórico: 2×2×2×3×2×2×3×2×2 = 1152 universos
        # Usamos amostragem inteligente

        universes = []

        # 1. Universo atual (sem nada novo)
        current = {k: v[0] for k, v in lever_options.items()}
        current["token_launch"] = "none"
        current["community"] = "none"
        current["funding"] = "bootstrap"
        universes.append(current.copy())

        # 2. Ações de custo zero combinadas (as mais viáveis agora)
        zero_cost_combos = list(itertools.product(
            [False, True],  # hn
            [False, True],  # arxiv
            [False, True],  # twitter
        ))
        for hn, ax, tw in zero_cost_combos:
            u = current.copy()
            u["hackernews_post"] = hn
            u["arxiv_paper"] = ax
            u["twitter_thread"] = tw
            universes.append(u)

        # 3. Combinações com token
        for hn in [True, False]:
            for token in ["none", "devnet", "mainnet"]:
                u = current.copy()
                u["hackernews_post"] = hn
                u["arxiv_paper"] = True
                u["token_launch"] = token
                universes.append(u)

        # 4. Combinações com funding
        for funding in ["bootstrap", "angel", "seed", "series_a"]:
            for hn in [True, False]:
                u = current.copy()
                u["hackernews_post"] = hn
                u["arxiv_paper"] = True
                u["funding"] = funding
                u["token_launch"] = "devnet" if funding != "bootstrap" else "none"
                universes.append(u)

        # 5. Com hub físico
        for funding in ["angel", "seed"]:
            for hn in [True, False]:
                u = current.copy()
                u["hackernews_post"] = hn
                u["arxiv_paper"] = True
                u["physical_hub"] = True
                u["funding"] = funding
                u["token_launch"] = "devnet"
                universes.append(u)

        # 6. Com parcerias estratégicas
        for wm in [True, False]:
            for ec in [True, False]:
                u = current.copy()
                u["hackernews_post"] = True
                u["arxiv_paper"] = True
                u["world_model_partner"] = wm
                u["enterprise_client"] = ec
                u["funding"] = "seed"
                u["token_launch"] = "devnet"
                universes.append(u)

        # 7. O universo máximo (tudo ativado)
        max_universe = {
            "hackernews_post": True,
            "arxiv_paper": True,
            "twitter_thread": True,
            "token_launch": "mainnet",
            "physical_hub": True,
            "community": "discord",
            "funding": "series_a",
            "world_model_partner": True,
            "enterprise_client": True,
        }
        universes.append(max_universe)

        # Deduplicar
        seen = set()
        unique_universes = []
        for u in universes:
            key = json.dumps(u, sort_keys=True)
            if key not in seen:
                seen.add(key)
                unique_universes.append(u)

        # Limitar e avaliar
        unique_universes = unique_universes[:max_u]
        evaluated = []
        total = len(unique_universes)

        print(f"\n🌌 Simulando {total} universos paralelos...")

        for i, decisions in enumerate(unique_universes):
            if (i + 1) % 20 == 0:
                print(f"   [{i+1}/{total}] universos avaliados...")

            agents = self._estimate_agents(decisions)
            valuation = self._estimate_valuation(agents, decisions)
            probability = self._calculate_probability(decisions)
            risk = self._calculate_risk(decisions)
            score = self._score_universe(decisions, agents)
            narrative = self._build_narrative(decisions, agents, valuation)

            # Labels legíveis
            labels = {}
            for lever, option in decisions.items():
                lever_data = GROWTH_LEVERS.get(lever, {})
                options_list = lever_data.get("options", [])
                labels_list = lever_data.get("labels", [])
                if option in options_list:
                    idx = options_list.index(option)
                    labels[lever] = labels_list[idx] if idx < len(labels_list) else str(option)
                else:
                    labels[lever] = str(option)

            universe = Universe(
                universe_id=f"U-{uuid.uuid4().hex[:6]}",
                timeline="12_months",
                decisions=decisions,
                decision_labels=labels,
                agents_12m=agents,
                valuation_usd=valuation,
                probability=probability,
                risk_score=risk,
                decision_score=score,
                narrative=narrative,
            )
            evaluated.append(universe)

        # Rank por EV = score × probability × valuation
        for u in evaluated:
            u.rank = 0  # será definido abaixo

        # Ordenar por EV ajustado por risco
        evaluated.sort(
            key=lambda u: u.decision_score * u.probability * (1 - u.risk_score * 0.3),
            reverse=True
        )
        for i, u in enumerate(evaluated):
            u.rank = i + 1

        self.universes = evaluated
        return evaluated

    def get_top_universes(self, n: int = 10) -> list[Universe]:
        if not self.universes:
            self.generate_universes()
        return self.universes[:n]

    def get_current_universe(self) -> Universe | None:
        """Retorna o universo mais próximo da situação atual."""
        for u in self.universes:
            if not any([
                u.decisions.get("hackernews_post"),
                u.decisions.get("arxiv_paper"),
                u.decisions.get("physical_hub"),
                u.decisions.get("token_launch") != "none",
                u.decisions.get("funding") != "bootstrap",
            ]):
                return u
        return None

    def get_best_next_action(self) -> dict:
        """
        Identifica a ÚNICA próxima ação que mais aumenta o score
        a partir do universo atual.
        """
        if not self.universes:
            self.generate_universes()

        current = self.get_current_universe()
        if not current:
            return {}

        # Comparar cada universo que difere do atual em apenas 1 decisão
        best_delta = None
        best_action = None

        for u in self.universes:
            diff_keys = [
                k for k in u.decisions
                if u.decisions[k] != current.decisions.get(k)
            ]
            if len(diff_keys) == 1:
                delta_score = u.decision_score - current.decision_score
                delta_agents = u.agents_12m - current.agents_12m
                delta_val = u.valuation_usd - current.valuation_usd
                if best_delta is None or delta_score > best_delta:
                    best_delta = delta_score
                    best_action = {
                        "action": diff_keys[0],
                        "from": current.decisions.get(diff_keys[0]),
                        "to": u.decisions[diff_keys[0]],
                        "label": u.decision_labels.get(diff_keys[0], ""),
                        "score_gain": round(delta_score, 4),
                        "agents_gain": delta_agents,
                        "valuation_gain_usd": round(delta_val),
                        "new_universe_rank": u.rank,
                        "probability": u.probability,
                    }

        return best_action or {}

    def print_report(self, top_n: int = 5):
        """Imprime relatório completo da simulação."""
        universes = self.get_top_universes(top_n)
        current = self.get_current_universe()
        best_next = self.get_best_next_action()

        print("\n" + "█"*62)
        print("  KEEPIT MULTIVERSE SIMULATOR")
        print(f"  {len(self.universes)} universos simulados | Top {top_n} caminhos")
        print("█"*62)

        if current:
            val_str = f"${current.valuation_usd/1e6:.0f}M"
            print(f"\n📍 UNIVERSO ATUAL (rank #{current.rank}):")
            print(f"   Agentes 12m: {current.agents_12m:,} | Valoração: {val_str}")
            print(f"   Score: {current.decision_score:.1%} | Prob: {current.probability:.0%}")

        if best_next:
            val_gain = best_next['valuation_gain_usd']
            val_str = f"+${val_gain/1e6:.0f}M" if val_gain >= 1e6 else f"+${val_gain:,.0f}"
            print(f"\n⚡ MELHOR PRÓXIMA AÇÃO (1 passo):")
            print(f"   → {best_next['label']}")
            print(f"   Score: +{best_next['score_gain']:.1%} | Agentes: +{best_next['agents_gain']:,} | Valoração: {val_str}")
            print(f"   Probabilidade de sucesso: {best_next['probability']:.0%}")

        print(f"\n🏆 TOP {top_n} UNIVERSOS VENCEDORES:")
        print("─"*62)

        for u in universes:
            val_str = f"${u.valuation_usd/1e9:.1f}B" if u.valuation_usd >= 1e9 else f"${u.valuation_usd/1e6:.0f}M"
            print(f"\n  #{u.rank} | Score: {u.decision_score:.0%} | Prob: {u.probability:.0%} | Risco: {u.risk_score:.0%}")
            print(f"  Agentes: {u.agents_12m:,} | Valoração: {val_str}")
            print(f"  Decisões ativas:")
            active = [v for k, v in u.decision_labels.items()
                     if u.decisions[k] not in [False, "none", "bootstrap"]]
            for a in active:
                print(f"    ✅ {a}")
            print(f"  Narrativa: {u.narrative[:120]}...")
            print("─"*62)

        print("\n█"*62)


def run_multiverse():
    sim = MultiverseSimulator()
    sim.generate_universes(max_universes=150)
    sim.print_report(top_n=7)
    return sim


if __name__ == "__main__":
    run_multiverse()
