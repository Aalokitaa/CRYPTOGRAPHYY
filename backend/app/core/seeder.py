"""
CryptoScope Realistic Data Seeder
Populates SQLite with exact realistic firmware targets, function records,
protocol graphs, security findings, and multi-model benchmark runs as specified.
"""

import json
import uuid
import datetime
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, init_db
from backend.app.core.models import AnalysisModel, RunModel, JobModel
from backend.app.api.analysis_router import ANALYSIS_CACHE

REALISTIC_TARGETS = [
    {
        "id": "tplink-archer-c6-v3",
        "filename": "tplink_archer_c6_v3_fw.bin",
        "file_size": 15938304, # 15.2 MB
        "sha256": "4a7f28bc9123e456789abcdef0123456789abcdef0123456789abcdef0123456",
        "md5": "b3e5a7d9c1f2e4b6a8d0c2e4f6a8b0c2",
        "format": "ELF / Linux Kernel Blob",
        "isa": "ARM32",
        "endianness": "little",
        "bits": 32,
        "entrypoint": "0x80008000",
        "confidence": 0.98,
        "container": "uImage header (LZMA compressed payload via binwalk)",
        "functions_count": 342,
        "primitive_counts": {"AES": 48, "HMAC": 26, "SHA-256": 38, "Non-crypto": 230},
        "advisories": [
            {
                "id": "ADV-001",
                "severity": "MEDIUM",
                "title": "Unauthenticated CBC-Mode Encryption Detected",
                "affected_primitives": ["AES"],
                "risk_summary": "AES-CBC routines identified without accompanying cryptographic MAC or AEAD envelope in call graph.",
                "remediation_guidance": "Migrate to authenticated encryption (AES-GCM or ChaCha20-Poly1305) to prevent padding-oracle attacks.",
                "cve_references": ["CWE-327", "RFC 7366"]
            }
        ],
        "patterns": [
            {
                "id": "PAT-001",
                "pattern_name": "TLS 1.2 Handshake & Record Layer",
                "confidence": 0.91,
                "matched_primitives": ["AES", "SHA-256", "HMAC"],
                "description": "Sequential invocation of SHA-256 digest followed by HMAC-SHA256 authentication and AES symmetric block cipher.",
                "security_caveat": "Static analysis identifies candidate architectural patterns but cannot confirm runtime dynamic protocol state.",
                "evidence": ["Call edge: sub_00401A20 (SHA-256) -> sub_00402140 (HMAC)", "Call edge: sub_00402140 (HMAC) -> sub_004035E0 (AES)"]
            }
        ]
    },
    {
        "id": "hikvision-ds2cd-cam",
        "filename": "hikvision_ds2cd_cam.img",
        "file_size": 23907532, # 22.8 MB
        "sha256": "c89b271034f5e718290abde1234567890abcdef1234567890abcdef12345678",
        "md5": "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6",
        "format": "ELF / CramFS Firmware",
        "isa": "ARM64",
        "endianness": "little",
        "bits": 64,
        "entrypoint": "0x00400000",
        "confidence": 0.99,
        "container": "CramFS SquashFS multi-partition image",
        "functions_count": 518,
        "primitive_counts": {"RSA": 32, "AES": 54, "SHA-256": 42, "SHA-512": 16, "Non-crypto": 374},
        "advisories": [
            {
                "id": "ADV-002",
                "severity": "HIGH",
                "title": "Short RSA Modulus / Legacy Key Schedule",
                "affected_primitives": ["RSA"],
                "risk_summary": "Montgomery multiplication loop structures characteristic of 1024-bit RSA modulus identified.",
                "remediation_guidance": "Enforce minimum 2048-bit or 3072-bit modulus, or transition to Ed25519 / NIST P-256.",
                "cve_references": ["NIST SP 800-131A"]
            }
        ],
        "patterns": [
            {
                "id": "PAT-002",
                "pattern_name": "Digital Signature Verification (Hash-then-Sign)",
                "confidence": 0.95,
                "matched_primitives": ["RSA", "SHA-256"],
                "description": "Firmware update verification routine feeding SHA-256 digest into RSA PKCS#1 v1.5 verification engine.",
                "security_caveat": "Static analysis identifies candidate architectural patterns but cannot confirm runtime dynamic protocol state.",
                "evidence": ["Digest passed to modexp bignum routine sub_00418A00"]
            }
        ]
    },
    {
        "id": "netgear-r7000-httpd",
        "filename": "netgear_r7000_httpd.elf",
        "file_size": 4300800, # 4.1 MB
        "sha256": "1f2e3d4c5b6a78901234567890abcdef1234567890abcdef1234567890abcdef",
        "md5": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d",
        "format": "ELF Executable (Stripped)",
        "isa": "ARM32",
        "endianness": "little",
        "bits": 32,
        "entrypoint": "0x00010480",
        "confidence": 0.96,
        "container": "Stripped ELF binary (Standalone daemon)",
        "functions_count": 189,
        "primitive_counts": {"DES": 22, "SHA-256": 18, "Non-crypto": 149},
        "advisories": [
            {
                "id": "ADV-003",
                "severity": "CRITICAL",
                "title": "Deprecated 64-bit Block Cipher (DES/3DES)",
                "affected_primitives": ["DES"],
                "risk_summary": "Legacy 64-bit block size Feistel cipher susceptible to birthday attack collisions (Sweet32).",
                "remediation_guidance": "Deprecate all DES and 3DES cipher suites; replace with AES-256 or ChaCha20.",
                "cve_references": ["CVE-2016-2183", "SWEET32"]
            }
        ],
        "patterns": []
    },
    {
        "id": "asus-rt-ac68u-wifi",
        "filename": "asus_rt_ac68u_wifi.bin",
        "file_size": 8808038, # 8.4 MB
        "sha256": "89abcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567",
        "md5": "7b8a9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
        "format": "ELF / Broadcom MIPS Blob",
        "isa": "MIPS32-BE",
        "endianness": "big",
        "bits": 32,
        "entrypoint": "0x80002000",
        "confidence": 0.94,
        "container": "Broadcom CFE TRX header with MIPS kernel",
        "functions_count": 267,
        "primitive_counts": {"AES": 36, "ECC": 28, "HMAC": 22, "Non-crypto": 181},
        "advisories": [],
        "patterns": [
            {
                "id": "PAT-003",
                "pattern_name": "ECDH Key Exchange + AES-CCM / WPA3 SAE",
                "confidence": 0.88,
                "matched_primitives": ["ECC", "AES", "HMAC"],
                "description": "Elliptic curve scalar multiplication coupled with HMAC key derivation for WPA3 Dragonfly handshake.",
                "security_caveat": "Static analysis identifies candidate architectural patterns but cannot confirm runtime dynamic protocol state.",
                "evidence": ["Curve25519 scalarmult called alongside HMAC-SHA256"]
            }
        ]
    },
    {
        "id": "esp32-ota-v24",
        "filename": "esp32_ota_v2.4.bin",
        "file_size": 1258291, # 1.2 MB
        "sha256": "567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234",
        "md5": "4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
        "format": "ESP32 App Image",
        "isa": "Xtensa",
        "endianness": "little",
        "bits": 32,
        "entrypoint": "0x40080000",
        "confidence": 0.45,
        "container": "Espressif Bootloader V2 format",
        "functions_count": 48,
        "primitive_counts": {"Unknown": 12, "Non-crypto": 36},
        "advisories": [
            {
                "id": "ADV-004",
                "severity": "INFORMATIONAL",
                "title": "Unsupported Architecture: Xtensa LX6/LX7",
                "affected_primitives": ["Unknown"],
                "risk_summary": "Target binary uses Xtensa instruction set. Capstone / LIEF cross-disassembly fallback engaged.",
                "remediation_guidance": "Install pluggable Ghidra headless or binwalk Xtensa plugin for deeper structural recovery.",
                "cve_references": []
            }
        ],
        "patterns": []
    },
    {
        "id": "sifive-hifive-demo",
        "filename": "sifive_hifive_demo.elf",
        "file_size": 2936012, # 2.8 MB
        "sha256": "34567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12",
        "md5": "2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f",
        "format": "ELF 64-bit LSB Executable",
        "isa": "RISC-V 64",
        "endianness": "little",
        "bits": 64,
        "entrypoint": "0x00010000",
        "confidence": 0.97,
        "container": "Bare-metal RISC-V Freedom-E-SDK payload",
        "functions_count": 142,
        "primitive_counts": {"ChaCha20": 24, "SHA-256": 16, "Non-crypto": 102},
        "advisories": [],
        "patterns": [
            {
                "id": "PAT-004",
                "pattern_name": "Authenticated Encryption with Associated Data (AEAD)",
                "confidence": 0.94,
                "matched_primitives": ["ChaCha20", "Poly1305"],
                "description": "ChaCha20 stream cipher 20-round quarter-round permutation paired with Poly1305 authenticator.",
                "security_caveat": "Static analysis identifies candidate architectural patterns but cannot confirm runtime dynamic protocol state.",
                "evidence": ["Constant hit: 'expand 32-byte k' in sub_000142C0", "Quarter-round macro unrolled across 4 blocks"]
            }
        ]
    }
]

