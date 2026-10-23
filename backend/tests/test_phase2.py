"""
Unit and Integration Tests for Phase 2: Binary Analysis Pipeline
Tests:
- Architecture, format, and endianness detection (ELF & Raw Blobs)
- Symbol-less function boundary recovery
- Basic block partitioning
- CFG construction, cyclomatic complexity, loop detection
- DFG construction, register normalization, def-use chains
- Full BinaryAnalysisPipeline execution
"""

from pathlib import Path
import pytest

from backend.app.datasets.manifest import TargetISA
from backend.app.analysis.detector import ArchitectureDetector
from backend.app.analysis.disassembler import MultiIsaDisassembler
from backend.app.analysis.functions import FunctionBoundaryRecovery
from backend.app.analysis.cfg import FunctionCFG, CallGraph
from backend.app.analysis.dfg import FunctionDFG, normalize_register
from backend.app.analysis.engine import BinaryAnalysisPipeline

def test_register_normalization():
    # x86-64
    assert normalize_register("rax", TargetISA.X86_64) == "REG_0"
    assert normalize_register("eax", TargetISA.X86_64) == "REG_0"
    assert normalize_register("rbx", TargetISA.X86_64) == "REG_1"
    assert normalize_register("rsp", TargetISA.X86_64) == "REG_SP"
    # ARM32
    assert normalize_register("r0", TargetISA.ARM32) == "REG_0"
    assert normalize_register("r1", TargetISA.ARM32) == "REG_1"
    assert normalize_register("lr", TargetISA.ARM32) == "REG_LR"
    # ARM64
    assert normalize_register("x0", TargetISA.ARM64) == "REG_0"
    assert normalize_register("w0", TargetISA.ARM64) == "REG_0"
    assert normalize_register("sp", TargetISA.ARM64) == "REG_SP"
    # MIPS
    assert normalize_register("$v0", TargetISA.MIPS32_LE) == "REG_2"
    assert normalize_register("$a0", TargetISA.MIPS32_LE) == "REG_4"
    assert normalize_register("$sp", TargetISA.MIPS32_LE) == "REG_SP"
    # RISC-V
    assert normalize_register("a0", TargetISA.RISCV64) == "REG_10"
    assert normalize_register("sp", TargetISA.RISCV64) == "REG_SP"

def test_architecture_detection_elf():
    base_dir = Path(__file__).resolve().parent.parent.parent
    detector = ArchitectureDetector()

    # Test detection on an ARM64 stripped binary from dataset
    arm64_bin = base_dir / "datasets" / "binaries" / "stripped" / "bin_arm64_gcc_o2_stripped.elf"
    assert arm64_bin.exists(), "ARM64 test binary must exist"

    result = detector.detect(arm64_bin)
    assert result.is_structured is True
    assert result.format == "ELF"
    assert result.isa == TargetISA.ARM64
    assert result.bits == 64
    assert result.endianness == "little"
    assert len(result.executable_regions) > 0

def test_raw_blob_heuristic_detection():
    detector = ArchitectureDetector()
    # Synthetic x86-64 raw byte buffer with prologue and arithmetic
    raw_x86 = (b'\x55\x48\x89\xe5\x48\x83\xec\x20'
               b'\x89\x7d\xec\x89\x75\xe8\x8b\x45\xec\x03\x45\xe8'
               b'\x5d\xc3') * 10

    res = detector.detect_raw_blob(raw_x86)
    assert res.is_structured is False
    assert res.format == "Raw Binary Blob"
    assert res.confidence > 0.3
    assert TargetISA.X86_64.value in res.score_breakdown

def test_function_boundary_and_cfg():
    base_dir = Path(__file__).resolve().parent.parent.parent
    x86_bin = base_dir / "datasets" / "binaries" / "stripped" / "bin_x86_64_gcc_o0_stripped.elf"
    assert x86_bin.exists()

    pipeline = BinaryAnalysisPipeline()
    detection, functions, callgraph, cfgs, dfgs = pipeline.analyze_binary(x86_bin)

    assert len(functions) > 0, "Must recover functions from binary"
    fn0 = functions[0]
    assert fn0.entry_addr > 0
    assert len(fn0.instructions) > 0
    assert len(fn0.basic_blocks) > 0

    cfg = cfgs[fn0.entry_addr]
    assert cfg.node_count >= 1
    assert cfg.cyclomatic_complexity >= 1

    dfg = dfgs[fn0.entry_addr]
    stats = dfg.get_stats()
    assert "dfg_node_count" in stats
    assert stats["dfg_node_count"] >= 1

def test_call_graph_construction():
    base_dir = Path(__file__).resolve().parent.parent.parent
    x86_bin = base_dir / "datasets" / "binaries" / "stripped" / "bin_x86_64_gcc_o0_stripped.elf"
    
    pipeline = BinaryAnalysisPipeline()
    _, functions, callgraph, _, _ = pipeline.analyze_binary(x86_bin)

    cg_dict = callgraph.to_dict()
    assert cg_dict["total_functions"] == len(functions)
    assert "nodes" in cg_dict
    assert "edges" in cg_dict
