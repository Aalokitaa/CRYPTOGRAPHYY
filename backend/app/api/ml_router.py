"""
CryptoScope ML & Training API Router
Endpoints:
- GET  /api/toolchain/status
- GET  /api/datasets
- POST /api/datasets/build
- POST /api/train
- GET  /api/runs
- GET  /api/runs/{id}
- GET  /api/compare?runs=...
- GET  /api/ablation
- GET  /api/cross-arch
- GET  /api/robustness
"""

import os
import glob
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db, SessionLocal
from backend.app.core.models import JobModel, RunModel
from backend.app.core.job_manager import job_manager
from backend.app.datasets.toolchain import get_toolchain_status
from backend.app.datasets.builder import DatasetBuilder
from backend.app.training.trainer import ModelTrainer
from backend.app.features.extractor import FeatureConfig

router = APIRouter(tags=["ML & Training"])

# Caches for heavy paper experiments
EXPERIMENT_CACHE_DIR = settings.BASE_DIR / "backend" / "app" / "models" / "experiments"
EXPERIMENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class DatasetBuildRequest(BaseModel):
    version: str = Field(default="v1.0.0", description="Dataset manifest version identifier")

class TrainRequest(BaseModel):
    model_type: str = Field(default="rf", description="rf, svm, xgb, cnn, lstm, transformer")
    level: int = Field(default=0, description="0 for full hierarchical (L1+L2+L3), or 1, 2, 3 for single level")
    dataset_version: str = Field(default="v1.0.0", description="Dataset manifest version to train on")
    enable_byte: bool = True
    enable_instruction: bool = True
    enable_cfg: bool = True
    enable_dfg: bool = True
    use_semantic_tokens: bool = True

async def run_dataset_build_task(job_id: str, version: str):
    try:
        await job_manager.update_job(job_id, 10, "Initializing Matrix", f"Preparing toolchain and target ISA matrix for {version}...")
        builder = DatasetBuilder()
        
        await job_manager.update_job(job_id, 30, "Compiling Multi-ISA Corpus", "Generating benchmark functions across x86-64, ARM32, ARM64, MIPS, and RISC-V...")
        manifest = builder.build_full_dataset(version=version)
        
        await job_manager.update_job(job_id, 85, "Extracting Ground-Truth Labels", f"Synthesized {len(manifest.binaries)} binaries with {manifest.total_functions} ground-truth functions.")
        
        await job_manager.complete_job(job_id, result_id=manifest.version, message=f"Dataset {manifest.version} built successfully ({manifest.total_functions} functions).")
    except Exception as e:
        await job_manager.fail_job(job_id, str(e))

async def run_training_task(job_id: str, req: TrainRequest):
    try:
        await job_manager.update_job(job_id, 10, "Loading Dataset", f"Loading dataset version {req.dataset_version} with zero-leakage grouped splitting...")
        trainer = ModelTrainer()
        feat_config = FeatureConfig(
            enable_byte=req.enable_byte,
            enable_instruction=req.enable_instruction,
            enable_cfg=req.enable_cfg,
            enable_dfg=req.enable_dfg,
            use_semantic_tokens=req.use_semantic_tokens
        )

        if req.level == 0:
            # Full hierarchical training
            await job_manager.update_job(job_id, 25, "Training Level 1", "Fitting Level 1 binary classifier (Crypto vs Non-Crypto)...")
            run_rec = trainer.train_hierarchical_pipeline(
                model_type=req.model_type,
                dataset_version=req.dataset_version,
                feature_config=feat_config
            )
            await job_manager.update_job(job_id, 75, "Calibrating Level 2 & 3", "Fitting Level 2 (Family) and Level 3 (Primitive) with confidence routing...")
        else:
            await job_manager.update_job(job_id, 40, f"Training Level {req.level}", f"Fitting {req.model_type} classifier on Level {req.level}...")
            _, metrics, _ = trainer.train_single_model(
                model_type=req.model_type,
                level=req.level,
                dataset_version=req.dataset_version,
                feature_config=feat_config
            )
            run_rec = {
                "run_id": f"run_{uuid.uuid4().hex[:8]}",
                "model_type": req.model_type,
                "dataset_version": req.dataset_version,
                "overall_f1": metrics.macro_f1,
                "model_path": "",
                f"level{req.level}_metrics": metrics.to_dict()
            }

        # Save to database
        db = SessionLocal()
        try:
            run_model = RunModel(
                id=run_rec["run_id"],
                model_type=req.model_type,
                dataset_version=req.dataset_version,
                overall_f1=float(run_rec.get("overall_f1", 0.0)),
                metrics_json=json.dumps(run_rec),
                config_json=json.dumps(req.model_dump()),
                model_path=run_rec.get("model_path", "")
            )
            db.add(run_model)
            db.commit()
        finally:
            db.close()

        await job_manager.complete_job(
            job_id, 
            result_id=run_rec["run_id"], 
            message=f"Training complete. Overall Macro F1: {run_rec.get('overall_f1', 0.0):.4f}"
        )
    except Exception as e:
        await job_manager.fail_job(job_id, str(e))

@router.get("/toolchain/status")
def toolchain_status():
    """
    Probes host compilers, cross-compilers, and Docker daemon.
    Returns status and copy-paste install commands for missing toolchains.
    """
    status = get_toolchain_status()
    return status.model_dump()

