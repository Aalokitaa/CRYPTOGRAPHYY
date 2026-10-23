"""
CryptoScope Unified Binary Analysis Engine
Orchestrates Architecture Detection, Symbol-less Function Recovery,
CFG construction, DFG construction, and Call Graph synthesis.
Supports pluggable backends (Built-in Capstone/LIEF, optional Ghidra/radare2).
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from pydantic import BaseModel

from backend.app.datasets.manifest import TargetISA
from backend.app.analysis.detector import ArchitectureDetector, DetectionResult
from backend.app.analysis.functions import FunctionBoundaryRecovery, RecoveredFunction
from backend.app.analysis.cfg import FunctionCFG, CallGraph
from backend.app.analysis.dfg import FunctionDFG

class AnalysisResultModel(BaseModel):
    binary_path: str
    file_size: int
    format: str
    isa: str
    endianness: str
    bits: int
    entrypoint: str
    confidence: float
    total_functions_recovered: int
    total_basic_blocks: int
    executable_sections: List[Dict[str, Any]]
    backend_used: str

class BinaryAnalysisPipeline:
    def __init__(self, backend_type: str = "builtin"):
        self.backend_type = backend_type
        self.detector = ArchitectureDetector()

    def analyze_binary(self, binary_path: Path) -> Tuple[DetectionResult, List[RecoveredFunction], CallGraph, Dict[int, FunctionCFG], Dict[int, FunctionDFG]]:
        binary_path = Path(binary_path)
        if not binary_path.exists():
            raise FileNotFoundError(f"Binary file not found: {binary_path}")

        # Step 1: Detect architecture, format, endianness
        detection = self.detector.detect(binary_path)

        # Step 2: Read executable bytes
        with open(binary_path, "rb") as f:
            full_data = f.read()

        recovered_functions: List[RecoveredFunction] = []

        recovery = FunctionBoundaryRecovery(
            isa=detection.isa,
            endianness=detection.endianness
        )

        for reg in detection.executable_regions:
            offset = reg.get("offset", 0)
            vaddr = reg.get("vaddr", 0)
            size = reg.get("size", len(full_data))
            chunk = full_data[offset : offset + size]

            fns = recovery.recover_functions(chunk, vaddr, entrypoint=detection.entrypoint)
            recovered_functions.extend(fns)

        # Fallback if no functions recovered
        if not recovered_functions and full_data:
            fallback_fns = recovery.recover_functions(full_data[:min(len(full_data), 16384)], 0x400000)
            recovered_functions.extend(fallback_fns)

        # Step 3: Build intra-procedural CFG and DFG per function
        cfgs: Dict[int, FunctionCFG] = {}
        dfgs: Dict[int, FunctionDFG] = {}

        for fn in recovered_functions:
            cfg = FunctionCFG(fn)
            dfg = FunctionDFG(fn)
            cfgs[fn.entry_addr] = cfg
            dfgs[fn.entry_addr] = dfg

        # Step 4: Build inter-procedural Call Graph
        callgraph = CallGraph(recovered_functions)

        return detection, recovered_functions, callgraph, cfgs, dfgs
