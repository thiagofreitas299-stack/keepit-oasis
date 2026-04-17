"""
═══════════════════════════════════════════════════════════════════════════
DVCA — Dual Validation / Counter-Validation Arbiter System
MODULE 3: CALIBRATION & TRAINING AGENTS
═══════════════════════════════════════════════════════════════════════════
Ciências Base:
  - Calibration Theory    (Guo et al. 2017 NeurIPS)
  - Platt Scaling         (Platt 1999)
  - ECE                   (Naeini et al. 2015)
  - Meta-Learning/AutoML  (Vanschoren 2019)
  - SGD / Online Learning (Shalev-Shwartz 2011)
"""

import numpy as np
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
import sys, os
sys.path.insert(0, os.path.dirname(__file__))


# ─────────────────────────────────────────────────────────────────
# MÉTRICAS DE CALIBRAÇÃO
# ─────────────────────────────────────────────────────────────────

def expected_calibration_error(confidences: np.ndarray, accuracies: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
    ece, n = 0.0, len(confidences)
    for i in range(n_bins):
        mask = (confidences >= bins[i]) & (confidences < bins[i+1])
        if mask.sum() == 0: continue
        ece += (mask.sum() / n) * abs(confidences[mask].mean() - accuracies[mask].mean())
    return float(ece)

def brier_score(probs: np.ndarray, labels: np.ndarray) -> float:
    return float(np.mean((probs - labels) ** 2))

def log_loss(probs: np.ndarray, labels: np.ndarray, eps: float = 1e-7) -> float:
    probs = np.clip(probs, eps, 1-eps)
    return float(-np.mean(labels * np.log(probs) + (1-labels) * np.log(1-probs)))


# ─────────────────────────────────────────────────────────────────
# BASE CALIBRATION AGENT
# ─────────────────────────────────────────────────────────────────

@dataclass
class CalibrationReport:
    agent_id: str
    validator_id: str
    old_params: Dict
    new_params: Dict
    ece_before: float
    ece_after: float
    improvement_pct: float
    n_samples_used: int
    iterations: int


class BaseCalibrationAgent:
    def __init__(self, agent_id: str, lr: float = 0.05, max_iter: int = 200):
        self.agent_id = agent_id
        self.lr = lr
        self.max_iter = max_iter
        self._calibration_history: List[CalibrationReport] = []

    def _sigmoid(self, x: np.ndarray, A: float, B: float) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-(A * x + B)))

    def _nll(self, x: np.ndarray, y: np.ndarray, A: float, B: float) -> float:
        p = np.clip(self._sigmoid(x, A, B), 1e-7, 1-1e-7)
        return -np.mean(y * np.log(p) + (1-y) * np.log(1-p))

    def _grad_step(self, x: np.ndarray, y: np.ndarray, A: float, B: float) -> Tuple[float, float]:
        h = 1e-5
        dA = (self._nll(x, y, A+h, B) - self._nll(x, y, A-h, B)) / (2*h)
        dB = (self._nll(x, y, A, B+h) - self._nll(x, y, A, B-h)) / (2*h)
        return A - self.lr * dA, B - self.lr * dB

    def calibrate(self, validator, raw_scores: np.ndarray, ground_truth: np.ndarray) -> CalibrationReport:
        old_A = validator._calibration_params.get('A', 1.0)
        old_B = validator._calibration_params.get('B', 0.0)
        confs_before = self._sigmoid(raw_scores, old_A, old_B)
        ece_before = expected_calibration_error(confs_before, ground_truth)
        A, B = old_A, old_B
        for _ in range(self.max_iter):
            A, B = self._grad_step(raw_scores, ground_truth, A, B)
        confs_after = self._sigmoid(raw_scores, A, B)
        ece_after = expected_calibration_error(confs_after, ground_truth)
        validator.set_calibration(A, B)
        improvement = ((ece_before - ece_after) / max(ece_before, 1e-8)) * 100
        report = CalibrationReport(
            agent_id=self.agent_id, validator_id=validator.validator_id,
            old_params={'A': round(old_A, 4), 'B': round(old_B, 4)},
            new_params={'A': round(A, 4), 'B': round(B, 4)},
            ece_before=round(ece_before, 6), ece_after=round(ece_after, 6),
            improvement_pct=round(improvement, 2), n_samples_used=len(raw_scores),
            iterations=self.max_iter,
        )
        self._calibration_history.append(report)
        return report


# ─────────────────────────────────────────────────────────────────
# FUSION WEIGHT OPTIMIZER
# ─────────────────────────────────────────────────────────────────

