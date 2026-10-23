"""
CryptoScope Dataset Generation CLI
Commands:
  python -m backend.app.datasets.cli status
  python -m backend.app.datasets.cli build [--version v1.0.0]
  python -m backend.app.datasets.cli list
"""

import sys
import argparse
import json
from backend.app.datasets.toolchain import get_toolchain_status
from backend.app.datasets.builder import DatasetBuilder

def cmd_status():
    status = get_toolchain_status()
    print("=" * 65)
    print(" CryptoScope Multi-Architecture Toolchain Status")
    print("=" * 65)
    print(f"Host OS:             {status.host_os}")
    print(f"Docker Daemon:       {'Available (' + status.docker_version + ')' if status.docker_available else 'Not Running'}")
    print(f"Local Compilation:   {'Ready' if status.can_compile_local else 'Degraded (Synthetic Generator Active)'}")
    print(f"Ready ISAs:          {', '.join(status.ready_isas) if status.ready_isas else 'None'}")
    print(f"Missing ISAs:        {', '.join(status.missing_isas) if status.missing_isas else 'None'}")
    print("-" * 65)
    print(f"{'Target ISA':<15} | {'Status':<12} | {'Command':<25}")
    print("-" * 65)
    for tool in status.tools:
        st = "READY" if tool.installed else "MISSING"
        print(f"{tool.target_isa:<15} | {st:<12} | {tool.command:<25}")
    
    if status.missing_isas:
        print("\nInstall Commands for Missing Toolchains:")
        print("  Debian/Ubuntu:")
        print("    sudo apt-get update && sudo apt-get install -y gcc-aarch64-linux-gnu \\")
        print("      gcc-arm-linux-gnueabihf gcc-mips-linux-gnu gcc-mipsel-linux-gnu \\")
        print("      gcc-riscv64-linux-gnu clang binutils-multiarch")
        print("  Docker Container:")
        print("    docker build -t cryptoscope-toolchain -f docker/toolchain.Dockerfile .")
    print("=" * 65)

def cmd_build(args):
    builder = DatasetBuilder()
    print(f"[*] Initiating dataset generation matrix (version: {args.version})...")
    manifest = builder.build_full_dataset(version=args.version)
    print("\n" + "=" * 65)
    print(" Dataset Generation Complete!")
    print("=" * 65)
    print(f"Total Binaries Generated: {manifest.total_binaries}")
    print(f"Total Labeled Functions: {manifest.total_functions}")
    print("\nClass Distribution:")
    for cls, count in manifest.class_distribution.items():
        print(f"  {cls:<20}: {count}")
    print("\nArchitecture Distribution:")
    for isa, count in manifest.isa_distribution.items():
        print(f"  {isa:<20}: {count}")
    print("\nOptimization Level Distribution:")
    for opt, count in manifest.opt_distribution.items():
        print(f"  {opt:<20}: {count}")
    print("=" * 65)

def cmd_list():
    builder = DatasetBuilder()
    manifests = list(builder.manifests_dir.glob("dataset_*.json"))
    print("=" * 65)
    print(f" Available Datasets ({len(manifests)} found)")
    print("=" * 65)
    for mf in manifests:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"- {data.get('version')}: {data.get('total_binaries')} binaries, {data.get('total_functions')} functions ({mf.name})")
        except Exception:
            print(f"- {mf.name}")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="CryptoScope Dataset CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    status_parser = subparsers.add_parser("status", help="Inspect cross-compiler toolchain status")
    
    build_parser = subparsers.add_parser("build", help="Build multi-architecture dataset matrix")
    build_parser.add_argument("--version", type=str, default="v1.0.0", help="Dataset version identifier")

    list_parser = subparsers.add_parser("list", help="List built dataset versions")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status()
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "list":
        cmd_list()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
