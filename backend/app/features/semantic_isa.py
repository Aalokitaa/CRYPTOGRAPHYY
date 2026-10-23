"""
CryptoScope Semantic Instruction Normalizer
Paper Table I, Section III-D:
Translates architecture-specific mnemonics across x86-64, ARM32, ARM64, MIPS, and RISC-V 64
into 14 architecture-neutral canonical semantic instruction classes.
Enables cross-architecture model generalization.
"""

from enum import Enum
from typing import Dict, Set

class SemanticInsnClass(str, Enum):
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    AND_OR_XOR = "AND_OR_XOR"
    SHL_SHR_ROT = "SHL_SHR_ROT"
    LOAD = "LOAD"
    STORE = "STORE"
    BRANCH_COND = "BRANCH_COND"
    BRANCH_UNCOND = "BRANCH_UNCOND"
    CALL = "CALL"
    RET = "RET"
    MOV = "MOV"
    CMP = "CMP"
    OTHER = "OTHER"

# Canonical mappings per architecture
X86_SEMANTIC_MAP: Dict[str, SemanticInsnClass] = {
    # ADD
    "add": SemanticInsnClass.ADD, "adc": SemanticInsnClass.ADD, "inc": SemanticInsnClass.ADD,
    "paddb": SemanticInsnClass.ADD, "paddw": SemanticInsnClass.ADD, "paddd": SemanticInsnClass.ADD, "paddq": SemanticInsnClass.ADD,
    "vaddps": SemanticInsnClass.ADD, "vaddpd": SemanticInsnClass.ADD, "xadd": SemanticInsnClass.ADD,
    # SUB
    "sub": SemanticInsnClass.SUB, "sbb": SemanticInsnClass.SUB, "dec": SemanticInsnClass.SUB,
    "psubb": SemanticInsnClass.SUB, "psubw": SemanticInsnClass.SUB, "psubd": SemanticInsnClass.SUB,
    # MUL
    "mul": SemanticInsnClass.MUL, "imul": SemanticInsnClass.MUL, "pmullw": SemanticInsnClass.MUL, "pmulld": SemanticInsnClass.MUL,
    # AND/OR/XOR
    "and": SemanticInsnClass.AND_OR_XOR, "pand": SemanticInsnClass.AND_OR_XOR,
    "or": SemanticInsnClass.AND_OR_XOR, "por": SemanticInsnClass.AND_OR_XOR,
    "xor": SemanticInsnClass.AND_OR_XOR, "pxor": SemanticInsnClass.AND_OR_XOR, "vxorps": SemanticInsnClass.AND_OR_XOR,
    "not": SemanticInsnClass.AND_OR_XOR, "andn": SemanticInsnClass.AND_OR_XOR,
    # SHIFT/ROTATE
    "shl": SemanticInsnClass.SHL_SHR_ROT, "shr": SemanticInsnClass.SHL_SHR_ROT,
    "sal": SemanticInsnClass.SHL_SHR_ROT, "sar": SemanticInsnClass.SHL_SHR_ROT,
    "rol": SemanticInsnClass.SHL_SHR_ROT, "ror": SemanticInsnClass.SHL_SHR_ROT,
    "pslld": SemanticInsnClass.SHL_SHR_ROT, "psrld": SemanticInsnClass.SHL_SHR_ROT,
    # LOAD/STORE
    "mov": SemanticInsnClass.MOV, "movzx": SemanticInsnClass.MOV, "movsx": SemanticInsnClass.MOV,
    "lea": SemanticInsnClass.LOAD, "push": SemanticInsnClass.STORE, "pop": SemanticInsnClass.LOAD,
    # BRANCH
    "jmp": SemanticInsnClass.BRANCH_UNCOND,
    "je": SemanticInsnClass.BRANCH_COND, "jne": SemanticInsnClass.BRANCH_COND,
    "jl": SemanticInsnClass.BRANCH_COND, "jle": SemanticInsnClass.BRANCH_COND,
    "jg": SemanticInsnClass.BRANCH_COND, "jge": SemanticInsnClass.BRANCH_COND,
    "jb": SemanticInsnClass.BRANCH_COND, "jbe": SemanticInsnClass.BRANCH_COND,
    "ja": SemanticInsnClass.BRANCH_COND, "jae": SemanticInsnClass.BRANCH_COND,
    "js": SemanticInsnClass.BRANCH_COND, "jns": SemanticInsnClass.BRANCH_COND,
    # CALL/RET
    "call": SemanticInsnClass.CALL, "ret": SemanticInsnClass.RET, "retq": SemanticInsnClass.RET,
    # CMP
    "cmp": SemanticInsnClass.CMP, "test": SemanticInsnClass.CMP
}

