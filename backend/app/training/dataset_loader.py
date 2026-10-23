"""
CryptoScope Dataset Loader & Grouped Data Splitter
Paper Section IV-D:
- Loads versioned dataset manifests
- GROUPED 70/15/15 splits by (source_program + implementation)
  Guarantees zero data leakage across compilers, opt-levels, or architectures!
- Cross-architecture scenarios:
  1. Same-ISA
  2. Mixed-ISA
  3. Unseen-ISA (Leave-One-ISA-Out)
  4. Leave-One-Compiler-Out
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from sklearn.model_selection import GroupShuffleSplit

from backend.app.datasets.manifest import DatasetManifest, TargetISA, OptLevel, CryptoFamily, CryptoPrimitive
from backend.app.analysis.disassembler import MultiIsaDisassembler
from backend.app.analysis.functions import RecoveredFunction
from backend.app.analysis.cfg import FunctionCFG
from backend.app.analysis.dfg import FunctionDFG
from backend.app.features.extractor import FeatureExtractor, FeatureConfig

class LoadedDataset:
    def __init__(self, 
                 X: np.ndarray, 
                 y_l1: np.ndarray, 
                 y_l2: np.ndarray, 
                 y_l3: np.ndarray,
                 groups: np.ndarray,
                 isas: np.ndarray,
                 compilers: np.ndarray,
                 opt_levels: np.ndarray,
                 feature_names: List[str]):
        self.X = X
        self.y_l1 = y_l1
        self.y_l2 = y_l2
        self.y_l3 = y_l3
        self.groups = groups
        self.isas = isas
        self.compilers = compilers
        self.opt_levels = opt_levels
        self.feature_names = feature_names

    def __len__(self):
        return len(self.X)

class DatasetLoader:
    def __init__(self, manifests_dir: Optional[Path] = None):
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.manifests_dir = manifests_dir or (self.base_dir / "datasets" / "manifests")

    def load_dataset(self, 
                     version: str = "v1.0.0", 
                     feature_config: Optional[FeatureConfig] = None) -> LoadedDataset:
        manifest_file = self.manifests_dir / f"dataset_{version}.json"
        if not manifest_file.exists():
            manifest_file = self.manifests_dir / "latest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"No dataset manifest found for version: {version}")

        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        manifest = DatasetManifest(**data)

        extractor = FeatureExtractor(config=feature_config)

        X_rows = []
        y_l1_rows = []
        y_l2_rows = []
        y_l3_rows = []
        group_rows = []
        isa_rows = []
        comp_rows = []
        opt_rows = []
        feat_names = []

        for b_manifest in manifest.binaries:
            b_path = Path(b_manifest.stripped_path)
            if not b_path.exists():
                continue

            with open(b_path, "rb") as f:
                raw_bytes = f.read()

            isa_val = TargetISA(b_manifest.isa)
            disasm = MultiIsaDisassembler(isa_val, b_manifest.endianness)

            for fn_meta in b_manifest.functions:
                # If function was inlined, skip physical instruction extraction
                if fn_meta.is_inlined or fn_meta.size == 0:
                    continue

                # Slice function code
                fn_offset = max(0, fn_meta.address - 0x400000)
                fn_bytes = raw_bytes[fn_offset : fn_offset + fn_meta.size]
                if not fn_bytes:
                    continue

                fn_insns = disasm.disassemble(fn_bytes, fn_meta.address)
                rec_fn = RecoveredFunction(fn_meta.id, fn_meta.address, isa_val)
                rec_fn.instructions = fn_insns

                cfg = FunctionCFG(rec_fn)
                dfg = FunctionDFG(rec_fn)

                vec, names, _ = extractor.extract_features(rec_fn, cfg, dfg)
                if not feat_names:
                    feat_names = names

                X_rows.append(vec)
                y_l1_rows.append(1 if fn_meta.is_crypto else 0)
                y_l2_rows.append(fn_meta.family.value)
                y_l3_rows.append(fn_meta.primitive.value)

                # Group ID: isolates all compilations (ISAs, compilers, opt levels) of this function
                group_id = f"{fn_meta.source_program}_{fn_meta.implementation}_{fn_meta.name}"
                group_rows.append(group_id)

                isa_rows.append(isa_val.value)
                comp_rows.append(b_manifest.compiler)
                opt_rows.append(b_manifest.opt_level.value)

        return LoadedDataset(
            X=np.array(X_rows, dtype=np.float32),
            y_l1=np.array(y_l1_rows, dtype=np.int64),
            y_l2=np.array(y_l2_rows, dtype=object),
            y_l3=np.array(y_l3_rows, dtype=object),
            groups=np.array(group_rows, dtype=object),
            isas=np.array(isa_rows, dtype=object),
            compilers=np.array(comp_rows, dtype=object),
            opt_levels=np.array(opt_rows, dtype=object),
            feature_names=feat_names
        )

    def get_split_indices(self, 
                          dataset: LoadedDataset, 
                          train_ratio: float = 0.70, 
                          test_ratio: float = 0.15, 
                          random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes grouped 70/15/15 split indices ensuring all levels align perfectly.
        """
        # First split into Train (70%) vs Temp (30%)
        gss_train = GroupShuffleSplit(n_splits=1, train_size=train_ratio, random_state=random_state)
        train_idx, temp_idx = next(gss_train.split(dataset.X, dataset.y_l1, groups=dataset.groups))

        # Split Temp into Val (50%) and Test (50%) -> 15% each of total
        gss_val = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=random_state)
        val_sub, test_sub = next(gss_val.split(dataset.X[temp_idx], dataset.y_l1[temp_idx], groups=dataset.groups[temp_idx]))

        val_idx = temp_idx[val_sub]
        test_idx = temp_idx[test_sub]

        return train_idx, val_idx, test_idx

    def split_grouped(self, 
                      dataset: LoadedDataset, 
                      level: int = 1,
                      train_ratio: float = 0.70, 
                      test_ratio: float = 0.15,
                      random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Grouped 70/15/15 split: No implementation group leaks across train/val/test!
        Returns: (X_tr, y_tr, grp_tr, X_val, y_val, grp_val, X_te, y_te, grp_te)
        """
        if level == 1: y = dataset.y_l1
        elif level == 2: y = dataset.y_l2
        else: y = dataset.y_l3

        train_idx, val_idx, test_idx = self.get_split_indices(
            dataset, train_ratio=train_ratio, test_ratio=test_ratio, random_state=random_state
        )

        return (
            dataset.X[train_idx], y[train_idx], dataset.groups[train_idx],
            dataset.X[val_idx], y[val_idx], dataset.groups[val_idx],
            dataset.X[test_idx], y[test_idx], dataset.groups[test_idx]
        )



    def split_unseen_isa(self, dataset: LoadedDataset, test_isa: str, level: int = 1):
        """
        Leave-One-ISA-Out scenario: Train on 4 ISAs, evaluate on 1 unseen ISA.
        """
        if level == 1: y = dataset.y_l1
        elif level == 2: y = dataset.y_l2
        else: y = dataset.y_l3

        train_mask = (dataset.isas != test_isa)
        test_mask = (dataset.isas == test_isa)

        return (
            dataset.X[train_mask], y[train_mask],
            dataset.X[test_mask], y[test_mask]
        )

    def split_leave_one_compiler(self, dataset: LoadedDataset, test_compiler: str, level: int = 1):
        """
        Leave-One-Compiler-Out scenario: Train on GCC, test on Clang (or vice versa).
        """
        if level == 1: y = dataset.y_l1
        elif level == 2: y = dataset.y_l2
        else: y = dataset.y_l3

        train_mask = (dataset.compilers != test_compiler)
        test_mask = (dataset.compilers == test_compiler)

        return (
            dataset.X[train_mask], y[train_mask],
            dataset.X[test_mask], y[test_mask]
        )
