"""
CryptoScope Multi-Architecture Capstone Disassembly Engine
Provides unified instruction disassembly across x86-64, ARM32 (ARM/Thumb), ARM64, MIPS, and RISC-V 64.
"""

from typing import List, Dict, Optional, Any, Tuple
import capstone
from backend.app.datasets.manifest import TargetISA

class DisassembledInstruction:
    def __init__(self, cs_insn: capstone.CsInsn, isa: TargetISA):
        self.address: int = cs_insn.address
        self.size: int = cs_insn.size
        self.mnemonic: str = cs_insn.mnemonic.lower()
        self.op_str: str = cs_insn.op_str
        self.bytes: bytes = bytes(cs_insn.bytes)
        self.hex_bytes: str = cs_insn.bytes.hex()
        self.isa: TargetISA = isa

        # Operand and register analysis
        self.regs_read: List[str] = [cs_insn.reg_name(r) for r in cs_insn.regs_read]
        self.regs_write: List[str] = [cs_insn.reg_name(r) for r in cs_insn.regs_write]
        self.groups: List[int] = list(cs_insn.groups)
        self.operands: List[Dict[str, Any]] = []

        if hasattr(cs_insn, "operands"):
            for op in cs_insn.operands:
                op_data = {"type": op.type}
                if op.type == capstone.CS_OP_IMM:
                    op_data["imm"] = op.imm
                elif op.type == capstone.CS_OP_REG:
                    op_data["reg"] = cs_insn.reg_name(op.reg)
                elif op.type == capstone.CS_OP_MEM:
                    mem_data = {
                        "base": cs_insn.reg_name(op.mem.base) if op.mem.base != 0 else None,
                        "index": cs_insn.reg_name(op.mem.index) if op.mem.index != 0 else None,
                        "disp": op.mem.disp
                    }
                    op_data["mem"] = mem_data
                self.operands.append(op_data)

    def is_call(self) -> bool:
        if capstone.CS_GRP_CALL in self.groups:
            return True
        return self.mnemonic in {"call", "bl", "blx", "jal", "jalr"}

    def is_ret(self) -> bool:
        if capstone.CS_GRP_RET in self.groups:
            return True
        return self.mnemonic in {"ret", "bx", "jr"}

    def is_branch(self) -> bool:
        if capstone.CS_GRP_JUMP in self.groups:
            return True
        return self.mnemonic.startswith("b") or self.mnemonic.startswith("j")

    def is_cond_branch(self) -> bool:
        if not self.is_branch():
            return False
        uncond = {"jmp", "b", "j", "jr"}
        return self.mnemonic not in uncond

class MultiIsaDisassembler:
    def __init__(self, isa: TargetISA, endianness: str = "little", thumb: bool = False):
        self.isa = isa
        self.endianness = endianness
        self.thumb = thumb
        self.cs = self._init_capstone()

    def _init_capstone(self) -> capstone.Cs:
        if self.isa == TargetISA.X86_64:
            cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        elif self.isa == TargetISA.ARM32:
            mode = capstone.CS_MODE_THUMB if self.thumb else capstone.CS_MODE_ARM
            cs = capstone.Cs(capstone.CS_ARCH_ARM, mode)
        elif self.isa == TargetISA.ARM64:
            cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
        elif self.isa in [TargetISA.MIPS32_LE, TargetISA.MIPS32_BE]:
            mode = capstone.CS_MODE_MIPS32
            if self.endianness == "big" or self.isa == TargetISA.MIPS32_BE:
                mode |= capstone.CS_MODE_BIG_ENDIAN
            else:
                mode |= capstone.CS_MODE_LITTLE_ENDIAN
            cs = capstone.Cs(capstone.CS_ARCH_MIPS, mode)
        elif self.isa == TargetISA.RISCV64:
            cs = capstone.Cs(capstone.CS_ARCH_RISCV, capstone.CS_MODE_RISCV64)
        else:
            cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

        cs.detail = True
        return cs

    def disassemble(self, code: bytes, base_address: int) -> List[DisassembledInstruction]:
        insns = []
        try:
            for insn in self.cs.disasm(code, base_address):
                insns.append(DisassembledInstruction(insn, self.isa))
        except Exception:
            pass
        return insns
