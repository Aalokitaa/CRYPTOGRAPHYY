"""
Unit and Integration Tests for Phase 3: Feature Extraction
Tests:
- Semantic instruction normalization across ISAs
- Cryptographic constant scanner and baseline classifier
- Byte-level feature extraction & Shannon entropy
- Instruction-level feature extraction & ratio calculations
- CFG & DFG feature extraction
- Group ablation toggles (Byte only, Insn only, Insn+CFG, etc.)
"""

from pathlib import Path
import pytest
import numpy as np

from backend.app.datasets.manifest import CryptoPrimitive
from backend.app.features.semantic_isa import (
    SemanticInsnClass, map_mnemonic_to_semantic
)
from backend.app.features.crypto_constants import CryptoConstantScanner
from backend.app.features.extractor import FeatureExtractor, FeatureConfig
from backend.app.analysis.engine import BinaryAnalysisPipeline

def test_semantic_instruction_mapping():
    # x86-64
    assert map_mnemonic_to_semantic("add") == SemanticInsnClass.ADD
    assert map_mnemonic_to_semantic("paddd") == SemanticInsnClass.ADD
    assert map_mnemonic_to_semantic("pxor") == SemanticInsnClass.AND_OR_XOR
    assert map_mnemonic_to_semantic("shl") == SemanticInsnClass.SHL_SHR_ROT
    assert map_mnemonic_to_semantic("ret") == SemanticInsnClass.RET
    # ARM32 / ARM64
    assert map_mnemonic_to_semantic("eor") == SemanticInsnClass.AND_OR_XOR
    assert map_mnemonic_to_semantic("ldr") == SemanticInsnClass.LOAD
    assert map_mnemonic_to_semantic("stp") == SemanticInsnClass.STORE
    assert map_mnemonic_to_semantic("b.eq") == SemanticInsnClass.BRANCH_COND
    # MIPS / RISC-V
    assert map_mnemonic_to_semantic("addiu") == SemanticInsnClass.ADD
    assert map_mnemonic_to_semantic("jal") == SemanticInsnClass.CALL
    assert map_mnemonic_to_semantic("slli") == SemanticInsnClass.SHL_SHR_ROT

def test_crypto_constant_scanner():
    scanner = CryptoConstantScanner()

    # Synthetic buffer with AES S-box and ChaCha20 constant
    buf = bytearray(b"\x90" * 32)
    buf += bytes([
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
        0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76
    ])
    buf += b"\x90" * 16
    buf += b"expand 32-byte k"

    matches = scanner.scan(bytes(buf))
    assert len(matches) >= 2
    prims = [m.primitive for m in matches]
    assert CryptoPrimitive.AES in prims
    assert CryptoPrimitive.CHACHA20 in prims

    # Baseline classification
    prim, conf, m_list = scanner.classify_baseline(bytes(buf))
    assert conf > 0.5
    assert prim in [CryptoPrimitive.AES, CryptoPrimitive.CHACHA20]

def test_feature_extraction_and_ablation():
    base_dir = Path(__file__).resolve().parent.parent.parent
    x86_bin = base_dir / "datasets" / "binaries" / "stripped" / "bin_x86_64_gcc_o0_stripped.elf"
    assert x86_bin.exists()

    pipeline = BinaryAnalysisPipeline()
    _, functions, _, cfgs, dfgs = pipeline.analyze_binary(x86_bin)
    assert len(functions) > 0
    fn0 = functions[0]

    # 1. Full Features (All 4 groups)
    cfg_all = FeatureConfig(enable_byte=True, enable_instruction=True, enable_cfg=True, enable_dfg=True)
    ext_all = FeatureExtractor(config=cfg_all)
    vec_all, names_all, dict_all = ext_all.extract_features(fn0, cfgs[fn0.entry_addr], dfgs[fn0.entry_addr])

    assert len(vec_all) > 30
    assert "entropy_overall" in dict_all
    assert "ratio_arithmetic" in dict_all
    assert "cyclomatic_complexity" in dict_all
    assert "dfg_node_count" in dict_all

    # 2. Ablation: Byte only
    cfg_byte = FeatureConfig(enable_byte=True, enable_instruction=False, enable_cfg=False, enable_dfg=False)
    ext_byte = FeatureExtractor(config=cfg_byte)
    vec_byte, names_byte, _ = ext_byte.extract_features(fn0)
    assert len(vec_byte) < len(vec_all)
    assert all("entropy" in name or "byte" in name for name in names_byte)

    # 3. Ablation: Instruction only
    cfg_insn = FeatureConfig(enable_byte=False, enable_instruction=True, enable_cfg=False, enable_dfg=False)
    ext_insn = FeatureExtractor(config=cfg_insn)
    vec_insn, names_insn, _ = ext_insn.extract_features(fn0)
    assert len(vec_insn) < len(vec_all)
    assert "ratio_arithmetic" in names_insn
