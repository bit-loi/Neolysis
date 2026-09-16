import re
from typing import Optional

from app.schemas.enzyme import EmbeddingResult, EnzymeFunctionPrediction
from app.services.uncertainty import uncertainty_estimate


class EnzymeFunctionService:
    def predict(
        self,
        sequence: str,
        embedding: Optional[EmbeddingResult] = None,
        enzyme_class_hint: Optional[str] = None,
    ) -> EnzymeFunctionPrediction:
        evidence: list[str] = []
        family = "general enzyme (type not yet identified)"
        ec_class = None
        confidence = 0.22

        if enzyme_class_hint:
            family = enzyme_class_hint.strip()
            evidence.append("You provided an expected enzyme type, which was used as a starting point.")
            confidence = 0.36

        if re.search(r"G[A-Z]S[A-Z]G", sequence):
            family = "hydrolase, possibly a lipase or esterase"
            ec_class = "EC 3.-.-.-"
            evidence.append("The sequence contains a pattern commonly found in fat- and ester-splitting enzymes.")
            confidence = max(confidence, 0.46)
        elif re.search(r"H[A-Z]H|H[A-Z]{2}H|H[A-Z]C", sequence):
            family = "oxidoreductase or metal-binding enzyme"
            ec_class = "EC 1.-.-.-"
            evidence.append("The sequence contains regions often linked to metal-binding enzymes.")
            confidence = max(confidence, 0.34)
        elif re.search(r"E[A-Z]{2,4}E", sequence):
            family = "glycoside hydrolase, an enzyme that breaks down sugars"
            ec_class = "EC 3.2.-.-"
            evidence.append("The sequence shows an arrangement often seen in sugar-splitting enzymes.")
            confidence = max(confidence, 0.33)

        if embedding:
            evidence.append("A numerical fingerprint of the sequence was generated to support the comparison.")

        confidence = round(confidence, 3)
        return EnzymeFunctionPrediction(
            predicted_family=family,
            predicted_ec_class=ec_class,
            confidence=confidence,
            uncertainty=uncertainty_estimate(
                confidence,
                "Confidence is a heuristic derived from motif specificity and optional user context.",
                "It has not been calibrated against a held-out experimental enzyme dataset.",
            ),
            explanation=(
                "This suggestion is based on recognizable patterns in the sequence. "
                "It is an early screening signal to help decide what to look at next, not a confirmed identification."
            ),
            evidence=evidence,
            method="sequence_pattern_analysis",
            model_version="enzyme-function-baseline-v0.1",
            limitations=[
                "This is a pattern-based suggestion, not a confirmed enzyme identification.",
                "Confirming the enzyme type needs a database search, a structural review, and laboratory testing.",
            ],
        )


enzyme_function_service = EnzymeFunctionService()
