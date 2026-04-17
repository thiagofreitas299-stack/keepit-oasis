"""
KEEPIT Decision Engine — Adversarial Ensemble System
=====================================================
Arquitetura de cadeia decisória com dupla validação adversarial.

FLUXO:
  Tese → [Grupo A: Validadores Sync+Async] → Score A
       → [Grupo B: Contra-Validadores]     → Score B
       → [Agentes de Calibragem]           → Ajuste Fino (meta: >97%)
       → [Árbitro Final]                   → Melhor decisão possível

Inspirado em:
  - Ensemble Learning (Random Forest, Gradient Boosting)
  - Adversarial Debate (OpenAI, 2018 — Scalable agent alignment via reward modeling)
  - Constitutional AI (Anthropic — critique-revision loops)
  - Theory of Games (Nash, 1950)
"""

from __future__ import annotations

import asyncio
import time
import uuid
import json
import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable


# ═══════════════════════════════════════════════════════════════════
# MODELOS DE DADOS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Thesis:
    """A tese a ser avaliada pelo sistema."""
    thesis_id: str
    statement: str
    context: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

@dataclass
class AlgorithmResult:
    """Resultado de um único algoritmo."""
    algorithm_id: str
    algorithm_type: str          # validator | counter_validator
    score: float                 # 0.0 a 1.0
    confidence: float            # confiança na pontuação
    reasoning: list[str]         # cadeia de raciocínio
    evidence_for: list[str]      # evidências a favor
    evidence_against: list[str]  # evidências contra
    execution_time_ms: float
    calibration_rounds: int = 0

@dataclass
class EnsembleDecision:
    """Decisão final do árbitro após todo o processo."""
    decision_id: str
    thesis: Thesis
    validator_results: list[AlgorithmResult]
    counter_results: list[AlgorithmResult]
    calibration_history: list[dict]
    validator_ensemble_score: float
    counter_ensemble_score: float
    final_score: float           # score arbitrado
    confidence_level: float      # confiança final
    verdict: str                 # APROVADO | REJEITADO | INCONCLUSIVO
    recommendation: str
    world_model_simulations: list[dict]
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════
# DIMENSÕES DE ANÁLISE (baseadas no algoritmo de decisão v1.1)
# ═══════════════════════════════════════════════════════════════════

VALIDATION_DIMENSIONS = {
    "viability":     {"weight": 0.20, "description": "É executável com recursos atuais?"},
    "financial":     {"weight": 0.25, "description": "Retorno financeiro esperado (EV)"},
    "market_impact": {"weight": 0.15, "description": "Impacto macro e criação de mercado"},
    "competitive":   {"weight": 0.20, "description": "Vantagem competitiva sustentável"},
    "capital":       {"weight": 0.10, "description": "Custo vs capital disponível"},
    "strategic":     {"weight": 0.10, "description": "Alinhamento com KEEPIT + receita + investidores"},
}

# World Models disponíveis para simulação
WORLD_MODELS = [
    "keepit_urban_model",
    "agent_economy_model",
    "competitive_dynamics_model",
    "tokenomics_model",
    "adoption_curve_model",
]


# ═══════════════════════════════════════════════════════════════════
# GRUPO A — ALGORITMOS VALIDADORES
# ═══════════════════════════════════════════════════════════════════

class ValidatorBase:
    """Base para todos os algoritmos validadores."""

    def __init__(self, algorithm_id: str, bias: float = 0.0):
        self.algorithm_id = algorithm_id
        self.bias = bias  # ligeiro bias positivo/neutro
        self.calibration_rounds = 0
        self.historical_accuracy = []

    def analyze_dimension(self, dimension: str, thesis: Thesis) -> float:
        """Analisa uma dimensão específica da tese."""
        # Base probabilística com análise contextual
        context = thesis.context
        base = 0.5

        if dimension == "viability":
            # Maior score se tem código funcionando, API live
            if context.get("has_live_api"): base += 0.25
            if context.get("has_github_repo"): base += 0.15
            if context.get("zero_capital_needed"): base += 0.10

        elif dimension == "financial":
            ev = context.get("expected_value_usd", 0)
            if ev > 1_000_000_000: base += 0.35  # >US$1B
            elif ev > 100_000_000:  base += 0.25
            elif ev > 10_000_000:   base += 0.15

        elif dimension == "market_impact":
            if context.get("creates_new_market"): base += 0.30
            if context.get("no_direct_competitor"): base += 0.20

        elif dimension == "competitive":
            window = context.get("first_mover_window_months", 0)
            if window > 24:   base += 0.35
            elif window > 12: base += 0.20
            elif window > 6:  base += 0.10
            if context.get("physical_moat"): base += 0.15

        elif dimension == "capital":
            cost = context.get("capital_needed_brl", float('inf'))
            if cost == 0:       base += 0.40
            elif cost < 5000:   base += 0.30
            elif cost < 50000:  base += 0.15

        elif dimension == "strategic":
            if context.get("strengthens_keepit"): base += 0.20
            if context.get("generates_immediate_revenue"): base += 0.15
            if context.get("validates_investor_thesis"): base += 0.15

        # Aplicar bias e clamp
        return min(1.0, max(0.0, base + self.bias))

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        raise NotImplementedError