ARM_SEMANTIC_MAP: Dict[str, SemanticInsnClass] = {
    # ADD
    "add": SemanticInsnClass.ADD, "adds": SemanticInsnClass.ADD, "adc": SemanticInsnClass.ADD, "adcs": SemanticInsnClass.ADD,
    # SUB
    "sub": SemanticInsnClass.SUB, "subs": SemanticInsnClass.SUB, "sbc": SemanticInsnClass.SUB, "rsb": SemanticInsnClass.SUB,
    # MUL
    "mul": SemanticInsnClass.MUL, "muls": SemanticInsnClass.MUL, "mla": SemanticInsnClass.MUL, "mls": SemanticInsnClass.MUL,
    "smull": SemanticInsnClass.MUL, "umull": SemanticInsnClass.MUL,
    # AND/OR/XOR
    "and": SemanticInsnClass.AND_OR_XOR, "ands": SemanticInsnClass.AND_OR_XOR,
    "orr": SemanticInsnClass.AND_OR_XOR, "orrs": SemanticInsnClass.AND_OR_XOR, "orn": SemanticInsnClass.AND_OR_XOR,
    "eor": SemanticInsnClass.AND_OR_XOR, "eors": SemanticInsnClass.AND_OR_XOR,
    "bic": SemanticInsnClass.AND_OR_XOR, "mvn": SemanticInsnClass.AND_OR_XOR,
    # SHIFT/ROTATE
    "lsl": SemanticInsnClass.SHL_SHR_ROT, "lsr": SemanticInsnClass.SHL_SHR_ROT,
    "asr": SemanticInsnClass.SHL_SHR_ROT, "ror": SemanticInsnClass.SHL_SHR_ROT,
    # LOAD/STORE
    "ldr": SemanticInsnClass.LOAD, "ldrb": SemanticInsnClass.LOAD, "ldrh": SemanticInsnClass.LOAD, "ldrd": SemanticInsnClass.LOAD,
    "str": SemanticInsnClass.STORE, "strb": SemanticInsnClass.STORE, "strh": SemanticInsnClass.STORE, "strd": SemanticInsnClass.STORE,
    "push": SemanticInsnClass.STORE, "pop": SemanticInsnClass.LOAD,
    # MOV
    "mov": SemanticInsnClass.MOV, "movs": SemanticInsnClass.MOV, "movw": SemanticInsnClass.MOV, "movt": SemanticInsnClass.MOV,
    # BRANCH
    "b": SemanticInsnClass.BRANCH_UNCOND, "bl": SemanticInsnClass.CALL, "blx": SemanticInsnClass.CALL, "bx": SemanticInsnClass.RET,
    "beq": SemanticInsnClass.BRANCH_COND, "bne": SemanticInsnClass.BRANCH_COND,
    "bcs": SemanticInsnClass.BRANCH_COND, "bcc": SemanticInsnClass.BRANCH_COND,
    "bmi": SemanticInsnClass.BRANCH_COND, "bpl": SemanticInsnClass.BRANCH_COND,
    "bvs": SemanticInsnClass.BRANCH_COND, "bvc": SemanticInsnClass.BRANCH_COND,
    "bhi": SemanticInsnClass.BRANCH_COND, "bls": SemanticInsnClass.BRANCH_COND,
    "bge": SemanticInsnClass.BRANCH_COND, "blt": SemanticInsnClass.BRANCH_COND,
    "bgt": SemanticInsnClass.BRANCH_COND, "ble": SemanticInsnClass.BRANCH_COND,
    # CMP
    "cmp": SemanticInsnClass.CMP, "cmn": SemanticInsnClass.CMP, "tst": SemanticInsnClass.CMP, "teq": SemanticInsnClass.CMP
}