def generate_functions_for_target(target: dict):
    prims = target["primitive_counts"]
    funcs = []
    base_addr = int(target["entrypoint"], 16) + 0x1000
    fn_idx = 0

    for prim, count in prims.items():
        for i in range(count):
            addr = base_addr + (fn_idx * 0x80)
            hex_addr = f"0x{addr:08x}"
            name = f"sub_{addr:08x}"
            size = 120 + ((fn_idx * 37) % 1164) # e.g. 1,284 B
            insn_count = size // 4
            is_crypto = (prim not in ["Non-crypto", "Unknown"])
            
            # Irregular realistic confidences
            conf_variants = [0.94, 0.71, 0.58, 0.97, 0.89, 0.92, 0.64]
            conf = conf_variants[fn_idx % len(conf_variants)] if is_crypto else (0.95 if prim == "Non-crypto" else 0.42)

            family = "Symmetric Cipher" if prim in ["AES", "DES", "ChaCha20"] else \
                     "Asymmetric Cipher" if prim in ["RSA", "ECC"] else \
                     "Cryptographic Hash" if "SHA" in prim else \
                     "Message Authentication Code" if prim == "HMAC" else \
                     "Non-crypto" if prim == "Non-crypto" else "Unknown"

            constants = []
            if prim == "AES" and i % 3 == 0:
                constants = ["AES S-box (0x63, 0x7c...)", "Rcon [0x01, 0x02]"]
            elif prim == "SHA-256" and i % 2 == 0:
                constants = ["SHA-256 K constants (0x428a2f98...)"]
            elif prim == "ChaCha20":
                constants = ["'expand 32-byte k'"]

            funcs.append({
                "id": f"fn_{hex_addr}",
                "name": name,
                "address": addr,
                "hex_address": hex_addr,
                "size": size,
                "insn_count": insn_count,
                "is_crypto": is_crypto,
                "family": family,
                "primitive": prim,
                "confidence": conf,
                "is_low_confidence": conf < 0.65,
                "constants_hit": constants,
                "block_count": 4 + (fn_idx % 12),
                "cyclomatic_complexity": 3 + (fn_idx % 9)
            })
            fn_idx += 1

    return funcs

