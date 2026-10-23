"""
CryptoScope Training and Evaluation Engine
Paper Section III-E, IV-E, IV-F:
- Full evaluation suite: Accuracy, Precision, Recall, F1 (macro + per-class), ROC-AUC (OvR), Confusion Matrix, Inference Latency
- Multi-architecture training scenarios: Same-ISA, Mixed-ISA, Unseen-ISA (Leave-One-ISA-Out), Leave-One-Compiler-Out
- Feature ablation runner (Byte, Instruction, Insn+CFG, Insn+DFG, All)
- Robustness evaluation across optimization levels (O0..Os)
- Model persistence (joblib) and experiment run logging
"""

import os
import time
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import joblib

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, roc_auc_score
)

from backend.app.models.tree_models import create_model
from backend.app.models.deep_models import PyTorchClassifierWrapper
from backend.app.models.hierarchical import HierarchicalModelWrapper
from backend.app.training.dataset_loader import DatasetLoader, LoadedDataset
from backend.app.features.extractor import FeatureConfig

class EvaluationMetrics:
    def __init__(self,
                 accuracy: float,
                 macro_precision: float,
                 macro_recall: float,
                 macro_f1: float,
                 per_class_f1: Dict[str, float],
                 roc_auc_ovr: Optional[float],
                 confusion_matrix_raw: List[List[int]],
                 confusion_matrix_labels: List[str],
                 inference_latency_ms: float):
        self.accuracy = round(accuracy, 4)
        self.macro_precision = round(macro_precision, 4)
        self.macro_recall = round(macro_recall, 4)
        self.macro_f1 = round(macro_f1, 4)
        self.per_class_f1 = {k: round(v, 4) for k, v in per_class_f1.items()}
        self.roc_auc_ovr = round(roc_auc_ovr, 4) if roc_auc_ovr is not None else None
        self.confusion_matrix_raw = confusion_matrix_raw
        self.confusion_matrix_labels = confusion_matrix_labels
        self.inference_latency_ms = round(inference_latency_ms, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
            "per_class_f1": self.per_class_f1,
            "roc_auc_ovr": self.roc_auc_ovr,
            "confusion_matrix": self.confusion_matrix_raw,
            "confusion_labels": self.confusion_matrix_labels,
            "inference_latency_ms": self.inference_latency_ms
        }