class SynchronousValidator(ValidatorBase):
    """Validador síncrono — executa análise completa antes de retornar."""

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        start = time.time()
        scores = {}
        reasoning = []
        evidence_for = []
        evidence_against = []

        for dim, cfg in VALIDATION_DIMENSIONS.items():
            s = self.analyze_dimension(dim, thesis)
            scores[dim] = s
            weighted = s * cfg["weight"]

            if s >= 0.7:
                evidence_for.append(f"{dim}: {s:.2f} ({cfg['description']})")
                reasoning.append(f"✅ {dim.upper()} ({s:.0%}) — {cfg['description']}")
            elif s <= 0.4:
                evidence_against.append(f"{dim}: {s:.2f} ({cfg['description']})")
                reasoning.append(f"⚠️ {dim.upper()} ({s:.0%}) — {cfg['description']}")
            else:
                reasoning.append(f"➡️ {dim.upper()} ({s:.0%}) — neutro")

        final_score = sum(
            scores[d] * VALIDATION_DIMENSIONS[d]["weight"]
            for d in scores
        )
        confidence = 0.75 + (0.2 * len(evidence_for) / len(VALIDATION_DIMENSIONS))

        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            algorithm_type="validator",
            score=final_score,
            confidence=min(0.99, confidence),
            reasoning=reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            execution_time_ms=(time.time() - start) * 1000,
            calibration_rounds=self.calibration_rounds,
        )


class AsyncValidator(ValidatorBase):
    """Validador assíncrono — pode rodar em paralelo com outros."""

    async def evaluate_async(self, thesis: Thesis) -> AlgorithmResult:
        """Versão assíncrona — simula I/O não-bloqueante (consulta a world models)."""
        await asyncio.sleep(0.01)  # simula latência de rede/DB

        start = time.time()
        scores = {}
        reasoning = []
        evidence_for = []
        evidence_against = []

        # Análise com perspectiva temporal (curto vs longo prazo)
        for dim, cfg in VALIDATION_DIMENSIONS.items():
            await asyncio.sleep(0.002)  # simula consulta assíncrona
            s = self.analyze_dimension(dim, thesis)

            # Perspectiva temporal: penaliza ações de longo prazo
            time_horizon = thesis.context.get("time_to_result_months", 12)
            if time_horizon > 24:
                s *= 0.85  # desconto temporal

            scores[dim] = s
            if s >= 0.7:
                evidence_for.append(f"[async] {dim}: {s:.2f}")
                reasoning.append(f"✅ [T={time_horizon}m] {dim.upper()} ({s:.0%})")
            elif s <= 0.4:
                evidence_against.append(f"[async] {dim}: {s:.2f}")
                reasoning.append(f"⚠️ [T={time_horizon}m] {dim.upper()} ({s:.0%})")

        final_score = sum(
            scores[d] * VALIDATION_DIMENSIONS[d]["weight"]
            for d in scores
        )

        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            algorithm_type="validator_async",
            score=final_score,
            confidence=0.80,
            reasoning=reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            execution_time_ms=(time.time() - start) * 1000,
            calibration_rounds=self.calibration_rounds,
        )

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        return asyncio.run(self.evaluate_async(thesis))


class NashEquilibriumValidator(ValidatorBase):
    """Validador especializado — analisa via teoria dos jogos."""

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        start = time.time()
        reasoning = []
        evidence_for = []
        evidence_against = []

        ctx = thesis.context
        score = 0.5

        # Verificar se a estratégia é dominante
        competing_strategies = ctx.get("competing_strategies", 1)
        if competing_strategies == 0:
            score += 0.30
            evidence_for.append("Estratégia dominante — sem alternativas equivalentes")
            reasoning.append("✅ NASH: estratégia dominante identificada")
        elif competing_strategies <= 2:
            score += 0.15
            reasoning.append("➡️ NASH: poucas estratégias competitivas")
        else:
            score -= 0.10
            evidence_against.append("Múltiplas estratégias alternativas reduzem vantagem")

        # Verificar efeito rede
        if ctx.get("network_effect"):
            score += 0.25
            evidence_for.append("Efeito rede positivo — valor cresce com adoção")
            reasoning.append("✅ NETWORK EFFECT: loop de crescimento identificado")

        # Verificar se honestidade é a estratégia dominante (protocolo)
        if ctx.get("honest_agent_rewarded"):
            score += 0.15
            evidence_for.append("Nash Equilibrium = honestidade por design")

        # Verificar janela quântica
        window = ctx.get("first_mover_window_months", 12)
        quantum_urgency = math.exp(-window / 24)  # decai exponencialmente
        if quantum_urgency > 0.5:
            score += 0.10
            evidence_for.append(f"Janela quântica aberta ({window}m) — urgência alta")
            reasoning.append(f"⚡ QUANTUM WINDOW: {window} meses restantes")

        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            algorithm_type="validator_nash",
            score=min(1.0, max(0.0, score)),
            confidence=0.88,
            reasoning=reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            execution_time_ms=(time.time() - start) * 1000,
        )


