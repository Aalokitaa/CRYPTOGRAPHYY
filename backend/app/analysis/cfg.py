"""
CryptoScope Control Flow Graph (CFG) & Call Graph Engine
Paper Section III-C, Table I:
- Function CFG construction via NetworkX DiGraph
- Cyclomatic complexity, back-edge loop detection, and nesting depth
- Degree distribution and structural graph vector representation
- Whole-binary Call Graph construction for protocol pattern analysis
"""

from typing import List, Dict, Set, Optional, Tuple, Any
import networkx as nx
from backend.app.analysis.functions import RecoveredFunction, BasicBlock

class FunctionCFG:
    def __init__(self, function: RecoveredFunction):
        self.function: RecoveredFunction = function
        self.graph: nx.DiGraph = nx.DiGraph()
        self._build_cfg()

    def _build_cfg(self):
        bb_map = {b.start_addr: b for b in self.function.basic_blocks}

        # Add nodes
        for bb in self.function.basic_blocks:
            self.graph.add_node(
                bb.start_addr,
                block_id=bb.block_id,
                start_addr=bb.start_addr,
                end_addr=bb.end_addr,
                insn_count=len(bb.instructions),
                size=bb.size
            )

        # Add directed edges
        for bb in self.function.basic_blocks:
            for succ in bb.successors:
                if succ in bb_map:
                    self.graph.add_edge(bb.start_addr, succ)

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    @property
    def cyclomatic_complexity(self) -> int:
        """Cyclomatic complexity: M = E - N + 2"""
        n = self.node_count
        e = self.edge_count
        if n == 0:
            return 1
        return max(1, e - n + 2)

    def detect_loops(self) -> List[Tuple[int, int]]:
        """Identifies back edges indicating loops via DFS cycle detection."""
        loops = []
        try:
            cycles = list(nx.simple_cycles(self.graph))
            for cycle in cycles:
                if len(cycle) >= 1:
                    loops.append((cycle[-1], cycle[0]))
        except Exception:
            pass
        return loops

    def get_loop_nesting_depth(self) -> int:
        """Computes maximum loop nesting depth."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if not cycles:
                return 0
            # Calculate overlap of cycle nodes
            max_depth = 1
            for i, c1 in enumerate(cycles):
                depth = 1
                s1 = set(c1)
                for j, c2 in enumerate(cycles):
                    if i != j and set(c2).issubset(s1):
                        depth += 1
                max_depth = max(max_depth, depth)
            return max_depth
        except Exception:
            return 0

    def get_degree_stats(self) -> Dict[str, float]:
        in_degrees = [d for _, d in self.graph.in_degree()]
        out_degrees = [d for _, d in self.graph.out_degree()]

        avg_in = sum(in_degrees) / max(1, len(in_degrees))
        avg_out = sum(out_degrees) / max(1, len(out_degrees))
        max_in = max(in_degrees) if in_degrees else 0
        max_out = max(out_degrees) if out_degrees else 0

        return {
            "avg_in_degree": round(avg_in, 3),
            "avg_out_degree": round(avg_out, 3),
            "max_in_degree": float(max_in),
            "max_out_degree": float(max_out)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes CFG for API and UI graph visualization (React Flow format)."""
        nodes = []
        for n, data in self.graph.nodes(data=True):
            bb = next((b for b in self.function.basic_blocks if b.start_addr == n), None)
            insn_lines = [f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in (bb.instructions if bb else [])]
            nodes.append({
                "id": str(n),
                "label": f"Block @ {hex(n)}",
                "instructions": insn_lines,
                "insn_count": data.get("insn_count", 0),
                "size": data.get("size", 0)
            })

        edges = []
        for u, v in self.graph.edges():
            edges.append({
                "source": str(u),
                "target": str(v),
                "id": f"e_{u}_{v}"
            })

        return {
            "function_id": self.function.id,
            "entry_addr": hex(self.function.entry_addr),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "loops_count": len(self.detect_loops()),
            "loop_nesting_depth": self.get_loop_nesting_depth(),
            "nodes": nodes,
            "edges": edges
        }


class CallGraph:
    def __init__(self, functions: List[RecoveredFunction]):
        self.functions: List[RecoveredFunction] = functions
        self.graph: nx.DiGraph = nx.DiGraph()
        self._build_callgraph()

    def _build_callgraph(self):
        fn_map = {fn.entry_addr: fn for fn in self.functions}

        # Add function nodes
        for fn in self.functions:
            self.graph.add_node(
                fn.entry_addr,
                fn_id=fn.id,
                entry_addr=fn.entry_addr,
                size=fn.size,
                block_count=len(fn.basic_blocks)
            )

        # Add call edges
        for fn in self.functions:
            for callee_addr in fn.callees:
                if callee_addr in fn_map:
                    self.graph.add_edge(fn.entry_addr, callee_addr)
                    fn_map[callee_addr].callers.add(fn.entry_addr)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes call graph for protocol pattern detection and UI."""
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append({
                "id": str(n),
                "label": f"fn_{hex(n)}",
                "entry_addr": hex(n),
                "size": data.get("size", 0),
                "block_count": data.get("block_count", 0)
            })

        edges = []
        for u, v in self.graph.edges():
            edges.append({
                "source": str(u),
                "target": str(v),
                "id": f"call_{u}_{v}"
            })

        return {
            "total_functions": self.graph.number_of_nodes(),
            "total_calls": self.graph.number_of_edges(),
            "nodes": nodes,
            "edges": edges
        }
