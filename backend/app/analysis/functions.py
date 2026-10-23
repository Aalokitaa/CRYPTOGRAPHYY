"""
CryptoScope Symbol-less Function Boundary Recovery & Basic Block Extraction
Paper Section III-C:
- Pure black-box analysis (ignores symbols, debug info, function names)
- Multi-architecture prologue signature detection
- Recursive descent and call-target harvesting
- Basic block partitioning and control flow termination
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from backend.app.datasets.manifest import TargetISA
from backend.app.analysis.disassembler import MultiIsaDisassembler, DisassembledInstruction

class BasicBlock:
    def __init__(self, block_id: str, start_addr: int, instructions: List[DisassembledInstruction]):
        self.block_id: str = block_id
        self.start_addr: int = start_addr
        self.instructions: List[DisassembledInstruction] = instructions
        self.end_addr: int = instructions[-1].address + instructions[-1].size if instructions else start_addr
        self.successors: List[int] = []
        self.predecessors: List[int] = []

    @property
    def size(self) -> int:
        return self.end_addr - self.start_addr

    @property
    def terminator(self) -> Optional[DisassembledInstruction]:
        return self.instructions[-1] if self.instructions else None

class RecoveredFunction:
    def __init__(self, fn_id: str, entry_addr: int, isa: TargetISA):
        self.id: str = fn_id
        self.entry_addr: int = entry_addr
        self.isa: TargetISA = isa
        self.basic_blocks: List[BasicBlock] = []
        self.instructions: List[DisassembledInstruction] = []
        self.callees: Set[int] = set()
        self.callers: Set[int] = set()

    @property
    def size(self) -> int:
        if not self.instructions:
            return 0
        return max(insn.address + insn.size for insn in self.instructions) - self.entry_addr

    @property
    def end_addr(self) -> int:
        return self.entry_addr + self.size

# Architecture prologue patterns
PROLOGUE_PATTERNS = {
    TargetISA.X86_64: [
        b'\x55\x48\x89\xe5',     # push rbp; mov rbp, rsp
        b'\x48\x83\xec',         # sub rsp, imm
        b'\x55\x89\xe5',         # push ebp; mov ebp, esp
        b'\x53\x41\x54'          # push rbx; push r12
    ],
    TargetISA.ARM32: [
        b'\x04\xe0\x2d\xe5',     # str lr, [sp, #-4]!
        b'\x04\xb0\x2d\xe5',     # str r11, [sp, #-4]!
        b'\x2d\xe9'              # push {..., lr} (Thumb/ARM)
    ],
    TargetISA.ARM64: [
        b'\xfd\x7b\xbf\xa9',     # stp x29, x30, [sp, #-16]!
        b'\xfd\x03\x00\x91'      # mov x29, sp
    ],
    TargetISA.MIPS32_LE: [
        b'\xe0\xff\xbd\x27',     # addiu $sp, $sp, -32 (LE)
        b'\x1c\x00\xbf\xaf'      # sw $ra, 28($sp)
    ],
    TargetISA.MIPS32_BE: [
        b'\x27\xbd\xff\xe0',     # addiu $sp, $sp, -32 (BE)
        b'\xaf\xbf\x00\x1c'      # sw $ra, 28($sp)
    ],
    TargetISA.RISCV64: [
        b'\x13\x01\x01\xff',     # addi sp, sp, -16
        b'\x23\x30\x11\x00'      # sd ra, 0(sp)
    ]
}

class FunctionBoundaryRecovery:
    def __init__(self, isa: TargetISA, endianness: str = "little", thumb: bool = False):
        self.isa = isa
        self.endianness = endianness
        self.thumb = thumb
        self.disasm = MultiIsaDisassembler(isa, endianness, thumb)

    def scan_prologues(self, code: bytes, base_vaddr: int) -> Set[int]:
        """Scans code for standard architectural prologue byte signatures."""
        entries = set()
        pats = PROLOGUE_PATTERNS.get(self.isa, [])
        for pat in pats:
            start = 0
            while True:
                idx = code.find(pat, start)
                if idx == -1:
                    break
                # Only align to instruction word boundary
                step = 2 if (self.isa == TargetISA.ARM32 and self.thumb) else 4 if self.isa != TargetISA.X86_64 else 1
                if idx % step == 0:
                    entries.add(base_vaddr + idx)
                start = idx + 1
        return entries

    def harvest_call_targets(self, insns: List[DisassembledInstruction], code_start: int, code_end: int) -> Set[int]:
        """Extracts direct call destinations as confirmed function entry points."""
        targets = set()
        for insn in insns:
            if insn.is_call():
                for op in insn.operands:
                    if op.get("type") == 2 and "imm" in op: # CS_OP_IMM
                        target = op["imm"]
                        if code_start <= target < code_end:
                            targets.add(target)
        return targets

    def partition_basic_blocks(self, insns: List[DisassembledInstruction], fn_id: str) -> List[BasicBlock]:
        """Partitions a continuous sequence of instructions into basic blocks."""
        if not insns:
            return []

        insn_by_addr = {insn.address: insn for insn in insns}
        leaders = {insns[0].address}

        # Step 1: Identify leader addresses
        for i, insn in enumerate(insns):
            if insn.is_branch() or insn.is_ret():
                # Target of branch is leader
                for op in insn.operands:
                    if op.get("type") == 2 and "imm" in op:
                        target = op["imm"]
                        if target in insn_by_addr:
                            leaders.add(target)
                # Next instruction after branch is leader
                if i + 1 < len(insns):
                    leaders.add(insns[i + 1].address)

        # Step 2: Chunk into basic blocks
        blocks = []
        cur_block_insns = []
        block_idx = 0

        for insn in insns:
            if insn.address in leaders and cur_block_insns:
                b = BasicBlock(f"{fn_id}_bb_{block_idx}", cur_block_insns[0].address, cur_block_insns)
                blocks.append(b)
                block_idx += 1
                cur_block_insns = []

            cur_block_insns.append(insn)

        if cur_block_insns:
            b = BasicBlock(f"{fn_id}_bb_{block_idx}", cur_block_insns[0].address, cur_block_insns)
            blocks.append(b)

        # Step 3: Resolve successor and predecessor edges
        bb_map = {b.start_addr: b for b in blocks}
        for b in blocks:
            term = b.terminator
            if not term:
                continue

            if term.is_ret():
                pass # Function exit, no intra-function successors
            elif term.is_cond_branch():
                # Branch taken target + fallthrough
                for op in term.operands:
                    if op.get("type") == 2 and "imm" in op:
                        tgt = op["imm"]
                        if tgt in bb_map:
                            b.successors.append(tgt)
                            bb_map[tgt].predecessors.append(b.start_addr)
                # Fallthrough
                fall_addr = term.address + term.size
                if fall_addr in bb_map:
                    b.successors.append(fall_addr)
                    bb_map[fall_addr].predecessors.append(b.start_addr)
            elif term.is_branch(): # Unconditional jump
                for op in term.operands:
                    if op.get("type") == 2 and "imm" in op:
                        tgt = op["imm"]
                        if tgt in bb_map:
                            b.successors.append(tgt)
                            bb_map[tgt].predecessors.append(b.start_addr)
            else:
                # Normal instruction or call fallthrough
                fall_addr = term.address + term.size
                if fall_addr in bb_map:
                    b.successors.append(fall_addr)
                    bb_map[fall_addr].predecessors.append(b.start_addr)

        return blocks

    def recover_functions(self, code: bytes, base_vaddr: int, entrypoint: Optional[int] = None) -> List[RecoveredFunction]:
        """
        Full symbol-less recovery:
        1. Linear sweep disassembly to establish instruction stream
        2. Prologue + Call-target harvesting + entrypoint initialization
        3. Delimiting function boundaries between consecutive entry points
        4. Basic block extraction
        """
        all_insns = self.disasm.disassemble(code, base_vaddr)
        if not all_insns:
            return []

        code_start = base_vaddr
        code_end = base_vaddr + len(code)

        # Discover entry points
        entry_points = self.scan_prologues(code, base_vaddr)
        call_targets = self.harvest_call_targets(all_insns, code_start, code_end)
        entry_points.update(call_targets)

        if entrypoint and code_start <= entrypoint < code_end:
            entry_points.add(entrypoint)

        # Ensure first instruction is an entry point if nothing else discovered
        if not entry_points:
            entry_points.add(all_insns[0].address)

        sorted_entries = sorted(list(entry_points))
        entry_set = set(sorted_entries)

        # Partition instructions into functions
        functions: List[RecoveredFunction] = []
        cur_fn: Optional[RecoveredFunction] = None

        insn_idx = 0
        for entry in sorted_entries:
            fn_id = f"fn_{hex(entry)}"
            fn = RecoveredFunction(fn_id, entry, self.isa)

            # Collect instructions until next entry or end of code or sequence of rets
            fn_insns = []
            while insn_idx < len(all_insns):
                insn = all_insns[insn_idx]
                if insn.address < entry:
                    insn_idx += 1
                    continue
                # If we've hit the next function's entry point, finish current function
                if fn_insns and insn.address in entry_set:
                    break

                fn_insns.append(insn)
                insn_idx += 1

                # If return instruction encountered and next instruction is aligned or padding
                if insn.is_ret():
                    # Stop if next instruction is prologue or next entry
                    if insn_idx < len(all_insns) and all_insns[insn_idx].address in entry_set:
                        break

            if fn_insns:
                fn.instructions = fn_insns
                fn.basic_blocks = self.partition_basic_blocks(fn_insns, fn_id)
                # Callee harvesting
                for i in fn_insns:
                    if i.is_call():
                        for op in i.operands:
                            if op.get("type") == 2 and "imm" in op:
                                fn.callees.add(op["imm"])

                functions.append(fn)

        return functions
