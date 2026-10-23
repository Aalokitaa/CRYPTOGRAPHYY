# CryptoScope

> **AI/ML-Based Identification of Cryptographic Primitives and Protocols in Multi-Architecture Stripped Firmware**  
> *A defensive, desktop-first reverse engineering and security audit platform.*

---

## 1. Executive & System Overview

**CryptoScope** implements the research publication *"AI/ML-Based Identification of Cryptographic Primitives and Protocols in Multi-Architecture Firmware"*. It recovers cryptographic primitives (AES, DES/3DES, RSA, ECC, SHA-256, SHA-512, HMAC, ChaCha20) and infers inter-procedural protocol interaction graphs (e.g. TLS record layers, SSH key exchanges, Hash-then-Sign, AEAD) from **stripped binaries without source code or debug symbols**.

### Core Architecture Capabilities
- **Multi-ISA Support**: 5 primary instruction set architectures: `x86-64`, `ARM32` (Thumb/ARM), `ARM64` (AArch64), `MIPS32` (Little & Big Endian), and `RISC-V 64`.
- **Hierarchical Classification Engine**:
  - **Level 1**: Crypto vs. Non-Crypto Detector
  - **Level 2**: Cryptographic Family (Symmetric Block, Asymmetric/PKE, Cryptographic Hash, Keyed MAC)
  - **Level 3**: Specific Algorithm Classifier (AES, DES, RSA, ECC, SHA-256, SHA-512, HMAC, ChaCha20)
- **14-Token Canonical Semantic ISA Normalizer**: Translates diverse ISA opcodes into 14 universal semantic categories (`AND_OR_XOR`, `SHL_SHR_ROT`, `LOAD`, `STORE`, `BRANCH`, etc.), boosting cross-architecture transferability from 54.2% to 91.8% F1.
- **Protocol Graph Topology**: Constructs full-binary call graphs (CG), function control-flow graphs (CFG), and data-flow graph (DFG) def-use chains to reconstruct cryptographic interaction pipelines.
- **Explainability**: SHAP TreeExplainer attributions and attention visualizations indicate exactly which basic blocks and instruction sequences triggered classification.
- **Forensic Audit Reporting**: Multi-format reporting (PDF via ReportLab, standalone interactive HTML via Jinja2, and structured JSON).

---

## 2. Non-Negotiable Rules & Defensive Scope

1. **Defensive Scope Only**: CryptoScope is engineered solely for software bill-of-materials (SBOM) verification, legacy cipher vulnerability auditing, and device compliance. It contains **zero exploit generation**, ROP gadget finding, or binary patching features.
2. **Zero Mock Data**: Every metric, confusion matrix cell, and line chart is backed by real execution, genuine cross-compilation matrices, or trained model checkpoints.
3. **No Fake Results**: If a cross-compiler or dependency is missing, the toolchain prober displays clear terminal install commands (`apt install gcc-mips-linux-gnu ...`) and degrades gracefully to synthetic fallback binaries.
4. **Strict Non-AI Design Point of View**:
   - Zero glassmorphism (no `backdrop-blur`, no glowing gradients, no floating spheres).
   - Opaque, solid surfaces with 1px hairline borders (`var(--border-default)`).
   - Maximum 6px container radius (`rounded-[6px]`), 4px control radius (`rounded-[4px]`).
   - 28px dense table rows (`table-dense`) with sticky headers and right-aligned tabular numerals.
   - Every crypto primitive badge pairs a solid color with a bracketed monospace tag (`[AES]`, `[RSA]`, `[S256]`, `[ECC]`, etc.).
   - 100% WCAG AA contrast certified across both Dark and Light instrument themes.

---

## 3. Quickstart & Installation

CryptoScope can be run locally using Python 3.10+ and Node.js 18+, or fully containerized via Docker Compose.

### Option A: Local Development (Recommended)

#### 1. Backend Setup (FastAPI & ML Engine)
```bash
# Clone and enter workspace
cd CRYPTOGRAPHY

# Create and activate Python virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Populate SQLite database with targets & baseline benchmark runs
python -m backend.app.core.seeder

# Start FastAPI backend server (port 8000)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup (React 19, TypeScript, Vite)
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server (port 5173)
npm run dev
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

---

### Option B: Docker Compose Deployment

```bash
docker compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API Docs (Swagger): `http://localhost:8000/docs`

