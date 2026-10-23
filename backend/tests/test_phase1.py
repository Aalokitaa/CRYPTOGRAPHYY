"""
Unit and Integration Tests for Phase 1: Dataset Generation Module
Tests:
- Toolchain probing and degradation
- Source code provenance integrity
- ELF synthesis and parsing with LIEF
- Ground-truth labeling across 3 levels
- Inlining detection
- Manifest structure and distributions
"""

import json
from pathlib import Path
import pytest
import lief

from backend.app.datasets.manifest import (
    CryptoFamily, CryptoPrimitive, TargetISA, OptLevel, DatasetManifest
)
from backend.app.datasets.toolchain import get_toolchain_status
from backend.app.datasets.builder import DatasetBuilder, SYMBOL_GROUND_TRUTH

def test_toolchain_status():
    status = get_toolchain_status()
    assert status is not None
    assert isinstance(status.ready_isas, list)
    assert isinstance(status.missing_isas, list)
    assert len(status.tools) == 6
    for t in status.tools:
        assert t.target_isa in [
            "x86-64", "ARM64", "ARM32", "MIPS32-BE", "MIPS32-LE", "RISC-V 64"
        ]
        assert "debian" in t.install_command

def test_source_license_provenance():
    base_dir = Path(__file__).resolve().parent.parent.parent
    prov_file = base_dir / "datasets" / "sources" / "LICENSE_PROVENANCE.json"
    assert prov_file.exists(), "LICENSE_PROVENANCE.json must exist"

    with open(prov_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "entries" in data
    assert len(data["entries"]) >= 20

    for entry in data["entries"]:
        assert "file" in entry
        assert "license" in entry
        assert "algorithm" in entry
        src_path = base_dir / entry["file"]
        assert src_path.exists(), f"Source file {src_path} declared in provenance must exist"

def test_synthetic_binary_generation_and_lief_parsing(tmp_path):
    builder = DatasetBuilder(base_dir=str(tmp_path))
    
    # Test building an ARM64 binary at O2
    manifest = builder.build_synthetic_multi_isa_binary(
        isa=TargetISA.ARM64,
        compiler="gcc",
        opt=OptLevel.O2
    )

    assert manifest.isa == TargetISA.ARM64
    assert manifest.opt_level == OptLevel.O2
    assert Path(manifest.stripped_path).exists()
    assert Path(manifest.original_path).exists()
    assert len(manifest.functions) > 0

    # Parse with LIEF
    elf = lief.parse(manifest.stripped_path)
    assert elf is not None
    assert elf.header.machine_type == lief.ELF.ARCH.AARCH64

def test_inlining_tracking(tmp_path):
    builder = DatasetBuilder(base_dir=str(tmp_path))
    
    # At O3, inlining is simulated and recorded
    manifest = builder.build_synthetic_multi_isa_binary(
        isa=TargetISA.X86_64,
        compiler="clang",
        opt=OptLevel.O3
    )

    inlined_fns = [fn for fn in manifest.functions if fn.is_inlined]
    assert len(inlined_fns) > 0, "O3 must have detected inlined functions"
    for fn in inlined_fns:
        assert fn.size == 0
        assert fn.address == 0
        assert fn.name in manifest.inlined_functions

def test_dataset_manifest_integrity():
    base_dir = Path(__file__).resolve().parent.parent.parent
    latest_manifest = base_dir / "datasets" / "manifests" / "latest.json"
    assert latest_manifest.exists(), "latest.json manifest must exist after dataset build"

    with open(latest_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = DatasetManifest(**data)
    assert manifest.total_binaries == 50
    assert manifest.total_functions > 1000

    # Ensure all target ISAs are represented
    expected_isas = {"x86-64", "ARM32", "ARM64", "MIPS32-LE", "RISC-V 64"}
    assert set(manifest.isa_distribution.keys()) == expected_isas

    # Ensure all 8 crypto primitives + non-crypto are represented
    expected_primitives = {
        "AES", "DES/3DES", "RSA", "ECC", "SHA-256", "SHA-512", "HMAC", "ChaCha20", "Non-crypto"
    }
    assert set(manifest.class_distribution.keys()) == expected_primitives