def seed_database():
    init_db()
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        existing_analyses = db.query(AnalysisModel).count()
        if existing_analyses >= 6:
            print("[Seeder] Database already populated with 6+ realistic targets.")
            return

        print("[Seeder] Populating realistic firmware targets...")
        for tgt in REALISTIC_TARGETS:
            funcs = generate_functions_for_target(tgt)
            summary_data = {
                "id": tgt["id"],
                "analysis_id": tgt["id"],
                "filename": tgt["filename"],
                "file_size": tgt["file_size"],
                "sha256": tgt["sha256"],
                "md5": tgt["md5"],
                "format": tgt["format"],
                "isa": tgt["isa"],
                "endianness": tgt["endianness"],
                "bits": tgt["bits"],
                "entrypoint": tgt["entrypoint"],
                "confidence": tgt["confidence"],
                "total_functions": len(funcs),
                "primitive_counts": tgt["primitive_counts"],
                "advisory_count": len(tgt["advisories"]),
                "pattern_count": len(tgt["patterns"])
            }

            nodes = []
            edges = []
            for idx, fn in enumerate(funcs[:20]):
                if fn["is_crypto"]:
                    nodes.append({
                        "id": fn["id"],
                        "type": "primitiveNode",
                        "data": {
                            "label": fn["name"],
                            "primitive": fn["primitive"],
                            "family": fn["family"],
                            "confidence": fn["confidence"],
                            "hex_address": fn["hex_address"]
                        },
                        "position": {"x": (idx % 4) * 240 + 40, "y": (idx // 4) * 140 + 40}
                    })

            for i in range(len(nodes) - 1):
                edges.append({
                    "id": f"e_{i}",
                    "source": nodes[i]["id"],
                    "target": nodes[i+1]["id"],
                    "label": "calls",
                    "animated": True
                })

            full_data = {
                **summary_data,
                "executable_sections": [
                    {"name": ".text", "start": int(tgt["entrypoint"], 16), "end": int(tgt["entrypoint"], 16) + 0x180000, "size": 0x180000, "entropy": 6.84},
                    {"name": ".rodata", "start": int(tgt["entrypoint"], 16) + 0x180000, "end": int(tgt["entrypoint"], 16) + 0x200000, "size": 0x80000, "entropy": 7.12}
                ],
                "functions": funcs,
                "protocol_graph": {"nodes": nodes, "edges": edges},
                "patterns": tgt["patterns"],
                "advisories": tgt["advisories"],
                "call_graph": {"nodes": [{"id": n["id"], "label": n["data"]["label"]} for n in nodes], "edges": edges}
            }

            model_row = AnalysisModel(
                id=tgt["id"],
                filename=tgt["filename"],
                file_size=tgt["file_size"],
                sha256=tgt["sha256"],
                format=tgt["format"],
                isa=tgt["isa"],
                endianness=tgt["endianness"],
                bits=tgt["bits"],
                entrypoint=tgt["entrypoint"],
                confidence=tgt["confidence"],
                summary_json=json.dumps(summary_data),
                full_data_json=json.dumps(full_data)
            )
            db.merge(model_row)

            # In-memory cache for fast interactive lookup
            ANALYSIS_CACHE[tgt["id"]] = {
                "full_data": full_data,
                "cfgs": {},
                "dfgs": {},
                "functions": {}
            }

        # Seed Runs
        runs_to_seed = [
            ("run_transformer_01", "transformer", "v1.0.0", 0.955),
            ("run_xgboost_02", "xgb", "v1.0.0", 0.971),
            ("run_rf_hierarchical", "rf", "v1.0.0", 0.964),
            ("run_cnn_01", "cnn", "v1.0.0", 0.951),
            ("run_lstm_01", "lstm", "v1.0.0", 0.943),
            ("run_svm_01", "svm", "v1.0.0", 0.936),
        ]

        for rid, mtype, dver, f1 in runs_to_seed:
            run_rec = {
                "run_id": rid,
                "model_type": mtype,
                "dataset_version": dver,
                "overall_f1": f1,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "model_path": f"/backend/app/models/saved/{rid}.joblib",
                "level1_metrics": {"accuracy": round(f1 + 0.012, 4), "macro_f1": round(f1 + 0.015, 4)},
                "level2_metrics": {"accuracy": round(f1 + 0.005, 4), "macro_f1": round(f1 + 0.008, 4)},
                "level3_metrics": {"accuracy": round(f1 - 0.004, 4), "macro_f1": round(f1, 4)}
            }
            rmodel = RunModel(
                id=rid,
                model_type=mtype,
                dataset_version=dver,
                overall_f1=f1,
                metrics_json=json.dumps(run_rec),
                config_json=json.dumps({"model_type": mtype, "dataset_version": dver, "optuna_trials": 50}),
                model_path=run_rec["model_path"]
            )
            db.merge(rmodel)

        db.commit()
        print(f"[Seeder] Seeded {len(REALISTIC_TARGETS)} firmware targets and {len(runs_to_seed)} benchmark runs successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
