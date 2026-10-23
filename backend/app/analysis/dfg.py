"""
CryptoScope Data Flow Graph (DFG) Engine
Paper Section III-C, Table I:
- Intra-procedural register def-use chain tracking
- Per-architecture register name normalization
- Memory load/store dependencies and immediate constants
- Def-use chain depth, table lookup detection, and DFG serialization
"""

from typing import List, Dict, Set, Optional, Tuple, Any
import networkx as nx
from backend.app.datasets.manifest import TargetISA
from backend.app.analysis.disassembler import DisassembledInstruction
from backend.app.analysis.functions import RecoveredFunction

# Unified architectural register normalization mapping
def normalize_register(reg_name: str, isa: TargetISA) -> str:
    r = reg_name.lower().strip()
    if not r:
        return ""

    if isa == TargetISA.X86_64:
        # Accumulator
        if r in {"rax", "eax", "ax", "al", "ah"}: return "REG_0"
        # Base
        if r in {"rbx", "ebx", "bx", "bl", "bh"}: return "REG_1"
        # Counter
        if r in {"rcx", "ecx", "cx", "cl", "ch"}: return "REG_2"
        # Data
        if r in {"rdx", "edx", "dx", "dl", "dh"}: return "REG_3"
        # Source/Dest Index
        if r in {"rsi", "esi", "si", "sil"}: return "REG_4"
        if r in {"rdi", "edi", "di", "dil"}: return "REG_5"
        # Stack & Base pointer
        if r in {"rsp", "esp", "sp"}: return "REG_SP"
        if r in {"rbp", "ebp", "bp"}: return "REG_FP"
        # R8..R15
        for i in range(8, 16):
            if r.startswith(f"r{i}"): return f"REG_{i}"
        return f"REG_{r.upper()}"

    elif isa == TargetISA.ARM32:
        if r in {"sp", "r13"}: return "REG_SP"
        if r in {"lr", "r14"}: return "REG_LR"
        if r in {"pc", "r15"}: return "REG_PC"
        if r.startswith("r") and r[1:].isdigit():
            idx = int(r[1:])
            return f"REG_{idx}"
        return f"REG_{r.upper()}"

    elif isa == TargetISA.ARM64:
        if r in {"sp", "wsp"}: return "REG_SP"
        if r in {"xzr", "wzr"}: return "REG_ZERO"
        if (r.startswith("x") or r.startswith("w")) and r[1:].isdigit():
            idx = int(r[1:])
            return f"REG_{idx}"
        return f"REG_{r.upper()}"

    elif isa in [TargetISA.MIPS32_LE, TargetISA.MIPS32_BE]:
        if r in {"$zero", "zero", "$0", "0"}: return "REG_ZERO"
        if r in {"$sp", "sp", "$29"}: return "REG_SP"
        if r in {"$fp", "fp", "$s8", "$30"}: return "REG_FP"
        if r in {"$ra", "ra", "$31"}: return "REG_LR"
        # Map common MIPS registers to numeric
        mips_alias = {
            "$v0": 2, "$v1": 3,
            "$a0": 4, "$a1": 5, "$a2": 6, "$a3": 7,
            "$t0": 8, "$t1": 9, "$t2": 10, "$t3": 11, "$t4": 12, "$t5": 13, "$t6": 14, "$t7": 15,
            "$s0": 16, "$s1": 17, "$s2": 18, "$s3": 19, "$s4": 20, "$s5": 21, "$s6": 22, "$s7": 23,
            "$t8": 24, "$t9": 25
        }
        if r in mips_alias:
            return f"REG_{mips_alias[r]}"
        return f"REG_{r.replace('$', '').upper()}"

    elif isa == TargetISA.RISCV64:
        if r in {"zero", "x0"}: return "REG_ZERO"
        if r in {"ra", "x1"}: return "REG_LR"
        if r in {"sp", "x2"}: return "REG_SP"
        if r in {"s0", "fp", "x8"}: return "REG_FP"
        # ABI to register index
        riscv_abi = {
            "a0": 10, "a1": 11, "a2": 12, "a3": 13, "a4": 14, "a5": 15, "a6": 16, "a7": 17,
            "t0": 5, "t1": 6, "t2": 7, "t3": 28, "t4": 29, "t5": 30, "t6": 31,
            "s1": 9, "s2": 18, "s3": 19, "s4": 20, "s5": 21, "s6": 22, "s7": 23
        }
        if r in riscv_abi:
            return f"REG_{riscv_abi[r]}"
        if r.startswith("x") and r[1:].isdigit():
            return f"REG_{r[1:]}"
        return f"REG_{r.upper()}"

    return f"REG_{r.upper()}"


