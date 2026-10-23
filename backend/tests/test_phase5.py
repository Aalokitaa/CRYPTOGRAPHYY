"""
Unit and Integration Tests for Phase 5: Protocol-Level Interpretation & Security Advisories
Tests:
- Protocol graph construction and serialization
- Pattern matching: TLS-like Handshake, Hash-then-Sign, AEAD, HMAC
- Evidence tracking and scientific caveat generation
- Defensive security advisories (DES/3DES Sweet32, unauthenticated encryption)
"""

import pytest
from backend.app.datasets.manifest import CryptoPrimitive, CryptoFamily
from backend.app.analysis.cfg import CallGraph
from backend.app.models.hierarchical import HierarchicalPrediction
from backend.app.protocol.graph import ProtocolGraphBuilder, ProtocolNode, ProtocolGraphData
from backend.app.protocol.patterns import ProtocolPatternMatcher
from backend.app.protocol.advisories import SecurityAdvisoryEngine

def test_protocol_graph_and_patterns():
    builder = ProtocolGraphBuilder()
    matcher = ProtocolPatternMatcher()

    # Create synthetic predictions for a binary containing ECC, AES, HMAC, and SHA-256
    preds = {
        0x401000: HierarchicalPrediction(
            is_crypto=True, l1_confidence=0.98,
            family="Asymmetric Cipher", l2_confidence=0.95,
            primitive="ECC", l3_confidence=0.92,
            overall_confidence=0.85, routing_path=[]
        ),
        0x402000: HierarchicalPrediction(
            is_crypto=True, l1_confidence=0.99,
            family="Symmetric Cipher", l2_confidence=0.98,
            primitive="AES", l3_confidence=0.95,
            overall_confidence=0.92, routing_path=[]
        ),
        0x403000: HierarchicalPrediction(
            is_crypto=True, l1_confidence=0.95,
            family="MAC", l2_confidence=0.90,
            primitive="HMAC", l3_confidence=0.90,
            overall_confidence=0.81, routing_path=[]
        ),
        0x404000: HierarchicalPrediction(
            is_crypto=True, l1_confidence=0.96,
            family="Hash", l2_confidence=0.95,
            primitive="SHA-256", l3_confidence=0.94,
            overall_confidence=0.86, routing_path=[]
        )
    }

    dummy_cg = CallGraph([])
    meta = {
        0x401000: {"name": "ecc_key_exchange", "size": 256},
        0x402000: {"name": "aes_encrypt", "size": 512},
        0x403000: {"name": "hmac_verify", "size": 128},
        0x404000: {"name": "sha256_hash", "size": 384}
    }

    graph = builder.build_protocol_graph(preds, dummy_cg, meta)
    assert graph.total_crypto_nodes == 4
    assert len(graph.nodes) == 4
    assert len(graph.edges) >= 3

    # Match protocol patterns
    findings = matcher.match_patterns(graph)
    assert len(findings) >= 2

    pattern_names = [f.pattern_name for f in findings]
    assert any("TLS" in p or "Handshake" in p for p in pattern_names)
    assert any("Hash-then-Sign" in p for p in pattern_names)
    assert any("Authenticated Encryption" in p for p in pattern_names)

    # Assert mandatory caveat is present
    for f in findings:
        assert "CAVEAT:" in f.caveat
        assert len(f.evidence) > 0

def test_security_advisories():
    engine = SecurityAdvisoryEngine()

    # Graph with legacy DES and unauthenticated encryption
    nodes = [
        ProtocolNode(
            id="n1", address=0x401000, hex_address="0x401000",
            name="des_encrypt", primitive="DES/3DES", family="Symmetric Cipher",
            confidence=0.9, size=200, is_crypto=True
        )
    ]
    graph = ProtocolGraphData(nodes=nodes, edges=[], total_crypto_nodes=1, density=0.0)

    advisories = engine.generate_advisories(graph)
    assert len(advisories) >= 2

    adv_titles = [a.title for a in advisories]
    assert any("DES" in t for t in adv_titles)
    assert any("Unauthenticated" in t for t in adv_titles)

    # Check Sweet32 CVE
    des_adv = next(a for a in advisories if "DES" in a.title)
    assert des_adv.severity == "HIGH"
    assert "Sweet32" in des_adv.cve_reference
    assert len(des_adv.remediation_guidance) > 10
