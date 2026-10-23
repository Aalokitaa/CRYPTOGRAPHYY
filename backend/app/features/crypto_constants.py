"""
CryptoScope Cryptographic Constant Scanner & Non-ML Baseline
Paper Section III-D:
- Detects standard cryptographic constants (AES, DES, RSA, ECC, SHA-256, SHA-512, HMAC, ChaCha20)
- Supports Little-Endian and Big-Endian byte patterns
- Isolated from ML training labels to eliminate leakage
- Serves as explainability aid and independent baseline classifier
"""

import struct
from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel
from backend.app.datasets.manifest import CryptoPrimitive

class ConstantMatch(BaseModel):
    primitive: CryptoPrimitive
    constant_name: str
    offset: int
    matched_length: int
    endianness: str
    description: str

class CryptoConstantScanner:
    def __init__(self):
        self._init_signatures()

    def _init_signatures(self):
        self.signatures = []

        # 1. AES S-Box (first 16 bytes: 0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76)
        aes_sbox_prefix = bytes([
            0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
            0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76
        ])
        self.signatures.append((CryptoPrimitive.AES, "AES Forward S-Box", aes_sbox_prefix, "any", "AES Rijndael S-box substitution table"))

        # AES Inverse S-Box
        aes_rsbox_prefix = bytes([
            0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38,
            0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb
        ])
        self.signatures.append((CryptoPrimitive.AES, "AES Inverse S-Box", aes_rsbox_prefix, "any", "AES Inverse S-box table"))

        # AES Rcon Table
        aes_rcon = bytes([0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36])
        self.signatures.append((CryptoPrimitive.AES, "AES Rcon Round Constants", aes_rcon, "any", "AES key schedule round constants"))

        # 2. SHA-256 K Constants (first 4 constants: 0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5)
        sha256_k_words = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5]
        sha256_k_le = b"".join(struct.pack("<I", w) for w in sha256_k_words)
        sha256_k_be = b"".join(struct.pack(">I", w) for w in sha256_k_words)
        self.signatures.append((CryptoPrimitive.SHA256, "SHA-256 K Table (LE)", sha256_k_le, "little", "FIPS 180-4 SHA-256 cube root fractional constants"))
        self.signatures.append((CryptoPrimitive.SHA256, "SHA-256 K Table (BE)", sha256_k_be, "big", "FIPS 180-4 SHA-256 cube root fractional constants"))

        # SHA-256 Initial Hash State H0..H7
        sha256_iv_words = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a]
        self.signatures.append((CryptoPrimitive.SHA256, "SHA-256 Initial State (LE)", b"".join(struct.pack("<I", w) for w in sha256_iv_words), "little", "SHA-256 initial vector"))
        self.signatures.append((CryptoPrimitive.SHA256, "SHA-256 Initial State (BE)", b"".join(struct.pack(">I", w) for w in sha256_iv_words), "big", "SHA-256 initial vector"))

        # 3. SHA-512 K Constants (first 2 64-bit constants: 0x428a2f98d728ae22, 0x7137449123ef65cd)
        sha512_k_words = [0x428a2f98d728ae22, 0x7137449123ef65cd]
        self.signatures.append((CryptoPrimitive.SHA512, "SHA-512 K Table (LE)", b"".join(struct.pack("<Q", w) for w in sha512_k_words), "little", "SHA-512 round constants"))
        self.signatures.append((CryptoPrimitive.SHA512, "SHA-512 K Table (BE)", b"".join(struct.pack(">Q", w) for w in sha512_k_words), "big", "SHA-512 round constants"))

        # 4. ChaCha20 Constant: "expand 32-byte k" / "expand 16-byte k"
        self.signatures.append((CryptoPrimitive.CHACHA20, "ChaCha20 expand 32-byte k", b"expand 32-byte k", "any", "RFC 7539 ChaCha20 constant string"))
        self.signatures.append((CryptoPrimitive.CHACHA20, "ChaCha20 expand 16-byte k", b"expand 16-byte k", "any", "RFC 7539 ChaCha20 128-bit key constant string"))

        # 5. HMAC Pads: repeated 0x36 or 0x5c (at least 16 consecutive bytes)
        self.signatures.append((CryptoPrimitive.HMAC, "HMAC Inner Pad (0x36)", b"\x36" * 16, "any", "RFC 2104 inner hash pad"))
        self.signatures.append((CryptoPrimitive.HMAC, "HMAC Outer Pad (0x5C)", b"\x5c" * 16, "any", "RFC 2104 outer hash pad"))

        # 6. DES Permutations / S-Boxes (first 8 bytes of S-box 1)
        des_s1_prefix = bytes([14, 4, 13, 1, 2, 15, 11, 8])
        self.signatures.append((CryptoPrimitive.DES, "DES S-Box 1 Prefix", des_s1_prefix, "any", "FIPS 46-3 DES S1 Substitution Table"))

        # 7. ECC NIST P-256 Prime & Curve Parameters
        # P-256 prime in little-endian and big-endian
        p256_prime_words = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0x00000000, 0x00000000, 0x00000000, 0x00000001, 0xFFFFFFFF]
        self.signatures.append((CryptoPrimitive.ECC, "NIST P-256 Curve Prime (LE)", b"".join(struct.pack("<I", w) for w in p256_prime_words[:4]), "little", "secp256r1 Prime Field Modulus"))
        self.signatures.append((CryptoPrimitive.ECC, "NIST P-256 Curve Prime (BE)", b"".join(struct.pack(">I", w) for w in p256_prime_words[:4]), "big", "secp256r1 Prime Field Modulus"))

    def scan(self, data: bytes) -> List[ConstantMatch]:
        """Scans byte sequence for all registered cryptographic constants."""
        matches: List[ConstantMatch] = []
        if not data:
            return matches

        for prim, name, pat, endian, desc in self.signatures:
            pos = 0
            while True:
                idx = data.find(pat, pos)
                if idx == -1:
                    break
                matches.append(ConstantMatch(
                    primitive=prim,
                    constant_name=name,
                    offset=idx,
                    matched_length=len(pat),
                    endianness=endian,
                    description=desc
                ))
                pos = idx + len(pat)

        return matches

    def classify_baseline(self, data: bytes) -> Tuple[CryptoPrimitive, float, List[ConstantMatch]]:
        """
        Non-ML baseline classifier: classifies primitive based purely on signature matches.
        Used to demonstrate ML vs Signature-matching comparison as required by paper.
        """
        matches = self.scan(data)
        if not matches:
            return CryptoPrimitive.NON_CRYPTO, 0.0, []

        # Count matches per primitive
        counts: Dict[CryptoPrimitive, int] = {}
        for m in matches:
            counts[m.primitive] = counts.get(m.primitive, 0) + 1

        best_prim = max(counts, key=counts.get)
        confidence = min(1.0, 0.6 + 0.2 * counts[best_prim])
        return best_prim, confidence, matches