class FunctionDFG:
    def __init__(self, function: RecoveredFunction):
        self.function: RecoveredFunction = function
        self.graph: nx.DiGraph = nx.DiGraph()
        self.def_use_chains: List[List[int]] = []
        self.constants: List[int] = []
        self.memory_dependencies: List[Tuple[int, int]] = []
        self._build_dfg()

    def _build_dfg(self):
        last_def: Dict[str, int] = {}
        last_mem_write: Optional[int] = None

        # Add node for each instruction
        for insn in self.function.instructions:
            self.graph.add_node(
                insn.address,
                mnemonic=insn.mnemonic,
                op_str=insn.op_str,
                hex_bytes=insn.hex_bytes
            )

            # 1. Harvest immediate constants
            for op in insn.operands:
                if op.get("type") == 2 and "imm" in op:
                    self.constants.append(op["imm"])

            # 2. Register Read (Uses) -> add edge from last defining instruction
            for r in insn.regs_read:
                norm_r = normalize_register(r, self.function.isa)
                if norm_r and norm_r in last_def:
                    producer = last_def[norm_r]
                    self.graph.add_edge(producer, insn.address, var=norm_r, type="reg")

            # 3. Register Write (Defs) -> update definition map
            for w in insn.regs_write:
                norm_w = normalize_register(w, self.function.isa)
                if norm_w:
                    last_def[norm_w] = insn.address

            # 4. Memory read/write dependencies
            has_mem_read = any(op.get("type") == 3 for op in insn.operands)
            has_mem_write = any(op.get("type") == 3 and idx == 0 for idx, op in enumerate(insn.operands))

            if has_mem_read and last_mem_write is not None:
                self.graph.add_edge(last_mem_write, insn.address, type="mem_dep")
                self.memory_dependencies.append((last_mem_write, insn.address))

            if has_mem_write:
                last_mem_write = insn.address

        # Compute def-use chain paths
        try:
            roots = [n for n, d in self.graph.in_degree() if d == 0]
            leaves = [n for n, d in self.graph.out_degree() if d == 0]
            for r in roots:
                for l in leaves:
                    if nx.has_path(self.graph, r, l):
                        paths = list(nx.all_simple_paths(self.graph, r, l, cutoff=15))
                        self.def_use_chains.extend(paths[:5])
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        chain_lens = [len(p) for p in self.def_use_chains] if self.def_use_chains else [0]
        max_chain = max(chain_lens) if chain_lens else 0
        avg_chain = sum(chain_lens) / max(1, len(chain_lens))

        # Detect table lookup pattern (e.g. load with displacement or index register)
        table_lookups = 0
        for insn in self.function.instructions:
            for op in insn.operands:
                if op.get("type") == 3 and "mem" in op: # memory operand
                    mem = op["mem"]
                    if mem.get("index") or (mem.get("disp", 0) > 0x100):
                        table_lookups += 1

        return {
            "dfg_node_count": self.graph.number_of_nodes(),
            "dfg_edge_count": self.graph.number_of_edges(),
            "max_def_use_chain_len": max_chain,
            "avg_def_use_chain_len": round(avg_chain, 2),
            "constant_count": len(self.constants),
            "table_lookup_count": table_lookups,
            "memory_dep_count": len(self.memory_dependencies)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes DFG for API and UI graph visualization."""
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append({
                "id": str(n),
                "label": f"{hex(n)}: {data.get('mnemonic')} {data.get('op_str')}",
                "address": hex(n),
                "mnemonic": data.get("mnemonic")
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": str(u),
                "target": str(v),
                "id": f"dfg_{u}_{v}",
                "label": data.get("var", data.get("type", ""))
            })

        return {
            "function_id": self.function.id,
            "stats": self.get_stats(),
            "nodes": nodes,
            "edges": edges
        }