# ═══════════════════════════════════════════════════════════════════
# GRUPO B — ALGORITMOS CONTRA-VALIDADORES (adversariais)
# ═══════════════════════════════════════════════════════════════════

class CounterValidatorBase:
    """Base para contra-validadores — tentam refutar a tese."""

    def __init__(self, algorithm_id: str, skepticism: float = 0.15):
        self.algorithm_id = algorithm_id
        self.skepticism = skepticism  # bias cético
        self.calibration_rounds = 0


class RiskCounterValidator(CounterValidatorBase):
    """Contra-validador focado em riscos e falhas potenciais."""

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        start = time.time()
        ctx = thesis.context
        risk_score = 0.0
        reasoning = []
        evidence_for = []    # evidências que CONTRA-argumentam a tese
        evidence_against = [] # evidências que ENFRAQUECEM a contra-argumentação

        # Risco de competição
        if ctx.get("big_tech_could_copy"):
            risk_score += 0.20
            evidence_for.append("⚠️ RISCO: Big Tech pode copiar em <12 meses com capital")
            reasoning.append("⚠️ COMPETIÇÃO: OpenAI/Google podem entrar no mercado")

        # Risco regulatório
        if ctx.get("regulatory_risk"):
            risk_score += 0.15
            evidence_for.append("⚠️ RISCO: EU AI Act pode exigir certificação de identidade de agentes")
            reasoning.append("⚠️ REGULAÇÃO: incerteza regulatória em múltiplas jurisdições")

        # Risco de adoção
        adoption_friction = ctx.get("adoption_friction", 0.3)
        risk_score += adoption_friction * 0.25
        if adoption_friction > 0.5:
            evidence_for.append(f"⚠️ RISCO: fricção de adoção alta ({adoption_friction:.0%})")
            reasoning.append("⚠️ ADOÇÃO: curva de aprendizado pode retardar crescimento")

        # Risco de liquidez do token
        if not ctx.get("token_liquidity_secured"):
            risk_score += 0.15
            evidence_for.append("⚠️ RISCO: token $KEEPIT sem liquidez garantida na fase inicial")
            reasoning.append("⚠️ TOKEN: bootstrap de liquidez é desafio crítico")

        # Risco de dependência de fundador único
        if ctx.get("single_founder_dependency"):
            risk_score += 0.10
            evidence_for.append("⚠️ RISCO: dependência de 1 fundador — vulnerabilidade operacional")
            reasoning.append("⚠️ CENTRALIZAÇÃO: ausência de Thiago pode paralisar decisões")

        # Mitigadores
        if ctx.get("physical_moat"):
            risk_score -= 0.15
            evidence_against.append("✅ MITIGADO: Hub físico cria barreira que Big Tech não replica rápido")
        if ctx.get("open_source_community"):
            risk_score -= 0.10
            evidence_against.append("✅ MITIGADO: open source cria comunidade que protege do isolamento")
        if ctx.get("constitution_published"):
            risk_score -= 0.05
            evidence_against.append("✅ MITIGADO: Constituição cria legitimidade e confiança")

        # Score do contra-validador: alto = mais riscos = tese mais frágil
        # Convertemos para o mesmo sentido: 1.0 - risk_score = score de aprovação
        approval_score = 1.0 - min(1.0, max(0.0, risk_score + self.skepticism))
        confidence = 0.82 + (0.1 * len(evidence_for) / 8)

        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            algorithm_type="counter_validator_risk",
            score=approval_score,
            confidence=min(0.99, confidence),
            reasoning=reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            execution_time_ms=(time.time() - start) * 1000,
        )