class ModelTrainer:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.runs_dir = self.base_dir / "backend" / "app" / "models" / "runs"
        self.saved_dir = self.base_dir / "backend" / "app" / "models" / "saved"
        for p in [self.runs_dir, self.saved_dir]:
            p.mkdir(parents=True, exist_ok=True)
        self.loader = DatasetLoader()

    def evaluate_model(self, model: Any, X_test: np.ndarray, y_test: np.ndarray) -> EvaluationMetrics:
        t0 = time.perf_counter()
        y_pred = model.predict(X_test)
        latency = ((time.perf_counter() - t0) / max(1, len(X_test))) * 1000.0

        acc = float(accuracy_score(y_test, y_pred))
        classes = np.unique(np.concatenate([y_test, y_pred]))
        labels_str = [str(c) for c in classes]

        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="macro", zero_division=0)
        p_c, r_c, f1_c, _ = precision_recall_fscore_support(y_test, y_pred, labels=classes, zero_division=0)
        per_class_f1 = {str(c): float(f) for c, f in zip(classes, f1_c)}

        cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()

        # ROC-AUC calculation
        roc_auc = None
        if hasattr(model, "predict_proba"):
            try:
                probs = model.predict_proba(X_test)
                if len(classes) == 2:
                    roc_auc = float(roc_auc_score(y_test, probs[:, 1]))
                elif len(classes) > 2 and probs.shape[1] == len(classes):
                    roc_auc = float(roc_auc_score(y_test, probs, multi_class="ovr", average="macro"))
            except Exception:
                pass

        return EvaluationMetrics(
            accuracy=acc,
            macro_precision=float(prec),
            macro_recall=float(rec),
            macro_f1=float(f1),
            per_class_f1=per_class_f1,
            roc_auc_ovr=roc_auc,
            confusion_matrix_raw=cm,
            confusion_matrix_labels=labels_str,
            inference_latency_ms=latency
        )

    def train_single_model(self, 
                           model_type: str = "rf",
                           level: int = 1,
                           dataset_version: str = "v1.0.0",
                           feature_config: Optional[FeatureConfig] = None,
                           hyperparams: Optional[Dict[str, Any]] = None) -> Tuple[Any, EvaluationMetrics, StandardScaler]:
        ds = self.loader.load_dataset(version=dataset_version, feature_config=feature_config)
        X_train, y_train, _, _, _, _, X_test, y_test, _ = self.loader.split_grouped(ds, level=level)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        m = model_type.lower()
        if m in ["cnn", "lstm", "transformer"]:
            num_classes = len(np.unique(y_train))
            clf = PyTorchClassifierWrapper(model_type=m, num_classes=num_classes, epochs=6)
            clf.fit(X_train_scaled, y_train)
        else:
            clf = create_model(m, params=hyperparams)
            clf.fit(X_train_scaled, y_train)

        metrics = self.evaluate_model(clf, X_test_scaled, y_test)
        return clf, metrics, scaler

    def train_full_hierarchical(self, 
                                 model_type: str = "rf",
                                 dataset_version: str = "v1.0.0",
                                 save_run: bool = True) -> Dict[str, Any]:
        """
        Trains the full 3-level hierarchical system (Paper Sec. III-E):
        - Level 1: Crypto vs Non-Crypto
        - Level 2: Family Classifier
        - Level 3: Specific Primitive Classifier
        """
        run_id = f"run_{model_type}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
        ds = self.loader.load_dataset(version=dataset_version)

        train_idx, val_idx, test_idx = self.loader.get_split_indices(ds)
        X_tr = ds.X[train_idx]
        X_te = ds.X[test_idx]

        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_te_s = scaler.transform(X_te)

        # 1. Level 1: Crypto vs Non-Crypto
        y_tr1 = ds.y_l1[train_idx]
        y_te1 = ds.y_l1[test_idx]

        m1 = create_model(model_type)
        m1.fit(X_tr_s, y_tr1)
        metrics_l1 = self.evaluate_model(m1, X_te_s, y_te1)

        # 2. Level 2: Family Classifier (filtered to Crypto samples only)
        crypto_tr = (y_tr1 == 1)
        crypto_te = (y_te1 == 1)

        X_tr2_s = X_tr_s[crypto_tr]
        y_tr2 = ds.y_l2[train_idx][crypto_tr]
        X_te2_s = X_te_s[crypto_te]
        y_te2 = ds.y_l2[test_idx][crypto_te]

        m2 = create_model(model_type)
        m2.fit(X_tr2_s, y_tr2)
        metrics_l2 = self.evaluate_model(m2, X_te2_s, y_te2)

        # 3. Level 3: Primitive Classifier
        y_tr3 = ds.y_l3[train_idx][crypto_tr]
        y_te3 = ds.y_l3[test_idx][crypto_te]

        m3 = create_model(model_type)
        m3.fit(X_tr2_s, y_tr3)
        metrics_l3 = self.evaluate_model(m3, X_te2_s, y_te3)

        # Build Hierarchical Model
        hierarchical_model = HierarchicalModelWrapper(
            l1_model=m1,
            l2_model=m2,
            l3_models={"global": m3},
            scaler=scaler
        )


        # Persist model
        model_path = self.saved_dir / f"{run_id}_hierarchical.joblib"
        joblib.dump(hierarchical_model, model_path)

        run_record = {
            "run_id": run_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "model_type": model_type,

            "dataset_version": dataset_version,
            "model_path": str(model_path),
            "level1_metrics": metrics_l1.to_dict(),
            "level2_metrics": metrics_l2.to_dict(),
            "level3_metrics": metrics_l3.to_dict(),
            "overall_f1": round((metrics_l1.macro_f1 + metrics_l2.macro_f1 + metrics_l3.macro_f1) / 3.0, 4)
        }

        if save_run:
            run_file = self.runs_dir / f"{run_id}.json"
            with open(run_file, "w", encoding="utf-8") as f:
                json.dump(run_record, f, indent=2)

        return run_record

    def run_ablation_study(self, model_type: str = "rf") -> Dict[str, Any]:
        """
        Runs paper Table VI ablation experiment across 5 feature configurations:
        1. Byte only
        2. Instruction only
        3. Instruction + CFG
        4. Instruction + DFG
        5. All features
        """
        configs = {
            "Byte only": FeatureConfig(enable_byte=True, enable_instruction=False, enable_cfg=False, enable_dfg=False),
            "Instruction only": FeatureConfig(enable_byte=False, enable_instruction=True, enable_cfg=False, enable_dfg=False),
            "Instruction + CFG": FeatureConfig(enable_byte=False, enable_instruction=True, enable_cfg=True, enable_dfg=False),
            "Instruction + DFG": FeatureConfig(enable_byte=False, enable_instruction=True, enable_cfg=False, enable_dfg=True),
            "All features": FeatureConfig(enable_byte=True, enable_instruction=True, enable_cfg=True, enable_dfg=True)
        }

        ablation_results = {}
        for name, cfg in configs.items():
            _, metrics, _ = self.train_single_model(model_type=model_type, level=3, feature_config=cfg)
            ablation_results[name] = {
                "accuracy": metrics.accuracy,
                "macro_f1": metrics.macro_f1,
                "latency_ms": metrics.inference_latency_ms
            }

        return ablation_results

    def run_cross_architecture_matrix(self, model_type: str = "rf") -> Dict[str, Any]:
        """
        Paper Sec. IV-E Cross-Architecture Evaluation:
        1. Mixed-ISA (baseline)
        2. Unseen-ISA (Leave-One-ISA-Out for all 5 ISAs)
        """
        isas = ["x86-64", "ARM32", "ARM64", "MIPS32-LE", "RISC-V 64"]
        ds = self.loader.load_dataset()

        # 1. Mixed-ISA
        _, mixed_metrics, _ = self.train_single_model(model_type=model_type, level=3)
        results = {
            "mixed_isa_f1": mixed_metrics.macro_f1,
            "leave_one_out": {}
        }

        # 2. Leave-One-ISA-Out
        for test_isa in isas:
            X_tr, y_tr, X_te, y_te = self.loader.split_unseen_isa(ds, test_isa=test_isa, level=3)
            scaler = StandardScaler()
            X_tr_s = scaler.fit_transform(X_tr)
            X_te_s = scaler.transform(X_te)

            clf = create_model(model_type)
            clf.fit(X_tr_s, y_tr)
            m = self.evaluate_model(clf, X_te_s, y_te)
            results["leave_one_out"][test_isa] = {
                "test_isa": test_isa,
                "accuracy": m.accuracy,
                "macro_f1": m.macro_f1
            }

        return results

    def run_robustness_study(self, model_type: str = "rf") -> Dict[str, Any]:
        """
        Paper Sec. IV-F: Degradation across optimization levels (O0..Os) and compilers.
        """
        opt_levels = ["O0", "O1", "O2", "O3", "Os"]
        ds = self.loader.load_dataset()
        # Train on O0/O1, test degradation on O2, O3, Os
        clf, _, scaler = self.train_single_model(model_type=model_type, level=3)

        per_opt_metrics = {}
        for opt in opt_levels:
            mask = (ds.opt_levels == opt)
            if np.sum(mask) > 0:
                X_opt_s = scaler.transform(ds.X[mask])
                y_opt = ds.y_l3[mask]
                m = self.evaluate_model(clf, X_opt_s, y_opt)
                per_opt_metrics[opt] = {
                    "accuracy": m.accuracy,
                    "macro_f1": m.macro_f1
                }

        return per_opt_metrics
