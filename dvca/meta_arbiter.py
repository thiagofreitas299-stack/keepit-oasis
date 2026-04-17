"""
═══════════════════════════════════════════════════════════════════════════
DVCA — Dual Validation / Counter-Validation Arbiter System
MODULE 4: WORLD MODEL SIMULATOR + META-ARBITER
═══════════════════════════════════════════════════════════════════════════
Ciências Base:
  - World Models          (Ha & Schmidhuber 2018; DreamerV3 2023)
  - Monte Carlo Tree Search (Coulom 2006; AlphaGo Silver 2016)
  - Prospect Theory       (Kahneman & Tversky 1979; Nobel 1992)
  - Decision Theory       (Savage 1954; Jeffrey 1965)
  - AI Safety via Debate  (Irving et al. 2018)
  - Constitutional AI     (Anthropic 2022)
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import time
import json
import sys, os
sys.path.insert(0, os.path.dirname(__file__))


@dataclass
class WorldModelState:
    scenario_id: str
    trajectory_scores: List[float]
    mean_outcome: float
    std_outcome: float
    percentile_5: float
    percentile_95: float
    tail_risk: float
    n_simulations: int


@dataclass
class FinalDecision:
    decision: str
    confidence: float
    v_score: float
    cv_score: float
    world_score: float
    composite_score: float
    winner: str
    winner_score: float
    risk_adjusted_score: float
    mcts_explored_nodes: int
    reasoning: List[str]
    timestamp: float = field(default_factory=time.time)


class WorldModelSimulator:
    def __init__(self, n_scenarios: int = 10, n_steps: int = 50, seed: Optional[int] = None):
        self.n_scenarios = n_scenarios
        self.n_steps = n_steps
        self.rng = np.random.RandomState(seed or 42)

    def _environment_model(self, state: float, action: float) -> float:
        drift    = 0.02 * (0.9 - state)
        momentum = 0.15 * action
        noise    = self.rng.normal(0, 0.03)
        return float(np.clip(state + drift + momentum + noise, 0, 1))

    def _reward_model(self, state: float, step: int) -> float:
        return state * (0.99 ** step)

    def _value_model(self, trajectory: List[float]) -> float:
        return sum(s * (0.99**i) for i, s in enumerate(trajectory))

    def simulate(self, initial_score: float, decision_quality: float) -> WorldModelState:
        scenario_values = []
        max_value = sum(0.99**i for i in range(self.n_steps + 1))
        for _ in range(self.n_scenarios):
            state = initial_score
            trajectory = [state]
            for step in range(self.n_steps):
                action = decision_quality + self.rng.normal(0, 0.05)
                state = self._environment_model(state, action)
                trajectory.append(state)
            normalized = float(np.clip(self._value_model(trajectory) / max_value, 0, 1))
            scenario_values.append(normalized)
        arr = np.array(scenario_values)
        return WorldModelState(
            scenario_id=f'WM_{int(time.time())}',
            trajectory_scores=scenario_values,
            mean_outcome=float(np.mean(arr)),
            std_outcome=float(np.std(arr)),
            percentile_5=float(np.percentile(arr, 5)),
            percentile_95=float(np.percentile(arr, 95)),
            tail_risk=float(np.mean(arr < 0.65)),
            n_simulations=self.n_scenarios,
        )


class MCTSNode:
    def __init__(self, action: str, parent=None, prior: float = 0.5):
        self.action = action
        self.parent = parent
        self.children: Dict[str, 'MCTSNode'] = {}
        self.visits = 0
        self.value_sum = 0.0
        self.prior = prior

    @property
    def value(self) -> float:
        return self.value_sum / max(self.visits, 1)

    def ucb_score(self, c: float = 1.414) -> float:
        if self.visits == 0: return float('inf')
        parent_visits = self.parent.visits if self.parent else 1
        return self.value + c * self.prior * np.sqrt(np.log(parent_visits) / self.visits)


class MCTSDecisionExplorer:
    ACTIONS = ['APPROVE', 'REJECT', 'ESCALATE', 'REVISE']
    ACTION_PRIORS = [0.5, 0.2, 0.2, 0.1]

    def __init__(self, n_simulations: int = 100):
        self.n_sim = n_simulations
        self.rng = np.random.RandomState(7)

    def _simulate(self, node: MCTSNode, composite: float, world_state: WorldModelState) -> float:
        base = {'APPROVE': composite, 'REJECT': 1-composite, 'ESCALATE': composite*0.7+0.3, 'REVISE': composite*0.8+0.15}.get(node.action, 0.5)
        return float(np.clip(base - world_state.tail_risk * 0.3 + self.rng.normal(0, 0.05), 0, 1))

    def _backpropagate(self, node: MCTSNode, reward: float):
        while node is not None:
            node.visits += 1
            node.value_sum += reward
            node = node.parent

    def search(self, composite: float, world_state: WorldModelState) -> Tuple[str, float, int]:
        root = MCTSNode(action='ROOT', prior=1.0)
        for action, prior in zip(self.ACTIONS, self.ACTION_PRIORS):
            root.children[action] = MCTSNode(action=action, parent=root, prior=prior)
        for _ in range(self.n_sim):
            child = max(root.children.values(), key=lambda n: n.ucb_score())
            reward = self._simulate(child, composite, world_state)
            self._backpropagate(child, reward)
            root.visits += 1
        best = max(root.children.values(), key=lambda n: n.value)
        return best.action, best.value, sum(n.visits for n in root.children.values())


class ProspectTheoryAdjuster:
    def __init__(self, alpha=0.88, beta=0.88, lambda_=2.25, gamma=0.65):
        self.alpha = alpha
        self.beta = beta
        self.lambda_ = lambda_
        self.gamma = gamma

    def value_function(self, x: float, reference: float = 0.5) -> float:
        d = x - reference
        return d**self.alpha if d >= 0 else -self.lambda_ * ((-d)**self.beta)

    def probability_weight(self, p: float) -> float:
        return (p**self.gamma) / ((p**self.gamma + (1-p)**self.gamma)**(1/self.gamma))

    def adjust(self, score: float, tail_risk: float) -> float:
        return float(np.clip(score * (1 - self.probability_weight(tail_risk) * 0.3), 0, 1))


class MetaArbiter:
    def __init__(self, v_weight=0.40, cv_weight=0.35, world_weight=0.25,
                 target=0.97, n_world_scenarios=20, n_mcts_simulations=200):
        self.vw = v_weight
        self.cvw = cv_weight
        self.ww = world_weight
        self.target = target
        self.world_model = WorldModelSimulator(n_scenarios=n_world_scenarios)
        self.mcts = MCTSDecisionExplorer(n_simulations=n_mcts_simulations)
        self.prospect = ProspectTheoryAdjuster()

    def _build_reasoning(self, v, cv, w, composite, winner, ws, action, mcts_val):
        return [
            f"[1/6] VALIDATION SCORE: {v:.4f} — {'PASSOU ≥97%' if v>=self.target else 'ABAIXO DO TARGET'}",
            f"[2/6] COUNTER-VALIDATION SCORE: {cv:.4f} — {'ROBUSTO ≥97%' if cv>=self.target else 'VULNERABILIDADES'}",
            f"[3/6] WINNER: {winner} com score {max(v,cv):.4f}",
            f"[4/6] WORLD MODEL: mean={ws.mean_outcome:.3f} | std={ws.std_outcome:.3f} | tail_risk={ws.tail_risk:.3f} | P5={ws.percentile_5:.3f} | P95={ws.percentile_95:.3f}",
            f"[5/6] COMPOSITE (V×{self.vw}+CV×{self.cvw}+W×{self.ww}): {composite:.4f}",
            f"[6/6] MCTS DECISION: '{action}' (value={mcts_val:.4f}) após exploração da árvore de decisão",
        ]

    def arbitrate(self, v_decision, cv_decision, payload: Any) -> FinalDecision:
        v  = v_decision.fused_confidence
        cv = cv_decision.cv_fused_score
        winner, winner_score = ('VALIDATION', v) if v >= cv else ('COUNTER-VALIDATION', cv)

        ws = self.world_model.simulate(initial_score=winner_score, decision_quality=(v+cv)/2)
        w = ws.mean_outcome
        composite = self.vw*v + self.cvw*cv + self.ww*w
        risk_adj = self.prospect.adjust(composite, ws.tail_risk)

        action, mcts_val, mcts_nodes = self.mcts.search(composite, ws)
        if not v_decision.passed or not cv_decision.passed:
            action, mcts_val = 'ESCALATE', composite * 0.7

        return FinalDecision(
            decision=action, confidence=float(risk_adj),
            v_score=round(v,4), cv_score=round(cv,4), world_score=round(w,4),
            composite_score=round(composite,4), winner=winner, winner_score=round(winner_score,4),
            risk_adjusted_score=round(risk_adj,4), mcts_explored_nodes=mcts_nodes,
            reasoning=self._build_reasoning(v, cv, w, composite, winner, ws, action, mcts_val),
        )


class DVCAPipeline:
    """Pipeline completo: Calibração → Validação → Contra-Validação → Arbitragem."""

    def __init__(self, auto_calibrate: bool = True):
        from validation_engine import ValidationEngine
        from counter_validation_engine import CounterValidationEngine
        from calibration_agents import MasterCalibrationOrchestrator

        self.v_engine  = ValidationEngine(target_confidence=0.97)
        self.cv_engine = CounterValidationEngine(target_robustness=0.97)
        self.arbiter   = MetaArbiter(n_world_scenarios=20, n_mcts_simulations=200)
        self.calibrated = False

        if auto_calibrate:
            orch = MasterCalibrationOrchestrator(target_accuracy=0.97, max_rounds=2)
            print("\n[DVCA] Running calibration agents...")
            rpts = orch.calibrate_engine(self.v_engine, self.cv_engine)
            s = rpts['summary']
            print(f"[DVCA] Calibration: ECE={s['avg_ece_final']:.5f} | Acc={s['estimated_accuracy']:.4f} | Target={s['target_met']}")
            self.calibrated = True

    def run(self, payload: Dict) -> FinalDecision:
        print("\n[DVCA] ─── FULL PIPELINE ───")
        v_dec  = self.v_engine.validate(payload)
        print(f"[DVCA] Validation: {v_dec.fused_confidence:.4f} | passed={v_dec.passed}")
        cv_dec = self.cv_engine.counter_validate(payload)
        print(f"[DVCA] Counter-Val: {cv_dec.cv_fused_score:.4f} | passed={cv_dec.passed}")
        return self.arbiter.arbitrate(v_dec, cv_dec, payload)


if __name__ == '__main__':
    np.random.seed(42)

    pipeline = DVCAPipeline(auto_calibrate=True)

    payload = {
        'evidence': True, 'contradicts': False,
        'arguments': ['a1','a2','a3','a4'], 'testable': True,
        'sources': [f's{i}' for i in range(8)],
        'data_points': 650, 'peer_reviewed': 8,
        'causal_links': 6, 'confounders_addressed': True,
        'temporal_order_valid': True, 'novelty_index': 0.35,
        'expert_consensus': 0.88, 'detected_biases': [],
        'bias_mitigation': True,
        'domains': ['economics','sociology','physics'],
        'cross_domain_coherence': 0.90, 'value': 0.87, 'uncertainty': 0.06,
        'time_horizon_years': 25, 'longitudinal_evidence': True,
        'harm_potential': 0.04, 'fairness_score': 0.93, 'transparency': 0.91,
        'source_distribution': [0.4, 0.35, 0.25],
        'known_counter_examples': 1, 'edge_cases_tested': 6,
        'justified_premises': 4, 'implicit_assumptions': 1,
        'contrary_sources': 2, 'survivorship_addressed': True,
        'internal_conflicts': 0, 'mutual_exclusive_claims': 0,
    }

    result = pipeline.run(payload)

    print(f"\n{'═'*62}")
    print(f"  DVCA FINAL DECISION — META-ARBITER")
    print(f"{'═'*62}")
    print(f"  DECISION:       {result.decision}")
    print(f"  CONFIDENCE:     {result.confidence:.4f}")
    print(f"  WINNER:         {result.winner} ({result.winner_score:.4f})")
    print(f"  V Score:        {result.v_score:.4f}")
    print(f"  CV Score:       {result.cv_score:.4f}")
    print(f"  World Model:    {result.world_score:.4f}")
    print(f"  Composite:      {result.composite_score:.4f}")
    print(f"  Risk-Adjusted:  {result.risk_adjusted_score:.4f}")
    print(f"  MCTS Nodes:     {result.mcts_explored_nodes}")
    print(f"\n  CHAIN-OF-THOUGHT:")
    for step in result.reasoning:
        print(f"    {step}")
    print(f"{'═'*62}\n")

    out = {
        'decision': result.decision, 'confidence': result.confidence,
        'v_score': result.v_score, 'cv_score': result.cv_score,
        'world_score': result.world_score, 'composite_score': result.composite_score,
        'winner': result.winner, 'winner_score': result.winner_score,
        'risk_adjusted_score': result.risk_adjusted_score,
        'mcts_nodes': result.mcts_explored_nodes, 'reasoning': result.reasoning,
    }
    out_path = os.path.join(os.path.dirname(__file__), 'last_decision.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"[DVCA] Result saved to {out_path}")
