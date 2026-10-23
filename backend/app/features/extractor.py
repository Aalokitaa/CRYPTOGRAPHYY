"""
CryptoScope Comprehensive Feature Extraction Engine
Paper Table I:
Four independently toggleable feature groups for ablation:
1. Byte-level features (entropy, sliding entropy, byte histograms, n-grams)
2. Instruction-level features (semantic classes vs raw mnemonics, operand stats, operation ratios)
3. CFG-level features (block/edge counts, cyclomatic complexity, loops, nesting depth, degree distributions)
4. DFG-level features (def-use chains, memory deps, constant counts, table lookup patterns)
Supports feature normalization (StandardScaler/MinMax) and disk caching.
"""

import math
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from backend.app.datasets.manifest import TargetISA
from backend.app.analysis.functions import RecoveredFunction
from backend.app.analysis.cfg import FunctionCFG
from backend.app.analysis.dfg import FunctionDFG
from backend.app.features.semantic_isa import SemanticInsnClass, map_mnemonic_to_semantic

class FeatureConfig:
    def __init__(self, 
                 enable_byte: bool = True, 
                 enable_instruction: bool = True, 
                 enable_cfg: bool = True, 
                 enable_dfg: bool = True,
                 use_semantic_isa: bool = True):
        self.enable_byte = enable_byte
        self.enable_instruction = enable_instruction
        self.enable_cfg = enable_cfg
        self.enable_dfg = enable_dfg
        self.use_semantic_isa = use_semantic_isa

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_byte": self.enable_byte,
            "enable_instruction": self.enable_instruction,
            "enable_cfg": self.enable_cfg,
            "enable_dfg": self.enable_dfg,
            "use_semantic_isa": self.use_semantic_isa
        }

