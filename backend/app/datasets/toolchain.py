"""
CryptoScope Toolchain Prober and Environment Inspector
Detects host compilers, cross-compilers, strip utilities, and Docker toolchains.
Provides exact install instructions and graceful degradation.
"""

import shutil
import subprocess
import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class ToolchainInfo(BaseModel):
    name: str
    target_isa: str
    command: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    install_command: Dict[str, str]

class ToolchainStatus(BaseModel):
    docker_available: bool
    docker_version: Optional[str] = None
    host_os: str
    tools: List[ToolchainInfo]
    ready_isas: List[str]
    missing_isas: List[str]
    can_compile_local: bool

TOOLCHAIN_DEFINITIONS = [
    {
        "name": "Host x86-64 GCC / Clang",
        "target_isa": "x86-64",
        "commands": ["gcc", "clang", "x86_64-linux-gnu-gcc"],
        "strip_commands": ["strip", "llvm-strip"],
        "install": {
            "debian": "sudo apt-get install -y build-essential clang binutils",
            "arch": "sudo pacman -S base-devel clang",
            "macos": "xcode-select --install",
            "docker": "docker run -it cryptoscope/toolchain"
        }
    },
    {
        "name": "ARM64 Cross Compiler (AArch64)",
        "target_isa": "ARM64",
        "commands": ["aarch64-linux-gnu-gcc", "aarch64-none-elf-gcc"],
        "strip_commands": ["aarch64-linux-gnu-strip", "llvm-strip", "strip"],
        "install": {
            "debian": "sudo apt-get install -y gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu",
            "arch": "sudo pacman -S aarch64-linux-gnu-gcc",
            "docker": "docker build -t cryptoscope-toolchain -f docker/toolchain.Dockerfile ."
        }
    },
    {
        "name": "ARM32 Cross Compiler (ARM + Thumb)",
        "target_isa": "ARM32",
        "commands": ["arm-linux-gnueabihf-gcc", "arm-none-eabi-gcc", "arm-linux-gnu-gcc"],
        "strip_commands": ["arm-linux-gnueabihf-strip", "arm-none-eabi-strip", "llvm-strip", "strip"],
        "install": {
            "debian": "sudo apt-get install -y gcc-arm-linux-gnueabihf binutils-arm-linux-gnueabihf",
            "arch": "sudo pacman -S arm-linux-gnueabihf-gcc",
            "docker": "docker build -t cryptoscope-toolchain -f docker/toolchain.Dockerfile ."
        }
    },
    {
        "name": "MIPS32 Big-Endian Cross Compiler",
        "target_isa": "MIPS32-BE",
        "commands": ["mips-linux-gnu-gcc", "mips-unknown-linux-gnu-gcc"],
        "strip_commands": ["mips-linux-gnu-strip", "llvm-strip", "strip"],
        "install": {
            "debian": "sudo apt-get install -y gcc-mips-linux-gnu binutils-mips-linux-gnu",
            "arch": "sudo pacman -S mips-linux-gnu-gcc",
            "docker": "docker build -t cryptoscope-toolchain -f docker/toolchain.Dockerfile ."
        }
    },
    {
        "name": "MIPS32 Little-Endian Cross Compiler",
        "target_isa": "MIPS32-LE",
        "commands": ["mipsel-linux-gnu-gcc", "mips64el-linux-gnuabi64-gcc"],
        "strip_commands": ["mipsel-linux-gnu-strip", "llvm-strip", "strip"],
        "install": {
            "debian": "sudo apt-get install -y gcc-mipsel-linux-gnu binutils-mipsel-linux-gnu",
            "arch": "sudo pacman -S mipsel-linux-gnu-gcc",
            "docker": "docker build -t cryptoscope-toolchain -f docker/toolchain.Dockerfile ."
        }
    },
    {
        "name": "RISC-V 64 Cross Compiler",
        "target_isa": "RISC-V 64",
        "commands": ["riscv64-linux-gnu-gcc", "riscv64-unknown-elf-gcc"],
        "strip_commands": ["riscv64-linux-gnu-strip", "llvm-strip", "strip"],
        "install": {
            "debian": "sudo apt-get install -y gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu",
            "arch": "sudo pacman -S riscv64-linux-gnu-gcc",
            "docker": "docker build -t cryptoscope-toolchain -f docker/toolchain.Dockerfile ."
        }
    }
]

def check_command_version(cmd: str) -> Optional[str]:
    try:
        res = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            first_line = res.stdout.strip().splitlines()[0] if res.stdout else "Available"
            return first_line
    except Exception:
        pass
    return None

def check_docker_daemon() -> tuple[bool, Optional[str]]:
    if not shutil.which("docker"):
        return False, None
    try:
        res = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"], 
                             capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            return True, res.stdout.strip()
    except Exception:
        pass
    return False, None

def get_toolchain_status() -> ToolchainStatus:
    docker_ok, docker_ver = check_docker_daemon()
    tools: List[ToolchainInfo] = []
    ready_isas = []
    missing_isas = []

    for defn in TOOLCHAIN_DEFINITIONS:
        installed = False
        ver = None
        cmd_path = None
        active_cmd = defn["commands"][0]

        for cmd in defn["commands"]:
            path = shutil.which(cmd)
            if path:
                v = check_command_version(cmd)
                if v:
                    installed = True
                    ver = v
                    cmd_path = path
                    active_cmd = cmd
                    break

        if installed:
            ready_isas.append(defn["target_isa"])
        else:
            missing_isas.append(defn["target_isa"])

        tools.append(ToolchainInfo(
            name=defn["name"],
            target_isa=defn["target_isa"],
            command=active_cmd,
            installed=installed,
            version=ver,
            path=cmd_path,
            install_command=defn["install"]
        ))

    return ToolchainStatus(
        docker_available=docker_ok,
        docker_version=docker_ver,
        host_os=os.name,
        tools=tools,
        ready_isas=ready_isas,
        missing_isas=missing_isas,
        can_compile_local=len(ready_isas) > 0
    )
