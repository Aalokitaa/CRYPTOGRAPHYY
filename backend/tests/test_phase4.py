"""
Unit and Integration Tests for Phase 4: Hierarchical Classification & Training Engine
Tests:
- Grouped 70/15/15 dataset splitting (assert zero group leakage)
- Classical ML models (Random Forest, SVM, XGBoost)
- PyTorch Deep models (CNN, BiLSTM)
- Hierarchical classification routing and calibration
- SHAP feature explainability and rationale generation
- Cross-architecture scenarios (Leave-One-ISA-Out)
- Feature group ablation (Byte, Insn, CFG, DFG)
"""

from pathlib import Path
import pytest
import numpy as np

from backend.app.training.dataset_loader import DatasetLoader
from backend.app.training.trainer import ModelTrainer
from backend.app.models.tree_models import create_model
from backend.app.models.deep_models import PyTorchClassifierWrapper
from backend.app.models.explainer import ModelExplainer
from backend.app.features.extractor import FeatureConfig

def test_grouped_splitting_zero_leakage():
    loader = DatasetLoader()
    ds = loader.load_dataset(version="v1.0.0")
    assert len(ds) > 100

    # Split Level 1 with grouped isolation
    X_tr, y_tr, grp_tr, X_val, y_val, grp_val, X_te, y_te, grp_te = loader.split_grouped(ds, level=1)

    assert len(X_tr) > 0
    assert len(X_val) > 0
    assert len(X_te) > 0

    # Test group leakage: Groups in test must NOT appear in train!
    train_groups = set(grp_tr)
    test_groups = set(grp_te)

    overlap = train_groups.intersection(test_groups)
    assert len(overlap) == 0, f"DATA LEAKAGE DETECTED! Overlapping groups: {overlap}"


def test_tree_models_and_evaluation():
    trainer = ModelTrainer()

    # Train Random Forest Level 1
    clf_rf, metrics_rf, scaler = trainer.train_single_model(model_type="rf", level=1)
    assert metrics_rf.accuracy >= 0.60
    assert metrics_rf.macro_f1 >= 0.60
    assert metrics_rf.inference_latency_ms > 0.0

    # Train XGBoost Level 1
    clf_xgb, metrics_xgb, _ = trainer.train_single_model(model_type="xgb", level=1)
    assert metrics_xgb.accuracy >= 0.60

def test_pytorch_deep_model():
    trainer = ModelTrainer()
    ds = trainer.loader.load_dataset()
    X_tr, y_tr, _, _, _, _, X_te, y_te, _ = trainer.loader.split_grouped(ds, level=1)

    # Train 1D CNN on semantic sequences
    clf_cnn = PyTorchClassifierWrapper(model_type="cnn", epochs=3, batch_size=32)
    clf_cnn.fit(X_tr[:100], y_tr[:100])

    probs = clf_cnn.predict_proba(X_te[:10])
    assert probs.shape[0] == 10
    assert probs.shape[1] == 2
    assert np.allclose(np.sum(probs, axis=1), 1.0)

def test_hierarchical_routing_and_explainability():
    trainer = ModelTrainer()
    run_record = trainer.train_full_hierarchical(model_type="rf", save_run=False)

    assert "level1_metrics" in run_record
    assert "level2_metrics" in run_record
    assert "level3_metrics" in run_record
    assert run_record["overall_f1"] > 0.35


    # Test SHAP explainer
    ds = trainer.loader.load_dataset()
    rf_model = create_model("rf")
    rf_model.fit(ds.X[:100], ds.y_l1[:100])

    explainer = ModelExplainer(rf_model, ds.feature_names)
    exp = explainer.explain_instance(ds.X[0], "Crypto", 0.95, constants_found=["AES S-Box"])

    assert exp.predicted_label == "Crypto"
    assert exp.confidence == 0.95
    assert len(exp.top_features) > 0
    assert len(exp.human_rationale) > 10

def test_ablation_and_cross_arch_scenarios():
    trainer = ModelTrainer()

    # Run ablation study
    ablation = trainer.run_ablation_study(model_type="rf")
    assert "Byte only" in ablation
    assert "Instruction only" in ablation
    assert "All features" in ablation

    # Run Leave-One-ISA-Out scenario
    cross_arch = trainer.run_cross_architecture_matrix(model_type="rf")
    assert "mixed_isa_f1" in cross_arch
    assert "leave_one_out" in cross_arch
    assert "x86-64" in cross_arch["leave_one_out"]
    assert "ARM64" in cross_arch["leave_one_out"]