class FeatureExtractor:
    def __init__(self, config: Optional[FeatureConfig] = None, cache_dir: Optional[Path] = None):
        self.config = config or FeatureConfig()
        self.cache_dir = cache_dir or (Path(__file__).resolve().parent.parent.parent.parent / ".cache" / "features")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract_byte_features(self, raw_bytes: bytes) -> Dict[str, float]:
        """Group 1: Byte-level features"""
        feats: Dict[str, float] = {}
        if not raw_bytes:
            feats["byte_len"] = 0.0
            feats["entropy_overall"] = 0.0
            feats["entropy_window_mean"] = 0.0
            feats["entropy_window_std"] = 0.0
            for i in range(16):
                feats[f"byte_hist_bin_{i}"] = 0.0
            return feats

        length = len(raw_bytes)
        feats["byte_len"] = float(length)

        # 1. Overall Shannon Entropy
        counts = [0] * 256
        for b in raw_bytes:
            counts[b] += 1
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / length
                entropy -= p * math.log2(p)
        feats["entropy_overall"] = round(entropy, 4)

        # 2. Sliding window entropy (window=32 bytes)
        win_size = 32
        window_entropies = []
        if length >= win_size:
            for w in range(0, length - win_size + 1, win_size // 2):
                chunk = raw_bytes[w : w + win_size]
                w_counts = [0] * 256
                for b in chunk: w_counts[b] += 1
                w_ent = 0.0
                for c in w_counts:
                    if c > 0:
                        p = c / win_size
                        w_ent -= p * math.log2(p)
                window_entropies.append(w_ent)

        if window_entropies:
            feats["entropy_window_mean"] = round(float(np.mean(window_entropies)), 4)
            feats["entropy_window_std"] = round(float(np.std(window_entropies)), 4)
        else:
            feats["entropy_window_mean"] = feats["entropy_overall"]
            feats["entropy_window_std"] = 0.0

        # 3. Normalized 16-bin byte frequency histogram
        for i in range(16):
            bin_sum = sum(counts[i*16 : (i+1)*16])
            feats[f"byte_hist_bin_{i}"] = round(bin_sum / length, 4)

        return feats

    def extract_instruction_features(self, function: RecoveredFunction) -> Dict[str, float]:
        """Group 2: Instruction-level features"""
        feats: Dict[str, float] = {}
        insns = function.instructions
        total_insns = len(insns)
        feats["insn_count"] = float(total_insns)

        if total_insns == 0:
            for cls in SemanticInsnClass:
                feats[f"sem_ratio_{cls.value}"] = 0.0
            feats["ratio_arithmetic"] = 0.0
            feats["ratio_logic"] = 0.0
            feats["ratio_shift_rot"] = 0.0
            feats["ratio_load_store"] = 0.0
            feats["ratio_branch"] = 0.0
            feats["imm_operand_ratio"] = 0.0
            feats["mem_operand_ratio"] = 0.0
            return feats

        # 1. Semantic instruction class histogram
        sem_counts = {cls.value: 0 for cls in SemanticInsnClass}
        imm_ops = 0
        mem_ops = 0
        reg_ops = 0
        total_ops = 0

        for insn in insns:
            if self.config.use_semantic_isa:
                cls = map_mnemonic_to_semantic(insn.mnemonic)
                sem_counts[cls.value] += 1
            else:
                # Raw fallback: simplified opcode bucket
                sem_counts[insn.mnemonic[:3].upper()] = sem_counts.get(insn.mnemonic[:3].upper(), 0) + 1

            for op in insn.operands:
                total_ops += 1
                op_type = op.get("type")
                if op_type == 2: imm_ops += 1
                elif op_type == 3: mem_ops += 1
                elif op_type == 1: reg_ops += 1

        for cls in SemanticInsnClass:
            feats[f"sem_ratio_{cls.value}"] = round(sem_counts.get(cls.value, 0) / total_insns, 4)

        # 2. Key cryptographic instruction domain ratios
        arith = sem_counts["ADD"] + sem_counts["SUB"] + sem_counts["MUL"]
        logic = sem_counts["AND_OR_XOR"]
        shifts = sem_counts["SHL_SHR_ROT"]
        mem = sem_counts["LOAD"] + sem_counts["STORE"]
        branches = sem_counts["BRANCH_COND"] + sem_counts["BRANCH_UNCOND"]

        feats["ratio_arithmetic"] = round(arith / total_insns, 4)
        feats["ratio_logic"] = round(logic / total_insns, 4)
        feats["ratio_shift_rot"] = round(shifts / total_insns, 4)
        feats["ratio_load_store"] = round(mem / total_insns, 4)
        feats["ratio_branch"] = round(branches / total_insns, 4)

        # 3. Operand type ratios
        feats["imm_operand_ratio"] = round(imm_ops / max(1, total_ops), 4)
        feats["mem_operand_ratio"] = round(mem_ops / max(1, total_ops), 4)

        return feats

    def extract_cfg_features(self, cfg: FunctionCFG) -> Dict[str, float]:
        """Group 3: CFG-level features"""
        deg_stats = cfg.get_degree_stats()
        return {
            "cfg_node_count": float(cfg.node_count),
            "cfg_edge_count": float(cfg.edge_count),
            "cyclomatic_complexity": float(cfg.cyclomatic_complexity),
            "loop_count": float(len(cfg.detect_loops())),
            "loop_nesting_depth": float(cfg.get_loop_nesting_depth()),
            "avg_in_degree": deg_stats["avg_in_degree"],
            "avg_out_degree": deg_stats["avg_out_degree"],
            "max_in_degree": deg_stats["max_in_degree"],
            "max_out_degree": deg_stats["max_out_degree"],
            "cfg_density": round(cfg.edge_count / max(1, cfg.node_count * (cfg.node_count - 1)), 4) if cfg.node_count > 1 else 0.0
        }

    def extract_dfg_features(self, dfg: FunctionDFG) -> Dict[str, float]:
        """Group 4: DFG-level features"""
        stats = dfg.get_stats()
        return {
            "dfg_node_count": float(stats["dfg_node_count"]),
            "dfg_edge_count": float(stats["dfg_edge_count"]),
            "max_def_use_chain_len": float(stats["max_def_use_chain_len"]),
            "avg_def_use_chain_len": float(stats["avg_def_use_chain_len"]),
            "dfg_constant_count": float(stats["constant_count"]),
            "table_lookup_count": float(stats["table_lookup_count"]),
            "memory_dep_count": float(stats["memory_dep_count"])
        }

    def extract_features(self, 
                         function: RecoveredFunction, 
                         cfg: Optional[FunctionCFG] = None, 
                         dfg: Optional[FunctionDFG] = None) -> Tuple[np.ndarray, List[str], Dict[str, float]]:
        """
        Extracts the full concatenated feature vector according to the active config toggles.
        Returns: (numpy_vector, feature_names_list, feature_dict)
        """
        all_features: Dict[str, float] = {}

        # 1. Byte features
        if self.config.enable_byte:
            raw_bytes = b"".join(insn.bytes for insn in function.instructions)
            all_features.update(self.extract_byte_features(raw_bytes))

        # 2. Instruction features
        if self.config.enable_instruction:
            all_features.update(self.extract_instruction_features(function))

        # 3. CFG features
        if self.config.enable_cfg:
            cfg_obj = cfg or FunctionCFG(function)
            all_features.update(self.extract_cfg_features(cfg_obj))

        # 4. DFG features
        if self.config.enable_dfg:
            dfg_obj = dfg or FunctionDFG(function)
            all_features.update(self.extract_dfg_features(dfg_obj))

        sorted_names = sorted(all_features.keys())
        vec = np.array([all_features[k] for k in sorted_names], dtype=np.float32)

        return vec, sorted_names, all_features
