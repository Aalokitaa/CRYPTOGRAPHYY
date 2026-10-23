"""
CryptoScope Phase 6 API Test Suite
Tests FastAPI endpoints:
- Health probe
- Toolchain status
- Datasets listing
- Upload and analyze binary
- Job status polling
- Analysis details
- Report export (JSON, HTML, PDF)
- Paper evaluation endpoints (ablation, cross-arch, robustness)
"""

import os
import json
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal, init_db
from backend.app.datasets.builder import DatasetBuilder
from backend.app.datasets.manifest import TargetISA, OptLevel

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

def test_toolchain_status_endpoint():
    res = client.get("/api/toolchain/status")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert "ready_isas" in data
    assert "missing_isas" in data
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) >= 5

def test_datasets_listing_endpoint():
    res = client.get("/api/datasets")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert len(data["datasets"]) > 0
    first = data["datasets"][0]
    assert "version" in first
    assert "total_functions" in first

def test_binary_analysis_and_report_pipeline():
    # 1. Create a tiny test binary using DatasetBuilder
    builder = DatasetBuilder()
    manifest = builder.build_synthetic_multi_isa_binary(TargetISA.X86_64, "gcc", OptLevel.O2)
    binary_path = Path(manifest.stripped_path)
    assert binary_path.exists()

    # 2. Upload to /api/analyze
    with open(binary_path, "rb") as f:
        res = client.post(
            "/api/analyze",
            files={"file": (binary_path.name, f, "application/octet-stream")},
            data={"model_choice": "rf", "backend": "builtin", "confidence_threshold": 0.5}
        )
    assert res.status_code == 200
    job_info = res.json()
    job_id = job_info["job_id"]
    assert job_id is not None

    # 3. Poll job status until completed
    max_retries = 30
    analysis_id = None
    for _ in range(max_retries):
        status_res = client.get(f"/api/jobs/{job_id}")
        assert status_res.status_code == 200
        job_data = status_res.json()
        if job_data["status"] == "completed":
            analysis_id = job_data["result_id"]
            break
        elif job_data["status"] == "failed":
            pytest.fail(f"Job failed: {job_data.get('error')}")
        time.sleep(0.5)

    assert analysis_id is not None, "Analysis job did not complete in time"

    # 4. Check /api/analyses/{id}
    analysis_res = client.get(f"/api/analyses/{analysis_id}")
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()
    assert analysis_data["filename"] == binary_path.name
    assert "isa" in analysis_data
    assert "functions" in analysis_data
    assert len(analysis_data["functions"]) > 0

    # 5. Export Report in JSON format
    rep_json = client.post(f"/api/reports/{analysis_id}?format=json")
    assert rep_json.status_code == 200
    assert rep_json.json()["id"] == analysis_id

    # 6. Export Report in HTML format
    rep_html = client.post(f"/api/reports/{analysis_id}?format=html")
    assert rep_html.status_code == 200
    assert "CryptoScope Security Audit Report" in rep_html.text

    # 7. Export Report in PDF format
    rep_pdf = client.post(f"/api/reports/{analysis_id}?format=pdf")
    assert rep_pdf.status_code == 200
    assert rep_pdf.headers["content-type"] == "application/pdf"
    assert len(rep_pdf.content) > 1000

def test_paper_evaluation_endpoints():
    # Test ablation endpoint
    res_abl = client.get("/api/ablation")
    assert res_abl.status_code == 200
    abl_data = res_abl.json()
    assert "All features" in abl_data or "Byte only" in abl_data

    # Test robustness endpoint
    res_rob = client.get("/api/robustness")
    assert res_rob.status_code == 200
    rob_data = res_rob.json()
    assert "O0" in rob_data or "O2" in rob_data