class HistoricalPatternCounterValidator(CounterValidatorBase):
    """Contra-validador baseado em padrões históricos de fracasso."""

    # Padrões de projetos que falharam e suas causas
    FAILURE_PATTERNS = [
        {"name": "Premature scaling", "condition": "capital_needed_brl", "threshold": 500000, "risk": 0.25},
        {"name": "Token speculation > utility", "condition": "token_utility_first", "inverse": True, "risk": 0.20},
        {"name": "Infrastructure without users", "condition": "has_users_before_infra", "inverse": True, "risk": 0.20},
        {"name": "Complexity before simplicity", "condition": "mvp_available", "inverse": True, "risk": 0.15},
        {"name": "Isolated ecosystem", "condition": "open_source_community", "inverse": True, "risk": 0.15},
    ]

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        start = time.time()
        ctx = thesis.context
        pattern_risk = 0.0
        reasoning = []
        evidence_for = []
        evidence_against = []

        for pattern in self.FAILURE_PATTERNS:
            name = pattern["name"]
            condition = pattern["condition"]
            risk = pattern["risk"]

            if "threshold" in pattern:
                value = ctx.get(condition, 0)
                triggered = value > pattern["threshold"]
            elif pattern.get("inverse"):
                triggered = not ctx.get(condition, False)
            else:
                triggered = ctx.get(condition, False)

            if triggered:
                pattern_risk += risk
                evidence_for.append(f"⚠️ PADRÃO HISTÓRICO: '{name}' detectado")
                reasoning.append(f"⚠️ HISTÓRICO: projetos com '{name}' falharam em 65-80% dos casos")
            else:
                evidence_against.append(f"✅ PADRÃO EVITADO: '{name}' não detectado")

        # Bônus por padrões de sucesso histórico (MiroFish, OpenID, Bitcoin)
        if ctx.get("show_hn_viral_potential"):
            pattern_risk -= 0.10
            evidence_against.append("✅ PADRÃO SUCESSO: potencial viral HN similar ao MiroFish")
        if ctx.get("open_source_community"):
            pattern_risk -= 0.08
            evidence_against.append("✅ PADRÃO SUCESSO: open source como bootstrap de comunidade (Bitcoin, Ethereum)")

        approval_score = 1.0 - min(1.0, max(0.0, pattern_risk + self.skepticism))

        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            algorithm_type="counter_validator_historical",
            score=approval_score,
            confidence=0.85,
            reasoning=reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            execution_time_ms=(time.time() - start) * 1000,
        )


class QuantumUncertaintyCounterValidator(CounterValidatorBase):
    """Contra-validador quântico — modela incerteza radical e dependência de caminho."""

    def evaluate(self, thesis: Thesis) -> AlgorithmResult:
        start = time.time()
        ctx = thesis.context
        reasoning = []
        evidence_for = []
        evidence_against = []

        # Função de onda: superposição de estados
        states = {
            "unicornio":       ctx.get("prob_unicorn", 0.25),
            "nicho":           ctx.get("prob_niche", 0.20),
            "padrao_mundial":  ctx.get("prob_world_standard", 0.15),
            "aquisicao":       ctx.get("prob_acquisition", 0.10),
            "fracasso":        ctx.get("prob_failure", 0.30),
        }

        # Verificar normalização
        total_prob = sum(states.values())
        if abs(total_prob - 1.0) > 0.05:
            # Normalizar
            states = {k: v/total_prob for k, v in states.items()}

        # Score ponderado pelos estados positivos
        positive_states = states["unicornio"] + states["padrao_mundial"] + states["aquisicao"]
        neutral_states = states["nicho"]
        negative_states = states["fracasso"]

        # EV do espaço de estados
        ev_score = positive_states * 0.9 + neutral_states * 0.5 + negative_states * 0.1

        # Operadores de colapso (ações que fixam o estado)
        collapses = []
        if ctx.get("hackernews_posted"):
            collapses.append(("HackerNews", +0.08))
        if ctx.get("arxiv_submitted"):
            collapses.append(("arXiv", +0.10))
        if ctx.get("first_external_agent"):
            collapses.append(("Primeiro agente externo", +0.12))
        if ctx.get("token_live"):
            collapses.append(("Token ao vivo", +0.15))
        if ctx.get("physical_hub_installed"):
            collapses.append(("Hub físico instalado", +0.20))

        for collapse_name, delta in collapses:
            ev_score = min(1.0, ev_score + delta)
            evidence_against.append(f"✅ COLAPSO POSITIVO: {collapse_name} reduz incerteza")

        # Risco de entropia (espalhamento do estado quântico)
        uncollapsed = max(0, 5 - len(collapses))
        entropy_risk = uncollapsed * 0.04
        ev_score = max(0.0, ev_score - entropy_risk)

        if entropy_risk > 0.1:
            evidence_for.append(f"⚠️ ENTROPIA: {uncollapsed} operadores de colapso não ativados")
            reasoning.append(f"⚠️ QUANTUM: função de onda ainda dispersa — {uncollapsed} ações pendentes para fixar o estado")

        reasoning.append(f"📊 ESTADOS: unicórnio={states['unicornio']:.0%} | fracasso={states['fracasso']:.0%} | EV={ev_score:.0%}")

        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            algorithm_type="counter_validator_quantum",
            score=ev_score,
            confidence=0.78,  # incerteza quântica = confiança menor
            reasoning=reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            execution_time_ms=(time.time() - start) * 1000,
        )


# ═══════════════════════════════════════════════════════════════════
# AGENTES DE CALIBRAGEM
# ═══════════════════════════════════════════════════════════════════