ARM64_SEMANTIC_MAP: Dict[str, SemanticInsnClass] = {
    # ADD
    "add": SemanticInsnClass.ADD, "adds": SemanticInsnClass.ADD, "adc": SemanticInsnClass.ADD, "adr": SemanticInsnClass.ADD, "adrp": SemanticInsnClass.ADD,
    # SUB
    "sub": SemanticInsnClass.SUB, "subs": SemanticInsnClass.SUB, "sbc": SemanticInsnClass.SUB, "neg": SemanticInsnClass.SUB,
    # MUL
    "mul": SemanticInsnClass.MUL, "smulh": SemanticInsnClass.MUL, "umulh": SemanticInsnClass.MUL, "madd": SemanticInsnClass.MUL, "msub": SemanticInsnClass.MUL,
    # AND/OR/XOR
    "and": SemanticInsnClass.AND_OR_XOR, "ands": SemanticInsnClass.AND_OR_XOR,
    "orr": SemanticInsnClass.AND_OR_XOR, "orn": SemanticInsnClass.AND_OR_XOR,
    "eor": SemanticInsnClass.AND_OR_XOR, "eon": SemanticInsnClass.AND_OR_XOR,
    "mvn": SemanticInsnClass.AND_OR_XOR, "bic": SemanticInsnClass.AND_OR_XOR,
    # SHIFT/ROTATE
    "lsl": SemanticInsnClass.SHL_SHR_ROT, "lsr": SemanticInsnClass.SHL_SHR_ROT,
    "asr": SemanticInsnClass.SHL_SHR_ROT, "ror": SemanticInsnClass.SHL_SHR_ROT,
    # LOAD/STORE
    "ldr": SemanticInsnClass.LOAD, "ldrb": SemanticInsnClass.LOAD, "ldrh": SemanticInsnClass.LOAD, "ldp": SemanticInsnClass.LOAD,
    "str": SemanticInsnClass.STORE, "strb": SemanticInsnClass.STORE, "strh": SemanticInsnClass.STORE, "stp": SemanticInsnClass.STORE,
    # MOV
    "mov": SemanticInsnClass.MOV, "movz": SemanticInsnClass.MOV, "movk": SemanticInsnClass.MOV, "movn": SemanticInsnClass.MOV,
    # BRANCH
    "b": SemanticInsnClass.BRANCH_UNCOND, "br": SemanticInsnClass.BRANCH_UNCOND,
    "bl": SemanticInsnClass.CALL, "blr": SemanticInsnClass.CALL, "ret": SemanticInsnClass.RET,
    "b.eq": SemanticInsnClass.BRANCH_COND, "b.ne": SemanticInsnClass.BRANCH_COND,
    "b.cs": SemanticInsnClass.BRANCH_COND, "b.cc": SemanticInsnClass.BRANCH_COND,
    "b.mi": SemanticInsnClass.BRANCH_COND, "b.pl": SemanticInsnClass.BRANCH_COND,
    "b.vs": SemanticInsnClass.BRANCH_COND, "b.vc": SemanticInsnClass.BRANCH_COND,
    "b.hi": SemanticInsnClass.BRANCH_COND, "b.ls": SemanticInsnClass.BRANCH_COND,
    "b.ge": SemanticInsnClass.BRANCH_COND, "b.lt": SemanticInsnClass.BRANCH_COND,
    "b.gt": SemanticInsnClass.BRANCH_COND, "b.le": SemanticInsnClass.BRANCH_COND,
    "cbz": SemanticInsnClass.BRANCH_COND, "cbnz": SemanticInsnClass.BRANCH_COND,
    "tbz": SemanticInsnClass.BRANCH_COND, "tbnz": SemanticInsnClass.BRANCH_COND,
    # CMP
    "cmp": SemanticInsnClass.CMP, "cmn": SemanticInsnClass.CMP, "tst": SemanticInsnClass.CMP
}

