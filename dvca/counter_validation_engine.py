"""
═══════════════════════════════════════════════════════════════════════════
DVCA — Dual Validation / Counter-Validation Arbiter System
MODULE 2: COUNTER-VALIDATION ENGINE
═══════════════════════════════════════════════════════════════════════════
Ciências Base:
  - Adversarial Machine Learning   (Goodfellow et al. 2015; NeurIPS AdvML 2024)
  - Devil's Advocate / AI Safety   (Irving et al. 2018)
  - Falsificationismo              (Popper 1959)
  - Stress Testing                 (Basel III / BIS)
  - Red-Teaming LLMs               (Anthropic/OpenAI 2022-2024)
"""

import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field
import time
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from validation_engine import BaseValidator, ValidationResult, BayesianFusion


@dataclass
class CounterValidationResult:
    cv_sync_score: float
    cv_async_score: float
    cv_fused_score: float
    passed: bool
    attack_results: List[ValidationResult]
    strongest_attack: str
    vulnerability_map: Dict[str, float]
    meta: Dict[str, Any]


class FalsificationAttacker(BaseValidator):
    def __init__(self):
        super().__init__('CV1_Falsification', threshold=0.97)
        self.set_calibration(A=2.0, B=-0.3)

    def _raw_score(self, payload: Any) -> float:
        if not isinstance(payload, dict): return 0.4
        if not payload.get('testable', False): return 0.3
        counter_penalty = min(0.5, payload.get('known_counter_examples', 0) * 0.15)
        edge_bonus = min(0.2, payload.get('edge_cases_tested', 0) * 0.04)
        return float(np.clip(0.85 - counter_penalty + edge_bonus + np.random.normal(0, 0.025), 0, 1))


class AssumptionChallengeAttacker(BaseValidator):
    def __init__(self):
        super().__init__('CV2_AssumptionChallenge', threshold=0.97)
        self.set_calibration(A=1.9, B=-0.2)

    def _raw_score(self, payload: Any) -> float:
        if not isinstance(payload, dict): return 0.5
        n = len(payload.get('arguments', []))
        ratio = payload.get('justified_premises', 0) / max(n, 1)
        penalty = min(0.3, payload.get('implicit_assumptions', 3) * 0.08)
        return float(np.clip(ratio * 0.7 + 0.3 - penalty + np.random.normal(0, 0.02), 0, 1))


class ConfirmationBiasAttacker(BaseValidator):
    def __init__(self):
        super().__init__('CV3_ConfirmationBias', threshold=0.97)
        self.set_calibration(A=2.1, B=-0.35)

    def _raw_score(self, payload: Any) -> float:
        if not isinstance(payload, dict): return 0.5
        total = max(len(payload.get('sources', ['x'])), 1)
        diversity = payload.get('contrary_sources', 0) / total
        surv = payload.get('survivorship_addressed', False)
        return float(np.clip(diversity * 0.6 + 0.4 * int(surv) + np.random.normal(0, 0.02), 0, 1))


class MonteCarloStressTester(BaseValidator):
    def __init__(self, n: int = 1000):
        super().__init__('CV4_MonteCarloStress', threshold=0.97)
        self.n = n
        self.set_calibration(A=2.3, B=-0.4)

    def _raw_score(self, payload: Any) -> float:
        val = payload.get('value', 0.8) if isinstance(payload, dict) else 0.8
        sigma = payload.get('uncertainty', 0.1) if isinstance(payload, dict) else 0.1
        samples = np.random.normal(val, sigma, self.n)
        return float(np.clip(np.mean(samples >= 0.65) + np.random.normal(0, 0.01), 0, 1))


class AlternativeHypothesisScorer(BaseValidator):
    def __init__(self, n_alternatives: int = 5):
        super().__init__('CV5_AltHypothesis', threshold=0.97)
        self.n_alternatives = n_alternatives
        self.set_calibration(A=1.85, B=-0.2)

    def _raw_score(self, payload: Any) -> float:
        val = payload.get('value', 0.8) if isinstance(payload, dict) else 0.8
        alts = np.abs(np.random.normal(val * 0.7, 0.1, self.n_alternatives))
        bf = val / (np.mean(alts) + 1e-6)
        return float(np.clip(bf / 4.0 + np.random.normal(0, 0.02), 0, 1))


class AdversarialPerturbationAttacker(BaseValidator):
    def __init__(self, epsilon: float = 0.08):
        super().__init__('CV6_AdversarialPerturbation', threshold=0.97)
        self.epsilon = epsilon
        self.set_calibration(A=2.0, B=-0.25)

    def _raw_score(self, payload: Any) -> float:
        val = payload.get('value', 0.8) if isinstance(payload, dict) else 0.8
        grad_sign = np.sign(np.random.randn(50))
        perturbed = val + self.epsilon * grad_sign
        return float(np.clip(np.mean(np.clip(perturbed, 0, 1) >= 0.65) + np.random.normal(0, 0.02), 0, 1))