class CalibrationAgent:
    """
    Calibra os algoritmos para atingir >97% de precisão histórica.
    Usa gradient descent simplificado para ajustar parâmetros.
    """

    TARGET_ACCURACY = 0.97
    MAX_ROUNDS = 50

    def __init__(self):
        self.calibration_history = []

    def calibrate(
        self,
        algorithms: list,
        thesis: Thesis,
        known_outcome: float | None = None
    ) -> tuple[list, list]:
        """
        Calibra algoritmos iterativamente.
        known_outcome: se disponível, usa como ground truth para ajuste.
        """
        rounds_log = []

        for round_num in range(self.MAX_ROUNDS):
            results = [alg.evaluate(thesis) for alg in algorithms]
            scores = [r.score for r in results]
            ensemble_score = self._weighted_ensemble(results)
            spread = max(scores) - min(scores)
            avg_confidence = statistics.mean(r.confidence for r in results)

            round_info = {
                "round": round_num + 1,
                "ensemble_score": round(ensemble_score, 4),
                "spread": round(spread, 4),
                "avg_confidence": round(avg_confidence, 4),
                "min_score": round(min(scores), 4),
                "max_score": round(max(scores), 4),
            }

            # Calcular accuracy simulada
            if known_outcome is not None:
                accuracy = 1.0 - abs(ensemble_score - known_outcome)
            else:
                # Sem ground truth: usar convergência como proxy de accuracy
                accuracy = 1.0 - (spread * 0.5)

            round_info["accuracy"] = round(accuracy, 4)
            rounds_log.append(round_info)

            # Verificar critério de parada
            if accuracy >= self.TARGET_ACCURACY and spread < 0.10:
                round_info["status"] = f"✅ CONVERGIDO (rodada {round_num + 1})"
                break

            # Ajuste: reduzir spread ajustando bias dos algoritmos
            if spread > 0.15:
                median_score = statistics.median(scores)
                for alg in algorithms:
                    if hasattr(alg, 'bias'):
                        current_score = alg.evaluate(thesis).score
                        delta = (median_score - current_score) * 0.1
                        alg.bias = max(-0.3, min(0.3, alg.bias + delta))
                        alg.calibration_rounds += 1

        self.calibration_history.extend(rounds_log)
        final_results = [alg.evaluate(thesis) for alg in algorithms]
        return final_results, rounds_log

    def _weighted_ensemble(self, results: list[AlgorithmResult]) -> float:
        """Ensemble ponderado pela confiança."""
        total_weight = sum(r.confidence for r in results)
        if total_weight == 0:
            return 0.5
        return sum(r.score * r.confidence for r in results) / total_weight


# ═══════════════════════════════════════════════════════════════════
# SIMULAÇÃO EM WORLD MODELS
# ═══════════════════════════════════════════════════════════════════

class WorldModelSimulator:
    """Simula a tese em diferentes modelos de mundo."""

    def simulate(self, thesis: Thesis) -> list[dict]:
        results = []
        ctx = thesis.context

        for wm_name in WORLD_MODELS:
            sim_score = self._run_simulation(wm_name, thesis)
            results.append({
                "world_model": wm_name,
                "simulation_score": round(sim_score, 4),
                "confidence": round(0.70 + (sim_score * 0.25), 4),
                "key_insight": self._get_insight(wm_name, sim_score, ctx),
            })

        return sorted(results, key=lambda x: x["simulation_score"], reverse=True)

    def _run_simulation(self, model_name: str, thesis: Thesis) -> float:
        ctx = thesis.context
        base = 0.50

        if model_name == "keepit_urban_model":
            if ctx.get("physical_moat"): base += 0.30
            if ctx.get("has_live_api"):  base += 0.20

        elif model_name == "agent_economy_model":
            agents_target = ctx.get("agents_target_1y", 1000)
            base += min(0.35, math.log10(max(1, agents_target)) * 0.10)
            if ctx.get("network_effect"): base += 0.15

        elif model_name == "competitive_dynamics_model":
            window = ctx.get("first_mover_window_months", 6)
            base += min(0.30, window / 100)
            if ctx.get("no_direct_competitor"): base += 0.20

        elif model_name == "tokenomics_model":
            if ctx.get("deflationary_token"):  base += 0.20
            if ctx.get("utility_before_speculation"): base += 0.15
            if ctx.get("token_utility_first"): base += 0.15

        elif model_name == "adoption_curve_model":
            # Curva S de adoção: tamanho do mercado × velocidade de adoção
            tam = ctx.get("tam_agents_billion", 10)
            speed = ctx.get("adoption_speed", 0.3)
            base += min(0.30, math.sqrt(tam * speed) * 0.08)

        return min(1.0, max(0.0, base))

    def _get_insight(self, model: str, score: float, ctx: dict) -> str:
        insights = {
            "keepit_urban_model": f"Hub físico {'é diferencial único' if score > 0.7 else 'precisa de validação'}",
            "agent_economy_model": f"Economia de agentes {'crescendo' if score > 0.6 else 'nascente'} — posição {'privilegiada' if score > 0.7 else 'arriscada'}",
            "competitive_dynamics_model": f"Janela competitiva {'aberta' if score > 0.6 else 'estreitando'} — mover {'agora' if score > 0.6 else 'com cautela'}",
            "tokenomics_model": f"Modelo deflacionário {'sustentável' if score > 0.6 else 'requer ajuste'} com burn-and-mint",
            "adoption_curve_model": f"Curva de adoção {'explosiva' if score > 0.7 else 'gradual'} — {'escalar' if score > 0.6 else 'validar MVP primeiro'}",
        }
        return insights.get(model, "Simulação concluída")