class FusionWeightOptimizer:
    def __init__(self, n_validators: int, lr: float = 0.02, max_iter: int = 300):
        self.n = n_validators
        self.lr = lr
        self.max_iter = max_iter
        self.weights = np.ones(n_validators) / n_validators

    def _ensemble_score(self, conf_matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
        w = np.clip(weights, 0, None)
        w = w / w.sum()
        return conf_matrix @ w

    def _loss(self, conf_matrix: np.ndarray, labels: np.ndarray, weights: np.ndarray) -> float:
        preds = np.clip(self._ensemble_score(conf_matrix, weights), 1e-7, 1-1e-7)
        return -np.mean(labels * np.log(preds) + (1-labels) * np.log(1-preds))

    def optimize(self, conf_matrix: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, List[float]]:
        w = self.weights.copy()
        losses = []
        for step in range(self.max_iter):
            grad = np.zeros(self.n)
            h = 1e-5
            for i in range(self.n):
                wp = w.copy(); wp[i] += h
                wm = w.copy(); wm[i] -= h
                grad[i] = (self._loss(conf_matrix, labels, wp) - self._loss(conf_matrix, labels, wm)) / (2*h)
            w = w - self.lr * grad
            w = np.clip(w, 0, None)
            w = w / w.sum()
            if step % 30 == 0:
                losses.append(self._loss(conf_matrix, labels, w))
        if np.any(np.isnan(w)) or w.sum() < 1e-8:
            w = np.ones(self.n) / self.n
        self.weights = w
        return w, losses


# ─────────────────────────────────────────────────────────────────
# SYNTHETIC DATA GENERATOR
# ─────────────────────────────────────────────────────────────────

class SyntheticTrainingDataGenerator:
    def __init__(self, n_samples: int = 500, seed: int = 42):
        self.n = n_samples
        self.rng = np.random.RandomState(seed)

    def generate(self) -> Tuple[List[Dict], np.ndarray]:
        payloads, labels = [], []
        for _ in range(self.n):
            q = self.rng.beta(3, 1.5)
            label = int(q > 0.65)
            payload = {
                'evidence': q > 0.5, 'contradicts': q < 0.3,
                'arguments': [f'a{i}' for i in range(int(q*5)+1)],
                'testable': q > 0.4,
                'sources': [f's{i}' for i in range(int(q*8)+1)],
                'data_points': int(q*800), 'peer_reviewed': int(q*9),
                'causal_links': int(q*7), 'confounders_addressed': q > 0.55,
                'temporal_order_valid': q > 0.5,
                'novelty_index': float(self.rng.uniform(0.1, 0.9)),
                'expert_consensus': float(np.clip(q*0.9 + self.rng.normal(0, 0.05), 0, 1)),
                'detected_biases': [] if q > 0.7 else ['anchoring'],
                'bias_mitigation': q > 0.6,
                'domains': ['economics','sociology'] if q > 0.6 else ['economics'],
                'cross_domain_coherence': float(np.clip(q + self.rng.normal(0, 0.05), 0, 1)),
                'value': float(np.clip(q + self.rng.normal(0, 0.06), 0, 1)),
                'uncertainty': float(self.rng.uniform(0.04, 0.15)),
                'time_horizon_years': int(q*30), 'longitudinal_evidence': q > 0.65,
                'harm_potential': float(self.rng.uniform(0, 0.2)),
                'fairness_score': float(q*0.95), 'transparency': float(q*0.9),
                'source_distribution': self.rng.dirichlet([3, 2, 1]).tolist(),
                'known_counter_examples': int(self.rng.poisson(max(0, 1-q))),
                'edge_cases_tested': int(q*8),
                'justified_premises': int(q*5)+1,
                'implicit_assumptions': max(0, int(self.rng.poisson(max(0, 3-q*2)))),
                'contrary_sources': int(q*3), 'survivorship_addressed': q > 0.6,
                'internal_conflicts': 0 if q > 0.7 else int(self.rng.poisson(1)),
                'mutual_exclusive_claims': 0 if q > 0.8 else int(self.rng.poisson(0.5)),
            }
            payloads.append(payload)
            labels.append(label)
        return payloads, np.array(labels)


# ─────────────────────────────────────────────────────────────────
# MASTER CALIBRATION ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────

class MasterCalibrationOrchestrator:
    def __init__(self, target_accuracy: float = 0.97, max_rounds: int = 5):
        self.target = target_accuracy
        self.max_rounds = max_rounds
        self.validation_agent  = BaseCalibrationAgent('CA_Validation', lr=0.05, max_iter=300)
        self.counter_agent     = BaseCalibrationAgent('CA_Counter',    lr=0.05, max_iter=300)
        self.weight_optimizer_v  = FusionWeightOptimizer(n_validators=10, lr=0.02, max_iter=400)
        self.weight_optimizer_cv = FusionWeightOptimizer(n_validators=7,  lr=0.02, max_iter=400)
        self.data_gen = SyntheticTrainingDataGenerator(n_samples=800)

    def _collect_raw_scores(self, validators, payloads):
        scores = []
        for payload in payloads:
            row = [v._raw_score(payload) for v in validators]
            scores.append(row)
        return np.array(scores)

    def calibrate_engine(self, validation_engine, counter_engine) -> Dict:
        payloads, labels = self.data_gen.generate()
        labels_f = labels.astype(float)
        all_reports = {'validation': [], 'counter': [], 'weights': {}}

        for round_n in range(1, self.max_rounds+1):
            print(f"\n  [CalibAgent] Round {round_n}/{self.max_rounds}")

            # Validation Engine
            all_v = validation_engine.sync_chain + validation_engine.async_pool
            v_scores = self._collect_raw_scores(all_v, payloads)
            v_reports = []
            for i, validator in enumerate(all_v):
                r = self.validation_agent.calibrate(validator, v_scores[:, i], labels_f)
                v_reports.append(r)
                print(f"    {validator.validator_id}: ECE {r.ece_before:.4f}→{r.ece_after:.4f} ({r.improvement_pct:+.1f}%)")

            # Optimize V weights
            v_confs = 1.0 / (1.0 + np.exp(-np.column_stack([
                v._calibration_params.get('A', 1.0) * v_scores[:, i] + v._calibration_params.get('B', 0.0)
                for i, v in enumerate(all_v)
            ])))
            opt_vw, _ = self.weight_optimizer_v.optimize(v_confs, labels_f)
            if np.any(np.isnan(opt_vw)): opt_vw = np.ones(10)/10
            sw = opt_vw[:5]/opt_vw[:5].sum()
            aw = opt_vw[5:]/opt_vw[5:].sum()
            validation_engine.sync_weights  = list(sw)
            validation_engine.async_weights = list(aw)

            # Counter Engine
            all_cv = counter_engine.cv_sync + counter_engine.cv_async
            cv_scores = self._collect_raw_scores(all_cv, payloads)
            cv_reports = []
            for i, validator in enumerate(all_cv):
                r = self.counter_agent.calibrate(validator, cv_scores[:, i], labels_f)
                cv_reports.append(r)
                print(f"    {validator.validator_id}: ECE {r.ece_before:.4f}→{r.ece_after:.4f} ({r.improvement_pct:+.1f}%)")

            # Optimize CV weights
            cv_confs = 1.0 / (1.0 + np.exp(-np.column_stack([
                v._calibration_params.get('A', 1.0) * cv_scores[:, i] + v._calibration_params.get('B', 0.0)
                for i, v in enumerate(all_cv)
            ])))
            opt_cvw, _ = self.weight_optimizer_cv.optimize(cv_confs, labels_f)
            if np.any(np.isnan(opt_cvw)): opt_cvw = np.ones(7)/7
            counter_engine.sync_weights  = list(opt_cvw[:3]/opt_cvw[:3].sum())
            counter_engine.async_weights = list(opt_cvw[3:]/opt_cvw[3:].sum())

            all_reports['validation'] += v_reports
            all_reports['counter']   += cv_reports

        final_eces = [r.ece_after for r in all_reports['validation'] + all_reports['counter']]
        avg_ece = np.mean(final_eces)
        est_acc = float(np.clip(1 - avg_ece, 0, 1))
        all_reports['summary'] = {
            'rounds': self.max_rounds,
            'avg_ece_final': round(avg_ece, 5),
            'estimated_accuracy': round(est_acc, 4),
            'target_met': est_acc >= self.target,
        }
        return all_reports


if __name__ == '__main__':
    np.random.seed(99)
    from validation_engine import ValidationEngine
    from counter_validation_engine import CounterValidationEngine

    v_engine  = ValidationEngine(target_confidence=0.97)
    cv_engine = CounterValidationEngine(target_robustness=0.97)
    orch = MasterCalibrationOrchestrator(target_accuracy=0.97, max_rounds=3)

    print("\n" + "="*60)
    print("  MASTER CALIBRATION ORCHESTRATOR")
    print("="*60)

    reports = orch.calibrate_engine(v_engine, cv_engine)
    s = reports['summary']

    print(f"\n  CALIBRATION SUMMARY")
    print(f"  Rounds:           {s['rounds']}")
    print(f"  Avg ECE (final):  {s['avg_ece_final']}")
    print(f"  Est. Accuracy:    {s['estimated_accuracy']:.4f}")
    print(f"  Target ≥97% Met:  {s['target_met']}")
    print("="*60 + "\n")
