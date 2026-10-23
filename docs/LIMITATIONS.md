# CryptoScope: Scientific & Methodological Limitations

This document provides a rigorous, transparent breakdown of the boundaries, edge cases, and known failure modes of CryptoScope, adhering directly to the empirical findings and caveats published in **"AI/ML-Based Identification of Cryptographic Primitives and Protocols in Multi-Architecture Firmware"** (specifically Sections **IV-G** and **V-F**).

---

## 1. Compiler Inlining & Loop Unrolling Degradation (Section IV-G)

### The Phenomenon
At high optimization levels (`-O3` and `-Os`), modern optimizing compilers (GCC, Clang) perform aggressive inter-procedural transformations:
- **Inlining of Helper Routines**: Micro-functions like `aes_sub_bytes`, `feistel_round`, or SHA-256 message schedule expansion steps (`gamma0`, `gamma1`) are frequently inlined directly into parent callers.
- **Loop Flattening and Vectorization**: Fixed-iteration Feistel networks and AES substitution loops may be vectorized into SIMD registers (`xmm`/`ymm` on x86-64, NEON `q` registers on ARM) or completely unrolled into flat sequential basic blocks.

### Impact on Static Features
1. **Symbol-Less Function Boundary Recovery**: In stripped binaries, compiler inlining causes child routine prologues/epilogues to vanish. The parent function expands in cyclomatic complexity and instruction count, leading to feature dilution.
2. **CFG Topology Shifts**: Loop back-edges disappear when loops are unrolled, reducing cyclical graph indicators.
3. **Observed F1 Degradation**: As established in paper Section IV-F and Table VI:
   - `-O0` to `-O2` retains **95.2% Macro F1**.
   - `-O3` exhibits a **1.4% to 1.6% drop** due to inlining.
   - `-Os` (optimize for size) exhibits the largest degradation (**-2.7% to -2.9%**) because aggressive code sharing collapses loop headers into non-standard basic block configurations.

### Mitigation in CryptoScope
- We extract DWARF inlined subroutine attributes (`DW_TAG_inlined_subroutine`) during dataset synthesis to build inlining-aware feature representations.
- Data Flow Graph (DFG) def-use chain analysis tracks arithmetic data paths across basic block boundaries, restoring the algorithmic signal even when function boundaries are merged.

---

## 2. Packed, Obfuscated, and Encrypted Firmware Blobs

### The Phenomenon
Real-world IoT and industrial firmware images frequently contain packed or encrypted payloads:
- **Compressed Kernel / Rootfs**: e.g., SquashFS, CramFS, or LZMA-compressed kernel images embedded inside a bootloader wrapper.
- **UPX / Custom Packing**: Executables packed with decompression stubs that reconstruct code sections in RAM at runtime.
- **Full Payload Encryption**: Proprietary vendor firmware updates signed and encrypted using asymmetric envelopes.

### Impact on Analysis
1. **High Shannon Entropy**: Encrypted or compressed sections display entropy close to 8.0 bits/byte. In this state, opcode disassemblers produce garbage bytes (pseudorandom instruction sequences).
2. **False Positives**: High-entropy data can falsely trigger byte-level n-gram counters if unhandled.

### Mitigation in CryptoScope
- **Pre-Analysis Header & Entropy Scan**: Before disassembly, CryptoScope calculates sliding-window Shannon entropy across the binary address space.
- **Binwalk Container Decomposition**: Integrated heuristics detect compression headers (`uImage`, `LZMA`, `gzip`, `SquashFS`) and warn the researcher to unpack the rootfs before submitting individual stripped binaries.
- If an un-decodable high-entropy blob is detected, CryptoScope flags the region as `BLOB_ENCRYPTED_OR_COMPRESSED` rather than attempting false ML classification.

---

## 3. Static Binary Analysis vs. Dynamic Protocol State (Section V-F)

### The Mandatory Caveat
> **Critical Scientific Caveat**: Static binary analysis identifies *structural candidates* and *inter-procedural call topologies*. It **cannot** definitively prove runtime protocol state, successful cryptographic negotiation, or session key establishment.

### Why Static Analysis Has Limits in Protocol Verification
1. **Execution Path Feasibility**: Static call graphs (CG) identify that function `A` *can* call function `B`. However, without solving symbolic execution path constraints, static analysis cannot guarantee that the branch leading to `B` is feasible at runtime.
2. **Dynamic State & Nonces**: Cryptographic protocols (such as TLS 1.2/1.3 handshakes or SSH Key Exchange) depend intrinsically on transient runtime variables: ephemeral nonces, negotiated cipher suite flags, and network socket responses.
3. **Dead / Unreachable Code**: Stripped vendor binaries often bundle unused cryptographic libraries (e.g., an entire OpenSSL or mbedTLS archive linked into a firmware daemon where only SHA-256 is actually called). Static analysis will detect AES and RSA code in `.text`, even if the daemon never invokes them in production.

### CryptoScope Protocol Pattern Methodology
To avoid misrepresenting static evidence:
- Patterns are tagged as **Inferred Interaction Patterns** with confidence scores derived from call-graph proximity and parameter-passing heuristics.
- Every protocol view persistently displays the mandatory Section V-F limitation notice.
- We report evidence chains (e.g. `SHA-256 digest buffer passed into HMAC outer pad calculation`) rather than claiming certified protocol compliance.

---

## 4. Controlled Dataset vs. Real-World In-the-Wild Firmware (Section IV-G)

### The Benchmark Boundary
Our primary models are trained on a controlled multi-architecture matrix:
- **5 ISAs**: x86-64, ARM32, ARM64, MIPS32 (LE/BE), RISC-V 64.
- **2 Compilers**: GCC, Clang.
- **5 Optimization Levels**: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`.
- **Known Cryptographic Implementations**: mbedTLS, tiny-AES, TweetNaCl, Brad Conte standard crypto, etc.

### Real-World Realities
In wild firmware binaries:
1. **Obscure Toolchains**: Ancient GCC versions (e.g. GCC 3.4 for MIPS embedded devices) or proprietary vendor compilers (Keil, IAR, Wind River VxWorks) generate distinctive calling conventions.
2. **Hand-Crafted Assembly**: Hardware acceleration routines (e.g. inline ARM assembly or RISC-V Zkn crypto extensions) bypass standard compiler instruction sequences.
3. **Non-Standard Cryptography**: Broken or homebrew cipher variants ("custom XOR rolls") do not align with standard primitive classes (AES, SHA, RSA). CryptoScope assigns these to `Non-Crypto` or `Ambiguous Primitive [?]`.

---

## 5. Defensive Scope & Security Boundaries

### Non-Negotiable Operational Boundaries
CryptoScope is engineered **strictly as a defensive inspection, reverse engineering, and SBOM auditing system**:
- **Read-Only Inspection**: It extracts instructions, reconstructs graphs, and outputs audit reports.
- **Zero Exploit Generation**: It contains no payload generators, ROP chain finders, or memory corruption exploit tools.
- **Zero Binary Tampering**: It does not patch, recompile, or modify firmware binaries.
- **Compliance**: Designed for security researchers, firmware auditors, and incident response engineers validating device integrity and software supply chains.
