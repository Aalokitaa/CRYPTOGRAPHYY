"""
CryptoScope Dataset Manifest Models & Schemas
Implements paper Section III-B, IV-B/D ground-truth tracking and inlining management.
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import datetime

class CryptoFamily(str, Enum):
    SYMMETRIC_CIPHER = "Symmetric Cipher"
    ASYMMETRIC_CIPHER = "Asymmetric Cipher"
    HASH = "Hash"
    MAC = "MAC"
    NON_CRYPTO = "Non-crypto"

class CryptoPrimitive(str, Enum):
    AES = "AES"
    DES = "DES/3DES"
    RSA = "RSA"
    ECC = "ECC"
    SHA256 = "SHA-256"
    SHA512 = "SHA-512"
    HMAC = "HMAC"
    CHACHA20 = "ChaCha20"
    NON_CRYPTO = "Non-crypto"

class TargetISA(str, Enum):
    X86_64 = "x86-64"
    ARM32 = "ARM32"
    ARM64 = "ARM64"
    MIPS32_LE = "MIPS32-LE"
    MIPS32_BE = "MIPS32-BE"
    RISCV64 = "RISC-V 64"

class OptLevel(str, Enum):
    O0 = "O0"
    O1 = "O1"
    O2 = "O2"
    O3 = "O3"
    OS = "Os"

class FunctionLabel(BaseModel):
    id: str = Field(..., description="Unique function identifier within binary")
    name: str = Field(..., description="Original symbol name before stripping")
    address: int = Field(..., description="Virtual address or offset in binary")
    size: int = Field(..., description="Function size in bytes")
    is_crypto: bool = Field(..., description="Level 1: True if cryptographic")
    family: CryptoFamily = Field(..., description="Level 2: Cryptographic family")
    primitive: CryptoPrimitive = Field(..., description="Level 3: Specific cryptographic primitive")
    source_program: str = Field(..., description="Source C file name")
    implementation: str = Field(..., description="Specific implementation variant")
    isa: TargetISA = Field(..., description="Architecture")
    compiler: str = Field(..., description="Compiler used (gcc, clang)")
    opt_level: OptLevel = Field(..., description="Optimization level")
    is_inlined: bool = Field(default=False, description="Whether compiler inlined this function")
    dwarf_found: bool = Field(default=True, description="Whether DWARF/symbol was present")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BinaryManifest(BaseModel):
    binary_id: str
    filename: str
    original_path: str
    stripped_path: str
    isa: TargetISA
    endianness: str = "little"  # little or big
    compiler: str
    opt_level: OptLevel
    is_stripped: bool = True
    sha256: str
    file_size: int
    functions: List[FunctionLabel] = Field(default_factory=list)
    inlined_functions: List[str] = Field(default_factory=list)

class DatasetManifest(BaseModel):
    version: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    description: str
    total_binaries: int
    total_functions: int
    binaries: List[BinaryManifest] = Field(default_factory=list)
    class_distribution: Dict[str, int] = Field(default_factory=dict)
    isa_distribution: Dict[str, int] = Field(default_factory=dict)
    opt_distribution: Dict[str, int] = Field(default_factory=dict)
    compiler_distribution: Dict[str, int] = Field(default_factory=dict)
