from app.schemas.report import (
    ReportGenerationRequest,
    ReportResponse,
    ValidationPlanItem,
    WET_LAB_DISCLAIMER,
)


class ReportGenerationService:
    def generate(self, request: ReportGenerationRequest) -> ReportResponse:
        validation = request.sequence_validation
        features = request.protein_features
        prediction = request.enzyme_prediction
        scoring = request.property_scoring
        variants = request.variant_ranking
        conditions = request.target_conditions

        summary_parts = [
            f"The submitted sequence is {'valid' if validation.valid else 'not valid'} and contains {validation.sequence_length} amino acids."
        ]
        if prediction:
            summary_parts.append(
                f"Its likely enzyme type is {prediction.predicted_family}, with {self._confidence_words(prediction.confidence)} confidence."
            )
        if scoring:
            summary_parts.append(
                f"Overall fit for the target industrial conditions is {self._score_words(scoring.industrial_fit_score)}."
            )
        if variants and variants.ranked_variants:
            top = variants.ranked_variants[0]
            summary_parts.append(
                f"The top candidate to test first is variant {top.variant_id} ({top.wet_lab_priority} priority)."
            )

        executive_summary = " ".join(summary_parts) + " " + WET_LAB_DISCLAIMER

        validation_plan = self._validation_plan(conditions, variants is not None)
        limitations = [
            "This report is based only on computer analysis of the sequence.",
            "It does not include any laboratory measurements of activity, stability, or production yield.",
            "Every candidate should be confirmed with laboratory testing before use.",
        ]

        json_report = {
            "executive_summary": executive_summary,
            "input_sequence_summary": validation.model_dump(),
            "protein_features": features.model_dump() if features else None,
            "predicted_function": prediction.model_dump() if prediction else None,
            "industrial_target_conditions": conditions.model_dump(),
            "property_indicators": scoring.model_dump() if scoring else None,
            "candidate_variant_ranking": variants.model_dump() if variants else None,
            "wet_lab_validation_plan": [item.model_dump() for item in validation_plan],
            "limitations": limitations,
            "disclaimer": WET_LAB_DISCLAIMER,
        }

        markdown = self._markdown(json_report)
        return ReportResponse(
            executive_summary=executive_summary,
            markdown_report=markdown,
            json_report=json_report,
            recommended_wet_lab_validation_plan=validation_plan,
            limitations=limitations,
        )

    def _validation_plan(self, conditions, has_variants: bool) -> list[ValidationPlanItem]:
        use_case = conditions.use_case or "custom"
        items = [
            ValidationPlanItem(
                step="Confirm expression and purification feasibility",
                rationale="Computational sequence scores do not measure expression yield or soluble recovery.",
            ),
            ValidationPlanItem(
                step="Run small-scale activity assay under target process conditions",
                rationale=f"The selected use case is {use_case}; activity must be measured under matching pH, temperature, salinity, and solvent conditions.",
            ),
            ValidationPlanItem(
                step="Measure heat and pH stability over realistic process times",
                rationale="Real-world use depends on the enzyme keeping its activity over time, which sequence analysis alone cannot confirm.",
            ),
        ]
        if has_variants:
            items.append(
                ValidationPlanItem(
                    step="Test the top variants side by side with the original enzyme",
                    rationale="The ranking suggests where to start; matched lab tests confirm which variant actually performs better.",
                )
            )
        return items

    @staticmethod
    def _confidence_words(value: float) -> str:
        if value >= 0.66:
            return "high"
        if value >= 0.4:
            return "moderate"
        return "low"

    @staticmethod
    def _score_words(value: float) -> str:
        if value >= 0.72:
            return "strong"
        if value >= 0.45:
            return "moderate"
        return "limited"

    def _markdown(self, report: dict) -> str:
        lines = [
            "Neolysis Enzyme Candidate Report",
            "",
            "Summary",
            report["executive_summary"],
            "",
            "Sequence Quality",
            f"The sequence is {'valid' if report['input_sequence_summary']['valid'] else 'not valid'}.",
            f"It contains {report['input_sequence_summary']['sequence_length']} amino acids.",
        ]
        warnings = report["input_sequence_summary"]["warnings"]
        if warnings:
            lines.append(f"Notes: {', '.join(warnings)}.")
        else:
            lines.append("No quality warnings were found.")

        lines.extend(["", "Likely Enzyme Type"])
        prediction = report.get("predicted_function")
        if prediction:
            lines.append(
                f"Closest match: {prediction['predicted_family']}."
            )
            lines.append(
                f"Confidence in this match is {self._confidence_words(prediction['confidence'])}."
            )
            lines.append(
                "This is an early screening signal based on sequence patterns, not a confirmed identification."
            )
        else:
            lines.append("Not enough information to suggest an enzyme type.")

        lines.extend(["", "Fit for Target Industrial Conditions"])
        scoring = report.get("property_indicators")
        if scoring:
            lines.append(
                f"Overall condition fit: {scoring['condition_fit']['label']}."
            )
            lines.append(f"Heat stability: {scoring['thermostability']['label']}.")
            lines.append(f"pH suitability: {scoring['ph_fit']['label']}.")
            lines.append(f"Solubility outlook: {scoring['solubility']['label']}.")
            if scoring["risk_flags"]:
                lines.append("Things to double-check:")
                for flag in scoring["risk_flags"]:
                    lines.append(f"  - {flag}")
        else:
            lines.append("Not enough information to estimate industrial fit.")

        lines.extend(["", "Candidate Variants to Test"])
        variants = report.get("candidate_variant_ranking")
        if variants and variants["ranked_variants"]:
            for item in variants["ranked_variants"]:
                lines.append(
                    f"  {item['rank']}. Variant {item['variant_id']} - "
                    f"{item['wet_lab_priority']} priority "
                    f"(estimated fit {item['predicted_fit_score']}, risk {item['risk_score']})."
                )
        else:
            lines.append("No variants were provided for comparison.")

        lines.extend(["", "Suggested Next Steps in the Lab"])
        for item in report["wet_lab_validation_plan"]:
            lines.append(f"  - {item['step']}. {item['rationale']}")

        lines.extend(["", "What This Report Does and Does Not Cover"])
        for limitation in report["limitations"]:
            lines.append(f"  - {limitation}")
        lines.extend(["", report["disclaimer"]])
        return "\n".join(lines)


report_generation_service = ReportGenerationService()
