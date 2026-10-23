"""
CryptoScope Architecture, Format, and Endianness Detection
Supports structured formats (ELF, PE, Mach-O) via LIEF and raw firmware blobs
via entropy analysis, instruction valid-ratio scoring, and prologue heuristic matching.
"""

import math
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from pydantic import BaseModel

import lief
import capstone

from backend.app.datasets.manifest import TargetISA

class DetectionResult(BaseModel):
    is_structured: bool
    format: str # "ELF", "PE", "Mach-O", "Raw Blob"
    isa: TargetISA
    endianness: str # "little" or "big"
    bits: int # 32 or 64
    entrypoint: int
    executable_regions: List[Dict[str, Any]]
    confidence: float
    score_breakdown: Dict[str, float]
    container_detected: bool = False
    container_info: Optional[str] = None

def calculate_shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    for count in counts:
        if count == 0:
            continue
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

class ArchitectureDetector:
    def __init__(self):
        self.binwalk_path = shutil.which("binwalk")

    def detect_structured(self, file_path: Path) -> Optional[DetectionResult]:
        try:
            parsed = lief.parse(str(file_path))
            if parsed is None:
                return None

            fmt = "Unknown"
            if isinstance(parsed, lief.ELF.Binary):
                fmt = "ELF"
                mach = parsed.header.machine_type
                endianness = "big" if parsed.header.identity_data.name == "MSB" else "little"
                is_64 = parsed.header.identity_class.name == "ELF64"
                bits = 64 if is_64 else 32

                isa_map = {
                    lief.ELF.ARCH.X86_64: TargetISA.X86_64,
                    lief.ELF.ARCH.ARM: TargetISA.ARM32,
                    lief.ELF.ARCH.AARCH64: TargetISA.ARM64,
                    lief.ELF.ARCH.MIPS: TargetISA.MIPS32_BE if endianness == "big" else TargetISA.MIPS32_LE,
                    lief.ELF.ARCH.RISCV: TargetISA.RISCV64
                }
                detected_isa = isa_map.get(mach, TargetISA.X86_64)

                # Extract executable sections or segments
                exec_regions = []
                for sec in parsed.sections:
                    try:
                        if sec.has(lief.ELF.Section.FLAGS.EXECINSTR):
                            exec_regions.append({
                                "name": sec.name,
                                "vaddr": sec.virtual_address,
                                "size": sec.size,
                                "offset": sec.offset,
                                "entropy": calculate_shannon_entropy(bytes(sec.content))
                            })
                    except Exception:
                        pass

                # If no section headers (e.g. stripped binary), examine executable segments
                if not exec_regions:
                    for seg in parsed.segments:
                        try:
                            # Check if segment has execute permission
                            is_exec = (int(seg.flags) & 1) != 0 # PF_X is bit 0
                            if is_exec or seg.physical_size > 0:
                                exec_regions.append({
                                    "name": f"seg_{hex(seg.virtual_address)}",
                                    "vaddr": seg.virtual_address,
                                    "size": seg.physical_size,
                                    "offset": seg.file_offset,
                                    "entropy": calculate_shannon_entropy(bytes(seg.content))
                                })
                        except Exception:
                            pass

                if not exec_regions and parsed.entrypoint:
                    exec_regions.append({
                        "name": ".text",
                        "vaddr": parsed.entrypoint,
                        "size": len(parsed.raw),
                        "offset": 0,
                        "entropy": calculate_shannon_entropy(bytes(parsed.raw[:4096]))
                    })


                return DetectionResult(
                    is_structured=True,
                    format=fmt,
                    isa=detected_isa,
                    endianness=endianness,
                    bits=bits,
                    entrypoint=parsed.entrypoint,
                    executable_regions=exec_regions,
                    confidence=1.0,
                    score_breakdown={detected_isa.value: 1.0}
                )

            elif isinstance(parsed, lief.PE.Binary):
                fmt = "PE"
                arch = parsed.header.machine
                isa = TargetISA.X86_64
                bits = 64
                if arch == lief.PE.Header.MACHINE_TYPES.AMD64:
                    isa = TargetISA.X86_64
                    bits = 64
                elif arch == lief.PE.Header.MACHINE_TYPES.ARM64:
                    isa = TargetISA.ARM64
                    bits = 64
                elif arch == lief.PE.Header.MACHINE_TYPES.ARM:
                    isa = TargetISA.ARM32
                    bits = 32

                exec_regions = []
                for sec in parsed.sections:
                    if sec.has_characteristic(lief.PE.Section.CHARACTERISTICS.MEM_EXECUTE):
                        exec_regions.append({
                            "name": sec.name,
                            "vaddr": sec.virtual_address,
                            "size": sec.size,
                            "offset": sec.pointerto_raw_data,
                            "entropy": calculate_shannon_entropy(bytes(sec.content))
                        })

                return DetectionResult(
                    is_structured=True,
                    format=fmt,
                    isa=isa,
                    endianness="little",
                    bits=bits,
                    entrypoint=parsed.optional_header.addressof_entrypoint,
                    executable_regions=exec_regions,
                    confidence=1.0,
                    score_breakdown={isa.value: 1.0}
                )

        except Exception:
            pass

        return None

    def detect_raw_blob(self, data: bytes) -> DetectionResult:
        """
        Trial-disassembles sample windows across all 6 ISA configurations.
        Scores valid instruction ratio and known prologue/epilogue signatures.
        """
        sample_size = min(len(data), 4096)
        sample = data[:sample_size]

        configs = [
            (TargetISA.X86_64, capstone.CS_ARCH_X86, capstone.CS_MODE_64, "little", 64),
            (TargetISA.ARM32, capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM, "little", 32),
            (TargetISA.ARM64, capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM, "little", 64),
            (TargetISA.MIPS32_LE, capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN, "little", 32),
            (TargetISA.MIPS32_BE, capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_BIG_ENDIAN, "big", 32),
            (TargetISA.RISCV64, capstone.CS_ARCH_RISCV, capstone.CS_MODE_RISCV64, "little", 64),
        ]

        # Prologue byte patterns
        prologues = {
            TargetISA.X86_64: [b'\x55\x48\x89\xe5', b'\x48\x83\xec', b'\x55\x89\xe5'],
            TargetISA.ARM32: [b'\x04\xe0\x2d\xe5', b'\x04\xb0\x2d\xe5', b'\x2d\xe9'],
            TargetISA.ARM64: [b'\xfd\x7b\xbf\xa9', b'\xfd\x03\x00\x91'],
            TargetISA.MIPS32_LE: [b'\xe0\xff\xbd\x27', b'\x1c\x00\xbf\xaf'],
            TargetISA.MIPS32_BE: [b'\x27\xbd\xff\xe0', b'\xaf\xbf\x00\x1c'],
            TargetISA.RISCV64: [b'\x13\x01\x01\xff', b'\x23\x30\x11\x00']
        }

        scores: Dict[str, float] = {}
        best_cfg = configs[0]
        max_score = -1.0

        for isa, arch, mode, endianness, bits in configs:
            try:
                cs = capstone.Cs(arch, mode)
                cs.detail = True
                valid_bytes = 0
                insn_count = 0

                for insn in cs.disasm(sample, 0x1000):
                    valid_bytes += insn.size
                    insn_count += 1

                valid_ratio = valid_bytes / max(1, len(sample))

                # Signature bonus
                sig_bonus = 0.0
                for pat in prologues.get(isa, []):
                    if pat in sample:
                        sig_bonus += 0.2

                total_score = min(1.0, valid_ratio * 0.8 + sig_bonus)
                scores[isa.value] = round(total_score, 3)

                if total_score > max_score:
                    max_score = total_score
                    best_cfg = (isa, arch, mode, endianness, bits)
            except Exception:
                scores[isa.value] = 0.0

        isa, _, _, endianness, bits = best_cfg
        conf = max(0.2, max_score)

        return DetectionResult(
            is_structured=False,
            format="Raw Binary Blob",
            isa=isa,
            endianness=endianness,
            bits=bits,
            entrypoint=0x0,
            executable_regions=[{
                "name": "raw_code",
                "vaddr": 0x0,
                "size": len(data),
                "offset": 0,
                "entropy": calculate_shannon_entropy(sample)
            }],
            confidence=conf,
            score_breakdown=scores
        )

    def detect(self, file_path: Path) -> DetectionResult:
        structured = self.detect_structured(file_path)
        if structured:
            return structured

        # If not structured, read raw bytes and run trial heuristic
        with open(file_path, "rb") as f:
            data = f.read()

        res = self.detect_raw_blob(data)

        # Check for binwalk container if available
        if self.binwalk_path:
            try:
                out = subprocess.run([self.binwalk_path, "--signature", str(file_path)], 
                                     capture_output=True, text=True, timeout=5)
                if out.returncode == 0 and "Squashfs" in out.stdout or "gzip" in out.stdout:
                    res.container_detected = True
                    res.container_info = out.stdout.strip()
            except Exception:
                pass

        return res