class InternalContradictionMiner(BaseValidator):
    def __init__(self):
        super().__init__('CV7_InternalContradiction', threshold=0.97)
        self.set_calibration(A=2.2, B=-0.4)

    def _raw_score(self, payload: Any) -> float:
        if not isinstance(payload, dict): return 0.6
        penalty = (
            0.3 * int(payload.get('contradicts', False)) +
            0.1 * payload.get('internal_conflicts', 0) +
            0.15 * payload.get('mutual_exclusive_claims', 0)
        )
        return float(np.clip(1.0 - penalty + np.random.normal(0, 0.02), 0, 1))


class CounterValidationEngine:
    """Red-team completo: 3 sync + 4 async. Score alto = tese robusta."""

    def __init__(self, target_robustness: float = 0.97):
        self.target = target_robustness
        self.fusion = BayesianFusion(prior=0.6)
        self.cv_sync = [FalsificationAttacker(), AssumptionChallengeAttacker(), ConfirmationBiasAttacker()]
        self.cv_async = [MonteCarloStressTester(), AlternativeHypothesisScorer(),
                         AdversarialPerturbationAttacker(), InternalContradictionMiner()]
        self.sync_weights  = [0.35, 0.35, 0.30]
        self.async_weights = [0.30, 0.25, 0.25, 0.20]

    def _run_cv_sync(self, payload) -> Tuple[float, List[ValidationResult]]:
        results, ep = [], dict(payload) if isinstance(payload, dict) else {'value': 0.8}
        for i, v in enumerate(self.cv_sync):
            r = v.validate(ep, mode='sync')
            ep[f'cv{i+1}_resistance'] = r.confidence
            results.append(r)
        return self.fusion.fuse([r.confidence for r in results], self.sync_weights), results

    def _run_cv_async(self, payload) -> Tuple[float, List[ValidationResult]]:
        rmap = {}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(v.validate, payload, 'async'): v.validator_id for v in self.cv_async}
            for f in as_completed(futures):
                vid = futures[f]
                try: rmap[vid] = f.result()
                except Exception as e:
                    rmap[vid] = ValidationResult(vid, 0.5, 0.5, False, {'error': str(e)}, 0, 'async')
        ordered = [rmap[v.validator_id] for v in self.cv_async]
        return self.fusion.fuse([r.confidence for r in ordered], self.async_weights), ordered

    def counter_validate(self, payload: Any) -> CounterValidationResult:
        ss, sa, sr, ar = [0.0], [0.0], [[]], [[]]

        def rs(): ss[0], sr[0] = self._run_cv_sync(payload)
        def ra(): sa[0], ar[0] = self._run_cv_async(payload)

        ts, ta = threading.Thread(target=rs), threading.Thread(target=ra)
        ts.start(); ta.start(); ts.join(); ta.join()

        fused = self.fusion.fuse([ss[0], sa[0]], [0.5, 0.5])
        all_r = sr[0] + ar[0]
        vuln = {r.validator_id: round(1 - r.confidence, 4) for r in all_r}
        strongest = max(vuln, key=vuln.get)

        return CounterValidationResult(
            cv_sync_score=float(ss[0]), cv_async_score=float(sa[0]),
            cv_fused_score=float(fused), passed=fused >= self.target,
            attack_results=all_r, strongest_attack=strongest, vulnerability_map=vuln,
            meta={'target': self.target, 'n_attackers': 7},
        )


if __name__ == '__main__':
    np.random.seed(42)
    engine = CounterValidationEngine()
    payload = {
        'testable': True, 'known_counter_examples': 1, 'edge_cases_tested': 5,
        'arguments': ['a1','a2','a3'], 'justified_premises': 3, 'implicit_assumptions': 1,
        'sources': ['s1','s2','s3','s4'], 'contrary_sources': 2,
        'survivorship_addressed': True, 'value': 0.85, 'uncertainty': 0.07,
        'contradicts': False, 'internal_conflicts': 0, 'mutual_exclusive_claims': 0,
    }
    r = engine.counter_validate(payload)
    print(f"\n{'='*60}\n  COUNTER-VALIDATION ENGINE\n{'='*60}")
    print(f"  CV Sync:   {r.cv_sync_score:.4f}")
    print(f"  CV Async:  {r.cv_async_score:.4f}")
    print(f"  Fused:     {r.cv_fused_score:.4f}")
    print(f"  ROBUST:    {r.passed}")
    print(f"  Strongest attack: {r.strongest_attack}")
    print(f"\n  Vulnerability Map:")
    for k, v in sorted(r.vulnerability_map.items(), key=lambda x: -x[1]):
        print(f"    {k:<35} vuln={v:.4f} {'█'*int(v*30)}")
    print(f"{'='*60}\n")
