"""
CryptoScope Protocol Graph Synthesizer
Paper Section V-F:
Constructs an inter-procedural protocol graph linking identified cryptographic primitives
via control-flow call relationships and data-flow dependencies.
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from pydantic import BaseModel
import networkx as nx

from backend.app.datasets.manifest import CryptoPrimitive, CryptoFamily
from backend.app.analysis.cfg import CallGraph
from backend.app.models.hierarchical import HierarchicalPrediction

class ProtocolNode(BaseModel):
    id: str
    address: int
    hex_address: str
    name: str
    primitive: str
    family: str
    confidence: float
    size: int
    is_crypto: bool

class ProtocolEdge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str # "call", "data_dep", "sequential"
    description: str

class ProtocolGraphData(BaseModel):
    nodes: List[ProtocolNode]
    edges: List[ProtocolEdge]
    total_crypto_nodes: int
    density: float

class ProtocolGraphBuilder:
    def __init__(self):
        pass

    def build_protocol_graph(self, 
                             predictions: Dict[int, HierarchicalPrediction],
                             callgraph: CallGraph,
                             function_metadata: Dict[int, Dict[str, Any]]) -> ProtocolGraphData:
        """
        Builds the protocol interaction graph from function predictions and CallGraph.
        """
        crypto_addrs = set()
        nodes: List[ProtocolNode] = []
        edges: List[ProtocolEdge] = []

        # 1. Filter nodes to cryptographic primitives (or non-crypto callers of crypto)
        for addr, pred in predictions.items():
            if pred.is_crypto and pred.primitive != "Non-crypto":
                crypto_addrs.add(addr)
                meta = function_metadata.get(addr, {})
                nodes.append(ProtocolNode(
                    id=f"node_{hex(addr)}",
                    address=addr,
                    hex_address=hex(addr),
                    name=meta.get("name", f"fn_{hex(addr)}"),
                    primitive=pred.primitive,
                    family=pred.family,
                    confidence=pred.overall_confidence,
                    size=meta.get("size", 0),
                    is_crypto=True
                ))

        # 2. Add edges between crypto nodes from CallGraph
        edge_set = set()
        for u, v in callgraph.graph.edges():
            if u in crypto_addrs and v in crypto_addrs:
                edge_id = f"edge_{hex(u)}_{hex(v)}"
                if edge_id not in edge_set:
                    edge_set.add(edge_id)
                    edges.append(ProtocolEdge(
                        id=edge_id,
                        source=f"node_{hex(u)}",
                        target=f"node_{hex(v)}",
                        edge_type="call",
                        description=f"{predictions[u].primitive} invokes {predictions[v].primitive}"
                    ))

        # 3. If direct call graph is sparse, add sequential / co-occurrence dependency edges
        if len(edges) == 0 and len(nodes) > 1:
            sorted_nodes = sorted(nodes, key=lambda n: n.address)
            for i in range(len(sorted_nodes) - 1):
                n1 = sorted_nodes[i]
                n2 = sorted_nodes[i + 1]
                edge_id = f"seq_{n1.hex_address}_{n2.hex_address}"
                edges.append(ProtocolEdge(
                    id=edge_id,
                    source=n1.id,
                    target=n2.id,
                    edge_type="sequential",
                    description=f"{n1.primitive} precedes {n2.primitive} in binary address space"
                ))

        density = len(edges) / max(1, len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0

        return ProtocolGraphData(
            nodes=nodes,
            edges=edges,
            total_crypto_nodes=len(nodes),
            density=round(density, 3)
        )
