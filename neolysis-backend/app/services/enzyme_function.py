import re
from typing import Optional

from app.schemas.enzyme import EmbeddingResult, EnzymeFunctionPrediction


class EnzymeFunctionService:
    def predict(
        self,
        sequence: str,
        embedding: Optional[EmbeddingResult] = None,
        enzyme_class_hint: Optional[str] = None,
    ) -> EnzymeFunctionPrediction:
        evidence: list[str] = []
        family = "enzyme function unknown"
        ec_class = None
        confidence = 0.22

        if enzyme_class_hint:
            family = enzyme_class_hint.strip()
            evidence.append("User supplied an enzyme class hint.")
            confidence = 0.36

        if re.search(r"G[A-Z]S[A-Z]G", sequence):
            family = "hydrolase-like enzyme; possible lipase or esterase"
            ec_class = "EC 3.-.-.-"
            evidence.append("Detected a G-X-S-X-G motif often associated with serine hydrolase scaffolds.")
            confidence = max(confidence, 0.46)
        elif re.search(r"H[A-Z]H|H[A-Z]{2}H|H[A-Z]C", sequence):
            family = "oxidoreductase-like or metal-binding enzyme candidate"
            ec_class = "EC 1.-.-.-"
            evidence.append("Detected histidine-rich motif patterns that can indicate metal-binding enzyme regions.")
            confidence = max(confidence, 0.34)
        elif re.search(r"E[A-Z]{2,4}E", sequence):
            family = "glycoside-hydrolase-like enzyme candidate"
            ec_class = "EC 3.2.-.-"
            evidence.append("Detected acidic residue spacing compatible with some glycoside hydrolase catalytic motifs.")
            confidence = max(confidence, 0.33)

        if embedding:
            evidence.append(f"Baseline composition embedding generated with {embedding.dimensions} dimensions.")

        return EnzymeFunctionPrediction(
            predicted_family=family,
            predicted_ec_class=ec_class,
            confidence=round(confidence, 3),
            explanation=(
                "This staging prediction uses transparent sequence motifs and composition features. "
                "It should be treated as a baseline triage signal, not as a validated functional annotation."
            ),
            evidence=evidence,
            method="baseline_motif_and_composition_scaffold",
            model_version="enzyme-function-baseline-v0.1",
            limitations=[
                "No trained enzyme classifier is used in this staging scaffold.",
                "Predicted function requires database search, structural review, and wet-lab validation.",
            ],
        )


enzyme_function_service = EnzymeFunctionService()