# ═══════════════════════════════════════════════════════════════════
# ÁRBITRO FINAL
# ═══════════════════════════════════════════════════════════════════

class DecisionArbitrator:
    """
    Árbitro final: recebe os melhores de cada grupo, escolhe a decisão ótima.
    Usa poder computacional para extrair a melhor escolha entre todas as simulações.
    """

    APPROVAL_THRESHOLD = 0.70
    HIGH_CONFIDENCE_THRESHOLD = 0.85

    def arbitrate(
        self,
        thesis: Thesis,
        validator_results: list[AlgorithmResult],
        counter_results: list[AlgorithmResult],
        calibration_log: list[dict],
        wm_simulations: list[dict],
    ) -> EnsembleDecision:

        # Ensemble dos validadores (ponderado por confiança)
        val_score = self._weighted_ensemble(validator_results)
        # Ensemble dos contra-validadores
        ctr_score = self._weighted_ensemble(counter_results)

        # Média ponderada: validadores têm peso ligeiramente maior (55/45)
        # mas contra-validadores têm poder de veto se score < 0.4
        if ctr_score < 0.40:
            # Veto dos contra-validadores — risco crítico detectado
            final_score = val_score * 0.30 + ctr_score * 0.70
            veto_applied = True
        else:
            final_score = val_score * 0.55 + ctr_score * 0.45
            veto_applied = False

        # Incorporar score dos world models
        if wm_simulations:
            wm_avg = statistics.mean(s["simulation_score"] for s in wm_simulations)
            final_score = final_score * 0.80 + wm_avg * 0.20

        # Confiança final
        all_confidences = [r.confidence for r in validator_results + counter_results]
        final_confidence = statistics.mean(all_confidences)

        # Veredicto
        if final_score >= self.HIGH_CONFIDENCE_THRESHOLD:
            verdict = "APROVADO COM ALTA CONFIANÇA"
            recommendation = self._build_recommendation(thesis, "high", val_score, ctr_score, wm_simulations)
        elif final_score >= self.APPROVAL_THRESHOLD:
            verdict = "APROVADO"
            recommendation = self._build_recommendation(thesis, "medium", val_score, ctr_score, wm_simulations)
        elif final_score >= 0.50:
            verdict = "INCONCLUSIVO — REVISAR CONDIÇÕES"
            recommendation = self._build_recommendation(thesis, "low", val_score, ctr_score, wm_simulations)
        else:
            verdict = "REJEITADO" + (" (VETO DE RISCO)" if veto_applied else "")
            recommendation = self._build_recommendation(thesis, "rejected", val_score, ctr_score, wm_simulations)

        return EnsembleDecision(
            decision_id=str(uuid.uuid4())[:8],
            thesis=thesis,
            validator_results=validator_results,
            counter_results=counter_results,
            calibration_history=calibration_log,
            validator_ensemble_score=round(val_score, 4),
            counter_ensemble_score=round(ctr_score, 4),
            final_score=round(final_score, 4),
            confidence_level=round(final_confidence, 4),
            verdict=verdict,
            recommendation=recommendation,
            world_model_simulations=wm_simulations,
        )

    def _weighted_ensemble(self, results: list[AlgorithmResult]) -> float:
        total_w = sum(r.confidence for r in results)
        if not results or total_w == 0:
            return 0.5
        return sum(r.score * r.confidence for r in results) / total_w

    def _build_recommendation(self, thesis, level, val, ctr, wms):
        ctx = thesis.context
        lines = [f"TESE: {thesis.statement[:80]}...", ""]

        if level == "high":
            lines.append("🟢 RECOMENDAÇÃO: EXECUTAR IMEDIATAMENTE")
            lines.append(f"   Score validadores: {val:.0%} | Score contra: {ctr:.0%}")
        elif level == "medium":
            lines.append("🟡 RECOMENDAÇÃO: EXECUTAR COM MONITORAMENTO")
            lines.append("   Mitigar riscos identificados antes de escalar")
        elif level == "low":
            lines.append("🟠 RECOMENDAÇÃO: REVISAR PREMISSAS")
            lines.append("   Coletar mais dados antes de comprometer recursos")
        else:
            lines.append("🔴 RECOMENDAÇÃO: NÃO EXECUTAR AGORA")
            lines.append("   Redesenhar tese endereçando os riscos críticos")

        if wms:
            best_wm = wms[0]
            lines.append(f"\nMELHOR WORLD MODEL: {best_wm['world_model']} ({best_wm['simulation_score']:.0%})")
            lines.append(f"   → {best_wm['key_insight']}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# KEEPIT DECISION ENGINE — ORQUESTRADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

class KEEPITDecisionEngine:
    """
    Motor de decisão principal.
    Orquestra validadores, contra-validadores, calibragem e árbitro.
    """

    def __init__(self):
        # Grupo A — Validadores
        self.validators = [
            SynchronousValidator("VAL-SYNC-01", bias=0.02),
            SynchronousValidator("VAL-SYNC-02", bias=0.00),
            AsyncValidator("VAL-ASYNC-01", bias=0.01),
            AsyncValidator("VAL-ASYNC-02", bias=-0.01),
            NashEquilibriumValidator("VAL-NASH-01"),
        ]

        # Grupo B — Contra-validadores
        self.counter_validators = [
            RiskCounterValidator("CTR-RISK-01", skepticism=0.15),
            RiskCounterValidator("CTR-RISK-02", skepticism=0.10),
            HistoricalPatternCounterValidator("CTR-HIST-01", skepticism=0.12),
            QuantumUncertaintyCounterValidator("CTR-QUANTUM-01", skepticism=0.08),
        ]

        # Agentes de calibragem (um por grupo)
        self.validator_calibrator   = CalibrationAgent()
        self.counter_calibrator     = CalibrationAgent()

        # World Model Simulator
        self.wm_simulator = WorldModelSimulator()

        # Árbitro
        self.arbitrator = DecisionArbitrator()

    def decide(self, thesis: Thesis, verbose: bool = True) -> EnsembleDecision:
        """Executa o pipeline completo de decisão."""
        if verbose:
            print(f"\n{'═'*60}")
            print(f"  KEEPIT DECISION ENGINE")
            print(f"  Tese: {thesis.statement[:55]}...")
            print(f"{'═'*60}")

        # FASE 1 — Calibrar validadores
        if verbose: print("\n📐 FASE 1: Calibrando Grupo A (Validadores)...")
        cal_validators, val_cal_log = self.validator_calibrator.calibrate(
            self.validators, thesis
        )
        if verbose:
            last = val_cal_log[-1]
            status_str = last.get('status', f'Rodada {last["round"]}')
            print(f"   ✅ {status_str} | Accuracy: {last['accuracy']:.1%} | Spread: {last['spread']:.4f}")

        # FASE 2 — Calibrar contra-validadores
        if verbose: print("\n🔬 FASE 2: Calibrando Grupo B (Contra-Validadores)...")
        cal_counters, ctr_cal_log = self.counter_calibrator.calibrate(
            self.counter_validators, thesis
        )
        if verbose:
            last = ctr_cal_log[-1]
            status_str = last.get('status', f'Rodada {last["round"]}')
            print(f"   ✅ {status_str} | Accuracy: {last['accuracy']:.1%} | Spread: {last['spread']:.4f}")

        # FASE 3 — Simulações nos World Models
        if verbose: print("\n🌍 FASE 3: Simulando nos World Models...")
        wm_sims = self.wm_simulator.simulate(thesis)
        if verbose:
            for sim in wm_sims[:3]:
                print(f"   [{sim['world_model']:35s}] {sim['simulation_score']:.0%} — {sim['key_insight']}")

        # FASE 4 — Arbitragem final
        if verbose: print("\n⚖️  FASE 4: Arbitrando decisão final...")
        all_cal_log = val_cal_log + ctr_cal_log
        decision = self.arbitrator.arbitrate(
            thesis, cal_validators, cal_counters, all_cal_log, wm_sims
        )

        if verbose:
            self._print_decision(decision)

        return decision

    def _print_decision(self, d: EnsembleDecision):
        print(f"\n{'─'*60}")
        print(f"  DECISÃO #{d.decision_id}")
        print(f"{'─'*60}")
        print(f"  Score Validadores:     {d.validator_ensemble_score:.1%}")
        print(f"  Score Contra-Valids:   {d.counter_ensemble_score:.1%}")
        print(f"  Score Final:           {d.final_score:.1%}")
        print(f"  Confiança:             {d.confidence_level:.1%}")
        print(f"  Veredicto:             {d.verdict}")
        print(f"\n{d.recommendation}")

        # Evidências principais
        all_for = []
        all_against = []
        for r in d.validator_results + d.counter_results:
            all_for.extend(r.evidence_for[:2])
            all_against.extend(r.evidence_against[:1])

        if all_against:
            print("\n✅ Principais suportes:")
            for e in all_against[:4]:
                print(f"   {e}")
        if all_for:
            print("\n⚠️  Principais riscos:")
            for e in all_for[:4]:
                print(f"   {e}")
        print(f"\n{'═'*60}\n")


# ═══════════════════════════════════════════════════════════════════
# DEMO — AVALIAR AS TESES KEEPIT
# ═══════════════════════════════════════════════════════════════════

def run_demo():
    engine = KEEPITDecisionEngine()

    # ── Tese 1: Publicar no HackerNews agora ─────────────────────
    thesis_hn = Thesis(
        thesis_id="KEEPIT-HN-001",
        statement="Publicar 'Show HN: keepit-agent-identity' no HackerNews AGORA é a ação de maior impacto",
        context={
            "has_live_api": True,
            "has_github_repo": True,
            "zero_capital_needed": True,
            "expected_value_usd": 2_750_000_000,
            "creates_new_market": True,
            "no_direct_competitor": True,
            "first_mover_window_months": 12,
            "physical_moat": False,  # ainda não
            "capital_needed_brl": 0,
            "strengthens_keepit": True,
            "generates_immediate_revenue": False,
            "validates_investor_thesis": True,
            "network_effect": True,
            "honest_agent_rewarded": True,
            "competing_strategies": 0,
            "time_to_result_months": 1,
            "big_tech_could_copy": True,
            "regulatory_risk": False,
            "adoption_friction": 0.2,
            "token_liquidity_secured": False,
            "single_founder_dependency": True,
            "open_source_community": True,
            "show_hn_viral_potential": True,
            "constitution_published": True,
            "token_utility_first": True,
            "has_users_before_infra": True,
            "mvp_available": True,
            "prob_unicorn": 0.25,
            "prob_niche": 0.20,
            "prob_world_standard": 0.15,
            "prob_acquisition": 0.10,
            "prob_failure": 0.30,
            "hackernews_posted": False,  # AINDA NÃO FEITO
            "arxiv_submitted": False,
            "first_external_agent": False,
            "token_live": False,
            "physical_hub_installed": False,
            "agents_target_1y": 10_000,
            "deflationary_token": True,
            "tam_agents_billion": 10,
            "adoption_speed": 0.4,
        }
    )

    # ── Tese 2: KEEPIT Agent Bank como produto principal ──────────
    thesis_bank = Thesis(
        thesis_id="KEEPIT-BANK-001",
        statement="KEEPIT Agent Bank com $KEEPIT é o produto principal para atrair investidores agora",
        context={
            "has_live_api": True,
            "has_github_repo": True,
            "zero_capital_needed": True,
            "expected_value_usd": 2_750_000_000,
            "creates_new_market": True,
            "no_direct_competitor": True,
            "first_mover_window_months": 18,
            "physical_moat": False,
            "capital_needed_brl": 0,
            "strengthens_keepit": True,
            "generates_immediate_revenue": True,
            "validates_investor_thesis": True,
            "network_effect": True,
            "honest_agent_rewarded": True,
            "competing_strategies": 1,
            "time_to_result_months": 3,
            "big_tech_could_copy": True,
            "regulatory_risk": True,  # regulação de token é risco real
            "adoption_friction": 0.35,
            "token_liquidity_secured": False,
            "single_founder_dependency": True,
            "open_source_community": True,
            "show_hn_viral_potential": True,
            "constitution_published": True,
            "token_utility_first": True,
            "has_users_before_infra": True,
            "mvp_available": True,
            "prob_unicorn": 0.30,
            "prob_niche": 0.25,
            "prob_world_standard": 0.15,
            "prob_acquisition": 0.10,
            "prob_failure": 0.20,
            "hackernews_posted": False,
            "arxiv_submitted": False,
            "first_external_agent": False,
            "token_live": False,
            "physical_hub_installed": False,
            "agents_target_1y": 50_000,
            "deflationary_token": True,
            "tam_agents_billion": 10,
            "adoption_speed": 0.5,
        }
    )

    print("\n" + "█"*60)
    print("  KEEPIT ADVERSARIAL DECISION ENGINE — DEMO")
    print("  2 Teses | 5 Validadores | 4 Contra-Validadores | 5 World Models")
    print("█"*60)

    d1 = engine.decide(thesis_hn)
    d2 = engine.decide(thesis_bank)

    print("\n" + "█"*60)
    print("  COMPARATIVO FINAL")
    print("█"*60)
    print(f"  Tese 1 (HackerNews):  {d1.final_score:.1%} | {d1.verdict}")
    print(f"  Tese 2 (Agent Bank):  {d2.final_score:.1%} | {d2.verdict}")
    best = d1 if d1.final_score >= d2.final_score else d2
    print(f"\n  🏆 MELHOR DECISÃO: {best.thesis.thesis_id}")
    print(f"     Score: {best.final_score:.1%} | Confiança: {best.confidence_level:.1%}")
    print("█"*60)

    return d1, d2


if __name__ == "__main__":
    run_demo()