@router.get("/datasets")
def list_datasets():
    """
    Lists all available dataset manifests, their version, total functions, and class distributions.
    """
    manifest_dir = settings.BASE_DIR / "datasets" / "manifests"
    manifest_files = glob.glob(str(manifest_dir / "dataset_*.json"))
    
    datasets = []
    for mf in sorted(manifest_files, reverse=True):
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
                datasets.append({
                    "version": data.get("version"),
                    "created_at": data.get("created_at"),
                    "binaries_count": len(data.get("binaries", [])),
                    "total_functions": data.get("total_functions", 0),
                    "class_distribution": data.get("class_distribution", {}),
                    "isa_distribution": data.get("isa_distribution", {}),
                    "manifest_path": mf
                })
        except Exception:
            continue
    return {"datasets": datasets}

@router.post("/datasets/build")
async def build_dataset(req: DatasetBuildRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers dataset generation across the 5 ISAs, 2 compilers, and 5 optimization levels.
    """
    job_id = f"job_ds_{uuid.uuid4().hex[:8]}"
    db_job = JobModel(
        id=job_id,
        job_type="dataset_build",
        status="pending",
        progress=0,
        step="Queued",
        message="Queued dataset build job"
    )
    db.add(db_job)
    db.commit()

    background_tasks.add_task(run_dataset_build_task, job_id, req.version)
    return {"job_id": job_id, "status": "queued"}

@router.post("/train")
async def train_model(req: TrainRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers model training (hierarchical or single level) on a versioned dataset.
    """
    job_id = f"job_train_{uuid.uuid4().hex[:8]}"
    db_job = JobModel(
        id=job_id,
        job_type="training",
        status="pending",
        progress=0,
        step="Queued",
        message=f"Queued training job for {req.model_type}"
    )
    db.add(db_job)
    db.commit()

    background_tasks.add_task(run_training_task, job_id, req)
    return {"job_id": job_id, "status": "queued"}

@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    """
    Lists all saved training runs and their macro F1 scores.
    """
    runs = db.query(RunModel).order_by(RunModel.created_at.desc()).all()
    out = []
    for r in runs:
        out.append({
            "id": r.id,
            "model_type": r.model_type,
            "dataset_version": r.dataset_version,
            "overall_f1": r.overall_f1,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "config": json.loads(r.config_json) if r.config_json else {}
        })
    return {"runs": out}

@router.get("/runs/{id}")
def get_run_detail(id: str, db: Session = Depends(get_db)):
    """
    Retrieves full metrics, per-class F1, confusion matrices, and ROC-AUC for a specific run.
    """
    run = db.query(RunModel).filter(RunModel.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{id}' not found.")
    
    return {
        "id": run.id,
        "model_type": run.model_type,
        "dataset_version": run.dataset_version,
        "overall_f1": run.overall_f1,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "metrics": json.loads(run.metrics_json),
        "config": json.loads(run.config_json) if run.config_json else {}
    }

@router.get("/compare")
def compare_runs(runs: str = Query(..., description="Comma-separated run IDs to compare"), db: Session = Depends(get_db)):
    """
    Compares performance metrics across multiple models or training runs.
    """
    run_ids = [r.strip() for r in runs.split(",") if r.strip()]
    if not run_ids:
        raise HTTPException(status_code=400, detail="No run IDs provided.")
    
    records = db.query(RunModel).filter(RunModel.id.in_(run_ids)).all()
    comparison = []
    for r in records:
        metrics_dict = json.loads(r.metrics_json)
        comparison.append({
            "id": r.id,
            "model_type": r.model_type,
            "overall_f1": r.overall_f1,
            "level1": metrics_dict.get("level1_metrics", {}),
            "level2": metrics_dict.get("level2_metrics", {}),
            "level3": metrics_dict.get("level3_metrics", {}),
        })
    return {"comparison": comparison}

@router.get("/ablation")
def get_ablation_results(refresh: bool = False, model_type: str = "rf"):
    """
    Paper Table VI: Feature Ablation Study.
    Compares 5 feature subsets: Byte only, Instruction only, Instruction+CFG, Instruction+DFG, All.
    """
    cache_file = EXPERIMENT_CACHE_DIR / f"ablation_{model_type}.json"
    if not refresh and cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    trainer = ModelTrainer()
    results = trainer.run_ablation_study(model_type=model_type)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results

@router.get("/cross-arch")
def get_cross_arch_results(refresh: bool = False, model_type: str = "rf"):
    """
    Paper Sec. IV-E: Cross-Architecture Generalization.
    Computes Mixed-ISA baseline and Leave-One-ISA-Out (unseen-ISA) metrics across all 5 architectures.
    """
    cache_file = EXPERIMENT_CACHE_DIR / f"cross_arch_{model_type}.json"
    if not refresh and cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    trainer = ModelTrainer()
    results = trainer.run_cross_architecture_matrix(model_type=model_type)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results

@router.get("/robustness")
def get_robustness_results(refresh: bool = False, model_type: str = "rf"):
    """
    Paper Sec. IV-F: Optimization Level Degradation Curves (O0, O1, O2, O3, Os).
    """
    cache_file = EXPERIMENT_CACHE_DIR / f"robustness_{model_type}.json"
    if not refresh and cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    trainer = ModelTrainer()
    results = trainer.run_robustness_study(model_type=model_type)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results