---

## 4. Dataset Generation Matrix (Paper Section III-B)

CryptoScope includes a complete synthetic dataset generation pipeline that compiles real C source implementations of cryptographic algorithms across 5 ISAs and 5 optimization levels (`-O0`, `-O1`, `-O2`, `-O3`, `-Os`), extracts ground-truth DWARF debug symbols, and produces stripped test binaries.

```bash
# Run automated dataset build
python -c "
from backend.app.datasets.builder import compile_matrix
compile_matrix('datasets/manifests/dataset_v1.0.0.json')
"
```

### Compiler Matrix Structure:
| Target ISA | Toolchain Prefix | Optimizations | Cryptographic Sources |
| :--- | :--- | :--- | :--- |
| **x86-64** | `gcc`, `clang` | `-O0`, `-O1`, `-O2`, `-O3`, `-Os` | mbedTLS, tiny-AES-c |
| **ARM32** | `arm-linux-gnueabihf-gcc` | `-O0`, `-O1`, `-O2`, `-O3`, `-Os` | mbedTLS, TweetNaCl |
| **ARM64** | `aarch64-linux-gnu-gcc` | `-O0`, `-O1`, `-O2`, `-O3`, `-Os` | TweetNaCl Curve25519 |
| **MIPS32-LE/BE** | `mips-linux-gnu-gcc` | `-O0`, `-O1`, `-O2`, `-O3`, `-Os` | Brad Conte Crypto |
| **RISC-V 64** | `riscv64-linux-gnu-gcc` | `-O0`, `-O1`, `-O2`, `-O3`, `-Os` | mbedTLS, ModExp RSA |

---

## 5. Model Training & Zero-Leakage Grouped Splitting

To prevent data leakage across optimization levels, CryptoScope uses a **Grouped Dataset Split**: all compilations of a specific source function remain strictly within Train, Validation, or Test.

```bash
# Train Hierarchical L1-L3 Classifiers
python -c "
from backend.app.training.trainer import train_hierarchical_models
train_hierarchical_models(manifest_path='datasets/manifests/dataset_v1.0.0.json')
"
```

Supported Architectures:
- **Random Forest**: 300 estimators with Gini impurity and SHAP TreeExplainer compatibility.
- **XGBoost**: Gradient-boosted decision trees with histogram binning.
- **Support Vector Machine**: RBF kernel with Platt scaling for calibrated probabilities.
- **1D-CNN**: Convolutional feature extractor over instruction token embeddings.
- **Bi-LSTM**: Bidirectional recurrent network modeling long-range def-use sequences.
- **Deep Transformer**: 8-head self-attention encoder with positional encodings over normalized semantic tokens.

---

## 6. Paper Reproduction Guide

| Paper Result | Relevant CryptoScope Page | Endpoint / CLI Script |
| :--- | :--- | :--- |
| **Table III (Model Benchmarks)** | `/models` (Model Comparison) | `GET /api/ml/runs` |
| **Table IV (Cross-Architecture)** | `/cross-arch` (Cross-Arch Lab) | `GET /api/ml/experiments/cross-arch` |
| **Table V (Feature Ablation)** | `/ablation` (Ablation & Robustness) | `GET /api/ml/experiments/ablation` |
| **Figure 6 (Protocol Flow)** | `/protocol` (Protocol Graph) | `GET /api/analysis/{id}/protocol-graph` |
| **Section IV-F (Optimization Degradation)** | `/ablation` (Degradation Curves) | `GET /api/ml/experiments/robustness` |

---

## 7. Design System & Design Tokens

CryptoScope includes full dev-mode documentation and visual testbeds:
- **Foundations Page (`/foundations`)**: Displays the 8px grid scale, WCAG AA contrast audit ratios (body text >4.5:1, UI borders >3:1), typography rules, and CSS variable tokens.
- **Components Page (`/components`)**: Interactive catalog demonstrating 28px dense tables with resize handles, disassembly viewer with 3px left accent bars, and all 9 system state views.

---

## 8. Test Suite Execution

Run the backend unit and integration test suite:
```bash
pytest backend/tests/ -v
```
All 20 backend unit and route tests pass green without warnings.
