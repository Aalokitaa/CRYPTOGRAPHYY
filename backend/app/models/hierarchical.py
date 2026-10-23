"""
CryptoScope Hierarchical Classification Engine
Paper Section III-E, Figure 4:
3-Level Hierarchical Inference Routing:
- Level 1: Crypto vs Non-Crypto
- Level 2: Cryptographic Family (Symmetric Cipher, Asymmetric Cipher, Hash, MAC)
- Level 3: Specific Primitive (AES, DES/3DES, RSA, ECC, SHA-256, SHA-512, HMAC, ChaCha20)
Each level produces calibrated confidence scores with 'low-confidence/unknown' rejection.
"""

from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel
import numpy as np

from backend.app.datasets.manifest import CryptoFamily, CryptoPrimitive

class HierarchicalPrediction(BaseModel):
    is_crypto: bool
    l1_confidence: float
    family: str
    l2_confidence: float
    primitive: str
    l3_confidence: float
    overall_confidence: float
    is_low_confidence: bool = False
    routing_path: List[str]
    per_class_probabilities: Dict[str, float] = {}

class HierarchicalModelWrapper:
    def __init__(self, 
                 l1_model: Any, 
                 l2_model: Any, 
                 l3_models: Dict[str, Any],
                 scaler: Optional[Any] = None,
                 threshold: float = 0.5):
        self.l1_model = l1_model
        self.l2_model = l2_model
        # l3_models can be a single model or per-family dict
        self.l3_models = l3_models
        self.scaler = scaler
        self.threshold = threshold

    def predict(self, x: np.ndarray) -> HierarchicalPrediction:
        """
        Executes hierarchical routing for a single feature vector.
        """
        if x.ndim == 1:
            x_in = x.reshape(1, -1)
        else:
            x_in = x

        if self.scaler is not None:
            x_in = self.scaler.transform(x_in)

        routing_path = []
        per_class_probs = {}

        # ---------------- LEVEL 1: Crypto vs Non-Crypto ----------------
        l1_probs = self.l1_model.predict_proba(x_in)[0]
        # l1_classes: [0: Non-Crypto, 1: Crypto]
        prob_crypto = float(l1_probs[1]) if len(l1_probs) > 1 else float(l1_probs[0])
        prob_noncrypto = float(l1_probs[0]) if len(l1_probs) > 1 else 1.0 - prob_crypto

        per_class_probs["Crypto"] = prob_crypto
        per_class_probs["Non-crypto"] = prob_noncrypto

        if prob_crypto < self.threshold:
            routing_path.extend(["Level 1: Non-Crypto", "Termination: Non-Crypto"])
            return HierarchicalPrediction(
                is_crypto=False,
                l1_confidence=prob_noncrypto,
                family=CryptoFamily.NON_CRYPTO.value,
                l2_confidence=prob_noncrypto,
                primitive=CryptoPrimitive.NON_CRYPTO.value,
                l3_confidence=prob_noncrypto,
                overall_confidence=prob_noncrypto,
                is_low_confidence=prob_noncrypto < 0.6,
                routing_path=routing_path,
                per_class_probabilities=per_class_probs
            )

        routing_path.append(f"Level 1: Crypto ({prob_crypto:.2f})")

        # ---------------- LEVEL 2: Family ----------------
        l2_probs = self.l2_model.predict_proba(x_in)[0]
        l2_classes = list(self.l2_model.classes_)
        best_l2_idx = int(np.argmax(l2_probs))
        family_name = str(l2_classes[best_l2_idx])
        l2_conf = float(l2_probs[best_l2_idx])

        for c, p in zip(l2_classes, l2_probs):
            per_class_probs[str(c)] = float(p)

        routing_path.append(f"Level 2: {family_name} ({l2_conf:.2f})")

        # ---------------- LEVEL 3: Specific Primitive ----------------
        # Route to L3 model (or global L3 model)
        l3_model = self.l3_models.get(family_name, self.l3_models.get("global"))
        if l3_model is not None:
            l3_probs = l3_model.predict_proba(x_in)[0]
            l3_classes = list(l3_model.classes_)
            best_l3_idx = int(np.argmax(l3_probs))
            prim_name = str(l3_classes[best_l3_idx])
            l3_conf = float(l3_probs[best_l3_idx])

            for c, p in zip(l3_classes, l3_probs):
                per_class_probs[str(c)] = float(p)
        else:
            prim_name = "Unknown"
            l3_conf = 0.5

        routing_path.append(f"Level 3: {prim_name} ({l3_conf:.2f})")

        overall_conf = round(prob_crypto * l2_conf * l3_conf, 3)
        is_low = (l2_conf < self.threshold) or (l3_conf < self.threshold)

        return HierarchicalPrediction(
            is_crypto=True,
            l1_confidence=round(prob_crypto, 3),
            family=family_name,
            l2_confidence=round(l2_conf, 3),
            primitive=prim_name,
            l3_confidence=round(l3_conf, 3),
            overall_confidence=overall_conf,
            is_low_confidence=is_low,
            routing_path=routing_path,
            per_class_probabilities=per_class_probs
        )
