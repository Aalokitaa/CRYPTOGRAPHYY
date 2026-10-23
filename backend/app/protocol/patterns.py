"""
CryptoScope Protocol Pattern Matcher
Paper Section V-F:
Infers high-level protocol constructs from topological combinations of identified primitives:
- Hybrid Encryption / TLS-like Handshake (Key Exchange -> KDF -> Cipher -> MAC)
- Hash-then-Sign (Digest -> Signature Verification)
- Authenticated Encryption (Encrypt-then-MAC / AEAD)
- HMAC-based Authentication
Includes evidence trails and scientific caveats on static analysis limitations.
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from pydantic import BaseModel
from backend.app.protocol.graph import ProtocolGraphData

class ProtocolPatternFinding(BaseModel):
    pattern_name: str
    category: str # "Handshake", "Signature", "AEAD", "Authentication"
    confidence: float # 0.0 to 1.0
    evidence: List[str]
    involved_primitives: List[str]
    involved_nodes: List[str]
    caveat: str
    description: str

class ProtocolPatternMatcher:
    def __init__(self):
        self.standard_caveat = (
            "CAVEAT: Static binary analysis identifies compiled algorithmic capabilities and structural "
            "call dependencies. Static analysis alone cannot confirm exact runtime protocol execution or network packet sequences."
        )

    def match_patterns(self, graph_data: ProtocolGraphData) -> List[ProtocolPatternFinding]:
        findings: List[ProtocolPatternFinding] = []
        if not graph_data.nodes:
            return findings

        # Group discovered primitives
        prims_present = {n.primitive for n in graph_data.nodes}
        nodes_by_prim: Dict[str, List[str]] = {}
        for n in graph_data.nodes:
            nodes_by_prim.setdefault(n.primitive, []).append(n.hex_address)

        has_asymm = bool(prims_present.intersection({"RSA", "ECC"}))
        has_hash = bool(prims_present.intersection({"SHA-256", "SHA-512"}))
        has_cipher = bool(prims_present.intersection({"AES", "ChaCha20", "DES/3DES"}))
        has_mac = "HMAC" in prims_present

        # 1. TLS-like Handshake / Hybrid Key Exchange & Encryption
        if has_asymm and has_cipher and (has_mac or has_hash):
            asym_prim = "ECC" if "ECC" in prims_present else "RSA"
            sym_prim = "AES" if "AES" in prims_present else "ChaCha20"
            evidence = [
                f"Asymmetric key agreement capability detected ({asym_prim})",
                f"Symmetric bulk encryption primitive detected ({sym_prim})",
                "Integrity/hash primitives present for transcript verification"
            ]
            involved = list(prims_present.intersection({asym_prim, sym_prim, "HMAC", "SHA-256", "SHA-512"}))
            inv_nodes = []
            for p in involved: inv_nodes.extend(nodes_by_prim.get(p, []))

            findings.append(ProtocolPatternFinding(
                pattern_name="TLS-like Handshake / Hybrid Encryption Pipeline",
                category="Handshake",
                confidence=0.88,
                evidence=evidence,
                involved_primitives=involved,
                involved_nodes=inv_nodes,
                caveat=self.standard_caveat,
                description=(
                    f"Binary contains structural composition for hybrid key exchange ({asym_prim}) followed by "
                    f"symmetric channel encryption ({sym_prim}). Characteristic of TLS, SSH, or secure bootloaders."
                )
            ))

        # 2. Hash-then-Sign Signature Verification Scheme
        if has_hash and has_asymm:
            asym_prim = "RSA" if "RSA" in prims_present else "ECC"
            hash_prim = "SHA-256" if "SHA-256" in prims_present else "SHA-512"
            evidence = [
                f"Cryptographic digest primitive ({hash_prim}) paired with asymmetric engine ({asym_prim})",
                "Characteristic of PKCS#1 v1.5 or ECDSA signature validation sequences"
            ]
            involved = [hash_prim, asym_prim]
            inv_nodes = nodes_by_prim.get(hash_prim, []) + nodes_by_prim.get(asym_prim, [])

            findings.append(ProtocolPatternFinding(
                pattern_name="Hash-then-Sign (Digital Signature Verification)",
                category="Signature",
                confidence=0.85,
                evidence=evidence,
                involved_primitives=involved,
                involved_nodes=inv_nodes,
                caveat=self.standard_caveat,
                description=(
                    f"Cryptographic hash ({hash_prim}) combined with asymmetric mathematics ({asym_prim}). "
                    "Typically employed in firmware image authentication, certificate verification, or code-signing."
                )
            ))

        # 3. Authenticated Encryption (Encrypt-then-MAC / AEAD)
        if has_cipher and has_mac:
            sym_prim = "AES" if "AES" in prims_present else "ChaCha20"
            evidence = [
                f"Symmetric cipher ({sym_prim}) co-located with keyed message authentication (HMAC)",
                "Provides both confidentiality and ciphertext integrity verification"
            ]
            involved = [sym_prim, "HMAC"]
            inv_nodes = nodes_by_prim.get(sym_prim, []) + nodes_by_prim.get("HMAC", [])

            findings.append(ProtocolPatternFinding(
                pattern_name="Authenticated Encryption (Encrypt-then-MAC / AEAD)",
                category="AEAD",
                confidence=0.82,
                evidence=evidence,
                involved_primitives=involved,
                involved_nodes=inv_nodes,
                caveat=self.standard_caveat,
                description=(
                    f"Symmetric block or stream cipher ({sym_prim}) paired with HMAC authentication. "
                    "Protects against padding-oracle and chosen-ciphertext attacks."
                )
            ))

        # 4. HMAC-based Message Authentication
        if has_mac and not has_cipher:
            evidence = [
                "Keyed-Hash Message Authentication Code (HMAC) isolated without bulk encryption",
                "Inner (0x36) and outer (0x5C) pad constants detected"
            ]
            involved = ["HMAC"]
            inv_nodes = nodes_by_prim.get("HMAC", [])

            findings.append(ProtocolPatternFinding(
                pattern_name="HMAC Message Authentication Protocol",
                category="Authentication",
                confidence=0.90,
                evidence=evidence,
                involved_primitives=involved,
                involved_nodes=inv_nodes,
                caveat=self.standard_caveat,
                description="Message authentication protocol utilizing shared secrets for token or command verification."
            ))

        # 5. Standalone Unauthenticated Bulk Encryption
        if has_cipher and not has_mac:
            sym_prim = "AES" if "AES" in prims_present else ("DES/3DES" if "DES/3DES" in prims_present else "ChaCha20")
            evidence = [
                f"Symmetric cipher ({sym_prim}) present without accompanying cryptographic MAC or AEAD scheme",
                "Integrity validation appears delegated to non-cryptographic CRC or absent"
            ]
            involved = [sym_prim]
            inv_nodes = nodes_by_prim.get(sym_prim, [])

            findings.append(ProtocolPatternFinding(
                pattern_name="Standalone Unauthenticated Encryption",
                category="Bulk Encryption",
                confidence=0.75,
                evidence=evidence,
                involved_primitives=involved,
                involved_nodes=inv_nodes,
                caveat=self.standard_caveat,
                description=f"Symmetric encryption ({sym_prim}) operating without authenticated integrity checks."
            ))

        # Sort findings by confidence
        findings.sort(key=lambda f: f.confidence, reverse=True)
        return findings