MIPS_SEMANTIC_MAP: Dict[str, SemanticInsnClass] = {
    # ADD
    "add": SemanticInsnClass.ADD, "addu": SemanticInsnClass.ADD, "addi": SemanticInsnClass.ADD, "addiu": SemanticInsnClass.ADD,
    # SUB
    "sub": SemanticInsnClass.SUB, "subu": SemanticInsnClass.SUB,
    # MUL
    "mult": SemanticInsnClass.MUL, "multu": SemanticInsnClass.MUL, "mul": SemanticInsnClass.MUL,
    # AND/OR/XOR
    "and": SemanticInsnClass.AND_OR_XOR, "andi": SemanticInsnClass.AND_OR_XOR,
    "or": SemanticInsnClass.AND_OR_XOR, "ori": SemanticInsnClass.AND_OR_XOR,
    "xor": SemanticInsnClass.AND_OR_XOR, "xori": SemanticInsnClass.AND_OR_XOR, "nor": SemanticInsnClass.AND_OR_XOR,
    # SHIFT/ROTATE
    "sll": SemanticInsnClass.SHL_SHR_ROT, "srl": SemanticInsnClass.SHL_SHR_ROT, "sra": SemanticInsnClass.SHL_SHR_ROT,
    "rotr": SemanticInsnClass.SHL_SHR_ROT, "rotrv": SemanticInsnClass.SHL_SHR_ROT,
    # LOAD/STORE
    "lb": SemanticInsnClass.LOAD, "lbu": SemanticInsnClass.LOAD, "lh": SemanticInsnClass.LOAD, "lhu": SemanticInsnClass.LOAD,
    "lw": SemanticInsnClass.LOAD, "lwl": SemanticInsnClass.LOAD, "lwr": SemanticInsnClass.LOAD,
    "sb": SemanticInsnClass.STORE, "sh": SemanticInsnClass.STORE, "sw": SemanticInsnClass.STORE,
    # MOV
    "move": SemanticInsnClass.MOV, "li": SemanticInsnClass.MOV, "lui": SemanticInsnClass.MOV,
    # BRANCH
    "j": SemanticInsnClass.BRANCH_UNCOND, "jr": SemanticInsnClass.RET, "jal": SemanticInsnClass.CALL, "jalr": SemanticInsnClass.CALL,
    "beq": SemanticInsnClass.BRANCH_COND, "bne": SemanticInsnClass.BRANCH_COND,
    "blez": SemanticInsnClass.BRANCH_COND, "bgtz": SemanticInsnClass.BRANCH_COND,
    "bltz": SemanticInsnClass.BRANCH_COND, "bgez": SemanticInsnClass.BRANCH_COND,
    # CMP
    "slt": SemanticInsnClass.CMP, "slti": SemanticInsnClass.CMP, "sltu": SemanticInsnClass.CMP
}

