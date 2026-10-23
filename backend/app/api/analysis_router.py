"""
CryptoScope Binary Analysis API Router
Endpoints:
- POST /api/analyze (upload firmware, options) -> job id
- GET /api/jobs/{id}
- WS /api/jobs/{id}/stream
- GET /api/analyses
- GET /api/analyses/{id}
- GET /api/functions/{id}/disasm
- GET /api/functions/{id}/cfg
- GET /api/functions/{id}/dfg
- GET /api/functions/{id}/explain
"""

import os
import uuid
import json
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db, SessionLocal
from backend.app.core.models import JobModel, AnalysisModel
from backend.app.core.job_manager import job_manager
from backend.app.analysis.engine import BinaryAnalysisPipeline
from backend.app.features.extractor import FeatureExtractor, FeatureConfig
from backend.app.features.crypto_constants import CryptoConstantScanner
from backend.app.training.trainer import ModelTrainer
from backend.app.protocol.graph import ProtocolGraphBuilder
from backend.app.protocol.patterns import ProtocolPatternMatcher
from backend.app.protocol.advisories import SecurityAdvisoryEngine
from backend.app.models.explainer import ModelExplainer

router = APIRouter(tags=["Analysis"])

# In-memory analysis cache for fast drill-downs
ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}

async def run_analysis_task(job_id: str, 
                            file_path: Path, 
                            filename: str,
                            model_choice: str = "rf",
                            backend_type: str = "builtin",
                            confidence_threshold: float = 0.5):
    try:
        # Step 1: Detect architecture & format
        await job_manager.update_job(job_id, 10, "Detecting Architecture", "Probing ELF/PE headers and trial disassembly heuristics...")
        pipeline = BinaryAnalysisPipeline(backend_type=backend_type)
        detection, functions, callgraph, cfgs, dfgs = pipeline.analyze_binary(file_path)

        await job_manager.update_job(
            job_id, 25, "Function Recovery", 
            f"Detected {detection.format} ({detection.isa.value}, {detection.endianness}). Recovered {len(functions)} functions."
        )

        # Step 2: Build Control & Data Flow Graphs
        await job_manager.update_job(job_id, 40, "Graph Construction", "Constructing basic block CFGs and def-use DFGs...")
        await asyncio.sleep(0.1) # Yield to event loop

        # Step 3: Feature Extraction
        await job_manager.update_job(job_id, 55, "Feature Extraction", "Extracting byte, instruction, CFG, and DFG feature vectors...")
        extractor = FeatureExtractor(config=FeatureConfig(enable_byte=True, enable_instruction=True, enable_cfg=True, enable_dfg=True))
        constant_scanner = CryptoConstantScanner()

        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        file_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        # Step 4: Hierarchical Classification
        await job_manager.update_job(job_id, 70, "Hierarchical Classification", "Routing functions through 3-level hierarchical classifier...")
        trainer = ModelTrainer()
        # Train or load model
        try:
            hierarchical_run = trainer.train_full_hierarchical(model_type=model_choice, save_run=False)
            model_path = hierarchical_run["model_path"]
            import joblib
            model = joblib.load(model_path)
        except Exception as e:
            # Fallback to single tree model if needed
            model = None

        function_records = []
        fn_meta_dict = {}
        predictions_map = {}
        primitive_counts: Dict[str, int] = {}

        for fn in functions:
            fn_bytes = b"".join(insn.bytes for insn in fn.instructions)
            cfg = cfgs.get(fn.entry_addr)
            dfg = dfgs.get(fn.entry_addr)

            vec, names, feat_dict = extractor.extract_features(fn, cfg, dfg)
            constants = constant_scanner.scan(fn_bytes)
            constant_names = [c.constant_name for c in constants]

            # Model prediction
            if model is not None:
                pred = model.predict(vec)
            else:
                # Baseline constant fallback
                prim_base, conf_base, _ = constant_scanner.classify_baseline(fn_bytes)
                from backend.app.models.hierarchical import HierarchicalPrediction
                pred = HierarchicalPrediction(
                    is_crypto=(prim_base.value != "Non-crypto"),
                    l1_confidence=conf_base,
                    family="Symmetric Cipher" if "AES" in prim_base.value else "Non-crypto",
                    l2_confidence=conf_base,
                    primitive=prim_base.value,
                    l3_confidence=conf_base,
                    overall_confidence=conf_base,
                    routing_path=["Baseline Signature Match"]
                )

            predictions_map[fn.entry_addr] = pred
            fn_meta_dict[fn.entry_addr] = {
                "name": f"fn_{hex(fn.entry_addr)}",
                "size": fn.size,
                "insn_count": len(fn.instructions)
            }

            primitive_counts[pred.primitive] = primitive_counts.get(pred.primitive, 0) + 1

            fn_rec = {
                "id": fn.id,
                "address": fn.entry_addr,
                "hex_address": hex(fn.entry_addr),
                "size": fn.size,
                "insn_count": len(fn.instructions),
                "is_crypto": pred.is_crypto,
                "family": pred.family,
                "primitive": pred.primitive,
                "confidence": pred.overall_confidence,
                "is_low_confidence": pred.is_low_confidence,
                "constants_hit": constant_names,
                "features": feat_dict,
                "routing_path": pred.routing_path
            }
            function_records.append(fn_rec)

        # Step 5: Protocol Graph & Security Findings
        await job_manager.update_job(job_id, 85, "Protocol & Security Synthesis", "Synthesizing protocol graph and evaluating security advisories...")
        proto_builder = ProtocolGraphBuilder()
        proto_matcher = ProtocolPatternMatcher()
        adv_engine = SecurityAdvisoryEngine()

        proto_graph = proto_builder.build_protocol_graph(predictions_map, callgraph, fn_meta_dict)
        patterns = proto_matcher.match_patterns(proto_graph)
        advisories = adv_engine.generate_advisories(proto_graph)

        # Step 6: Complete & Persist
        analysis_id = str(uuid.uuid4())
        summary_data = {
            "id": analysis_id,
            "analysis_id": analysis_id,
            "filename": filename,
            "file_size": len(raw_bytes),
            "sha256": file_sha256,
            "format": detection.format,
            "isa": detection.isa.value,
            "endianness": detection.endianness,
            "bits": detection.bits,
            "entrypoint": hex(detection.entrypoint),
            "confidence": detection.confidence,
            "total_functions": len(functions),
            "primitive_counts": primitive_counts,
            "advisory_count": len(advisories),
            "pattern_count": len(patterns)
        }

        full_analysis_data = {
            **summary_data,
            "executable_sections": detection.executable_regions,
            "functions": function_records,
            "protocol_graph": proto_graph.model_dump(),
            "patterns": [p.model_dump() for p in patterns],
            "advisories": [a.model_dump() for a in advisories],
            "call_graph": callgraph.to_dict()
        }

        # Cache in memory
        ANALYSIS_CACHE[analysis_id] = {
            "full_data": full_analysis_data,
            "cfgs": {fn.id: cfgs[fn.entry_addr] for fn in functions if fn.entry_addr in cfgs},
            "dfgs": {fn.id: dfgs[fn.entry_addr] for fn in functions if fn.entry_addr in dfgs},
            "functions": {fn.id: fn for fn in functions}
        }

        # Save to SQLite
        db = SessionLocal()
        try:
            record = AnalysisModel(
                id=analysis_id,
                filename=filename,
                file_size=len(raw_bytes),
                sha256=file_sha256,
                format=detection.format,
                isa=detection.isa.value,
                endianness=detection.endianness,
                bits=detection.bits,
                entrypoint=hex(detection.entrypoint),
                confidence=detection.confidence,
                summary_json=json.dumps(summary_data),
                full_data_json=json.dumps(full_analysis_data)
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        await job_manager.update_job(
            job_id, 100, "Completed", "Analysis finished successfully.",
            status="completed", result_id=analysis_id
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        await job_manager.update_job(
            job_id, 100, "Failed", f"Error during analysis: {str(e)}",
            status="failed", error=str(e)
        )

@router.post("/analyze")
async def analyze_firmware(background_tasks: BackgroundTasks,
                           file: UploadFile = File(...),
                           model_choice: str = Form("rf"),
                           backend: str = Form("builtin"),
                           confidence_threshold: float = Form(0.5)):
    # Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size (100MB)")

    job_id = str(uuid.uuid4())
    upload_path = settings.UPLOAD_DIR / f"{job_id}_{file.filename}"
    with open(upload_path, "wb") as f:
        f.write(file_bytes)

    job_manager.create_job(job_id, "analysis", "Analysis Queued")

    background_tasks.add_task(
        run_analysis_task,
        job_id=job_id,
        file_path=upload_path,
        filename=file.filename,
        model_choice=model_choice,
        backend_type=backend,
        confidence_threshold=confidence_threshold
    )

    return {"job_id": job_id, "status": "running", "filename": file.filename}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "step": job.step,
        "message": job.message,
        "logs": json.loads(job.logs_json) if job.logs_json else [],
        "result_id": job.result_id,
        "error": job.error
    }

@router.websocket("/jobs/{job_id}/stream")
async def websocket_job_stream(websocket: WebSocket, job_id: str):
    await job_manager.register_websocket(job_id, websocket)
    try:
        while True:
            # Keep socket open and respond to pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        job_manager.unregister_websocket(job_id, websocket)

@router.get("/analyses")
async def list_analyses(db: Session = Depends(get_db)):
    records = db.query(AnalysisModel).order_by(AnalysisModel.created_at.desc()).all()
    results = []
    for r in records:
        summary = json.loads(r.summary_json)
        results.append(summary)
    return results

@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    if analysis_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[analysis_id]["full_data"]

    record = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found")

    return json.loads(record.full_data_json)

@router.get("/functions/{fn_id}/disasm")
async def get_function_disassembly(fn_id: str):
    for a_id, data in ANALYSIS_CACHE.items():
        if fn_id in data.get("functions", {}):
            fn = data["functions"][fn_id]
            lines = []
            for insn in fn.instructions:
                lines.append({
                    "address": hex(insn.address),
                    "mnemonic": insn.mnemonic,
                    "op_str": insn.op_str,
                    "bytes": insn.hex_bytes
                })
            return {"function_id": fn_id, "instructions": lines}
    raise HTTPException(status_code=404, detail="Function not found in active analysis cache")

@router.get("/functions/{fn_id}/cfg")
async def get_function_cfg(fn_id: str):
    for a_id, data in ANALYSIS_CACHE.items():
        if fn_id in data.get("cfgs", {}):
            return data["cfgs"][fn_id].to_dict()
    raise HTTPException(status_code=404, detail="CFG not found for function")

@router.get("/functions/{fn_id}/dfg")
async def get_function_dfg(fn_id: str):
    for a_id, data in ANALYSIS_CACHE.items():
        if fn_id in data.get("dfgs", {}):
            return data["dfgs"][fn_id].to_dict()
    raise HTTPException(status_code=404, detail="DFG not found for function")

@router.get("/functions/{fn_id}/explain")
async def get_function_explanation(fn_id: str):
    for a_id, data in ANALYSIS_CACHE.items():
        full = data["full_data"]
        for fn_rec in full.get("functions", []):
            if fn_rec["id"] == fn_id:
                feats = fn_rec.get("features", {})
                vec = np.array(list(feats.values()), dtype=np.float32)
                explainer = ModelExplainer(None, list(feats.keys()))
                exp = explainer.explain_instance(
                    vec, fn_rec["primitive"], fn_rec["confidence"], constants_found=fn_rec.get("constants_hit", [])
                )
                return exp.model_dump()
    raise HTTPException(status_code=404, detail="Function explanation not found")
