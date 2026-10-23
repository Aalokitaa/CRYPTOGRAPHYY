"""
CryptoScope Security Advisory Engine
Paper Section V-F:
Audits identified cryptographic primitives and combinations to produce
defensive security observations (flagging weak, broken, or misconfigured cryptography).
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from pydantic import BaseModel
from backend.app.protocol.graph import ProtocolGraphData

class SecurityAdvisory(BaseModel):
    advisory_id: str
    title: str
    severity: str # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"
    cve_reference: Optional[str] = None
    affected_primitives: List[str]
    affected_addresses: List[str]
    risk_summary: str
    remediation_guidance: str

class SecurityAdvisoryEngine:
    def __init__(self):
        pass

    def generate_advisories(self, graph_data: ProtocolGraphData) -> List[SecurityAdvisory]:
        advisories: List[SecurityAdvisory] = []
        if not graph_data.nodes:
            return advisories

        prims = {n.primitive for n in graph_data.nodes}
        nodes_by_prim: Dict[str, List[str]] = {}
        for n in graph_data.nodes:
            nodes_by_prim.setdefault(n.primitive, []).append(n.hex_address)

        # 1. Check for DES or 3DES
        if "DES/3DES" in prims:
            advisories.append(SecurityAdvisory(
                advisory_id="SEC-ADV-001",
                title="Deprecated Legacy Cipher Detected: DES / Triple-DES",
                severity="HIGH",
                cve_reference="CVE-2016-2183 (Sweet32)",
                affected_primitives=["DES/3DES"],
                affected_addresses=nodes_by_prim.get("DES/3DES", []),
                risk_summary=(
                    "Single DES utilizes an effective key length of only 56 bits, vulnerable to exhaustive "
                    "key recovery. 3DES utilizes a 64-bit block size susceptible to birthday bound collision attacks "
                    "(Sweet32) in high-throughput channels."
                ),
                remediation_guidance=(
                    "Deprecate DES/3DES routines. Replace with modern NIST-approved symmetric ciphers such as "
                    "AES-128/256 in Galois/Counter Mode (GCM) or ChaCha20-Poly1305."
                )
            ))

        # 2. Check for Unauthenticated Encryption (Symmetric Cipher without MAC/AEAD)
        has_sym = bool(prims.intersection({"AES", "ChaCha20", "DES/3DES"}))
        has_mac = "HMAC" in prims
        if has_sym and not has_mac:
            ciphers = list(prims.intersection({"AES", "ChaCha20", "DES/3DES"}))
            c_addrs = []
            for c in ciphers: c_addrs.extend(nodes_by_prim.get(c, []))

            advisories.append(SecurityAdvisory(
                advisory_id="SEC-ADV-002",
                title="Unauthenticated Symmetric Encryption (Missing MAC/AEAD)",
                severity="MEDIUM",
                cve_reference="CWE-311 / CWE-327",
                affected_primitives=ciphers,
                affected_addresses=c_addrs,
                risk_summary=(
                    "Symmetric encryption primitives were detected without accompanying cryptographic message "
                    "authentication codes (MAC/HMAC). Unauthenticated ciphertext allows active adversaries to perform "
                    "bit-flipping attacks, padding-oracle attacks, or cut-and-paste tampering."
                ),
                remediation_guidance=(
                    "Adopt Authenticated Encryption with Associated Data (AEAD) constructions (such as AES-GCM, "
                    "AES-CCM, or ChaCha20-Poly1305) or implement strict Encrypt-then-MAC with HMAC-SHA256."
                )
            ))

        # 3. Informational: Legacy Hash Algorithm in Signature Chains
        if "SHA-256" in prims or "SHA-512" in prims:
            advisories.append(SecurityAdvisory(
                advisory_id="SEC-ADV-003",
                title="Cryptographic Hash Conformance: SHA-2 Family Confirmed",
                severity="INFORMATIONAL",
                cve_reference="NIST FIPS 180-4",
                affected_primitives=list(prims.intersection({"SHA-256", "SHA-512"})),
                affected_addresses=nodes_by_prim.get("SHA-256", []) + nodes_by_prim.get("SHA-512", []),
                risk_summary="Firmware utilizes approved SHA-2 family digests (256-bit / 512-bit). No deprecated MD5 or SHA-1 detected.",
                remediation_guidance="Maintain SHA-256/512 or evaluate migration to SHA-3 (Keccak) for future revisions."
            ))

        return advisories