RISCV_SEMANTIC_MAP: Dict[str, SemanticInsnClass] = {
    # ADD
    "add": SemanticInsnClass.ADD, "addi": SemanticInsnClass.ADD, "addw": SemanticInsnClass.ADD, "addiw": SemanticInsnClass.ADD, "auipc": SemanticInsnClass.ADD,
    # SUB
    "sub": SemanticInsnClass.SUB, "subw": SemanticInsnClass.SUB,
    # MUL
    "mul": SemanticInsnClass.MUL, "mulw": SemanticInsnClass.MUL, "mulh": SemanticInsnClass.MUL,
    # AND/OR/XOR
    "and": SemanticInsnClass.AND_OR_XOR, "andi": SemanticInsnClass.AND_OR_XOR,
    "or": SemanticInsnClass.AND_OR_XOR, "ori": SemanticInsnClass.AND_OR_XOR,
    "xor": SemanticInsnClass.AND_OR_XOR, "xori": SemanticInsnClass.AND_OR_XOR,
    # SHIFT
    "sll": SemanticInsnClass.SHL_SHR_ROT, "slli": SemanticInsnClass.SHL_SHR_ROT,
    "srl": SemanticInsnClass.SHL_SHR_ROT, "srli": SemanticInsnClass.SHL_SHR_ROT,
    "sra": SemanticInsnClass.SHL_SHR_ROT, "srai": SemanticInsnClass.SHL_SHR_ROT,
    # LOAD/STORE
    "lb": SemanticInsnClass.LOAD, "lbu": SemanticInsnClass.LOAD, "lh": SemanticInsnClass.LOAD, "lhu": SemanticInsnClass.LOAD,
    "lw": SemanticInsnClass.LOAD, "lwu": SemanticInsnClass.LOAD, "ld": SemanticInsnClass.LOAD,
    "sb": SemanticInsnClass.STORE, "sh": SemanticInsnClass.STORE, "sw": SemanticInsnClass.STORE, "sd": SemanticInsnClass.STORE,
    # MOV
    "mv": SemanticInsnClass.MOV, "li": SemanticInsnClass.MOV, "lui": SemanticInsnClass.MOV,
    # BRANCH
    "jal": SemanticInsnClass.CALL, "jalr": SemanticInsnClass.CALL,
    "beq": SemanticInsnClass.BRANCH_COND, "bne": SemanticInsnClass.BRANCH_COND,
    "blt": SemanticInsnClass.BRANCH_COND, "bge": SemanticInsnClass.BRANCH_COND,
    "bltu": SemanticInsnClass.BRANCH_COND, "bgeu": SemanticInsnClass.BRANCH_COND,
    "ret": SemanticInsnClass.RET, "j": SemanticInsnClass.BRANCH_UNCOND, "jr": SemanticInsnClass.BRANCH_UNCOND,
    # CMP
    "slt": SemanticInsnClass.CMP, "slti": SemanticInsnClass.CMP, "sltu": SemanticInsnClass.CMP
}

def map_mnemonic_to_semantic(mnemonic: str) -> SemanticInsnClass:
    m = mnemonic.lower().strip()
    # Check direct maps
    if m in X86_SEMANTIC_MAP: return X86_SEMANTIC_MAP[m]
    if m in ARM_SEMANTIC_MAP: return ARM_SEMANTIC_MAP[m]
    if m in ARM64_SEMANTIC_MAP: return ARM64_SEMANTIC_MAP[m]
    if m in MIPS_SEMANTIC_MAP: return MIPS_SEMANTIC_MAP[m]
    if m in RISCV_SEMANTIC_MAP: return RISCV_SEMANTIC_MAP[m]

    # Heuristic prefix/suffix matching
    if m.startswith("add") or m.startswith("vadd") or m.startswith("padd"):
        return SemanticInsnClass.ADD
    if m.startswith("sub") or m.startswith("vsub") or m.startswith("psub"):
        return SemanticInsnClass.SUB
    if m.startswith("mul") or m.startswith("vmul"):
        return SemanticInsnClass.MUL
    if m.startswith("xor") or m.startswith("pxor") or m.startswith("eor"):
        return SemanticInsnClass.AND_OR_XOR
    if m.startswith("and") or m.startswith("orr"):
        return SemanticInsnClass.AND_OR_XOR
    if m.startswith("sh") or m.startswith("sll") or m.startswith("srl") or m.startswith("ror"):
        return SemanticInsnClass.SHL_SHR_ROT
    if m.startswith("ld") or m.startswith("load"):
        return SemanticInsnClass.LOAD
    if m.startswith("st") or m.startswith("store"):
        return SemanticInsnClass.STORE
    if m.startswith("b") or m.startswith("j"):
        return SemanticInsnClass.BRANCH_COND

    return SemanticInsnClass.OTHER
