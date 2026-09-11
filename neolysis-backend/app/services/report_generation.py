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
            f"Sequence validation returned {'valid' if validation.valid else 'invalid'} status for a {validation.sequence_length}-residue input."
        ]
        if prediction:
            summary_parts.append(
                f"Baseline function scaffold suggests {prediction.predicted_family} with confidence {prediction.confidence:.2f}."
            )
        if scoring:
            summary_parts.append(
                f"Industrial fit proxy score is {scoring.industrial_fit_score:.2f} ({scoring.condition_fit.label})."
            )
        if variants and variants.ranked_variants:
            top = variants.ranked_variants[0]
            summary_parts.append(
                f"Top ranked variant is {top.variant_id} with wet-lab priority {top.wet_lab_priority}."
            )

        executive_summary = " ".join(summary_parts) + " " + WET_LAB_DISCLAIMER

        validation_plan = self._validation_plan(conditions, variants is not None)
        limitations = [
            "This staging report is generated only from structured computational outputs.",
            "No wet-lab activity, kinetics, expression, or process-stability data is included.",
            "All candidate and variant decisions require experimental validation.",
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
                step="Measure thermal and pH stability over process-relevant time windows",
                rationale="Industrial deployment depends on retained activity and shelf/process stability, not only sequence-level proxies.",
            ),
        ]
        if has_variants:
            items.append(
                ValidationPlanItem(
                    step="Screen top variants side-by-side with the wild type",
                    rationale="Variant ranking is a prioritization scaffold and should be validated with matched assays.",
                )
            )
        return items

    @staticmethod
    def _markdown(report: dict) -> str:
        lines = [
            "# Neolysis Enzyme Candidate Report",
            "",
            "## Executive Summary",
            report["executive_summary"],
            "",
            "## Sequence Quality",
            f"- Valid: {report['input_sequence_summary']['valid']}",
            f"- Length: {report['input_sequence_summary']['sequence_length']} residues",
            f"- Warnings: {', '.join(report['input_sequence_summary']['warnings']) or 'None'}",
            "",
            "## Predicted Function / Enzyme Class",
        ]
        prediction = report.get("predicted_function")
        if prediction:
            lines.extend([
                f"- Prediction: {prediction['predicted_family']}",
                f"- Confidence: {prediction['confidence']}",
            ])
            if prediction.get("uncertainty"):
                lines.extend([
                    f"- Uncertainty: {prediction['uncertainty']['level']} ({prediction['uncertainty']['uncertainty']})",
                    f"- Calibration: {prediction['uncertainty']['calibration_status']}",
                ])
            lines.append(f"- Method: {prediction['method']}")
        else:
            lines.append("- Not provided.")

        lines.extend(["", "## Industrial Property Indicators"])
        scoring = report.get("property_indicators")
        if scoring:
            lines.append(f"- Industrial fit score: {scoring['industrial_fit_score']}")
            if scoring.get("uncertainty"):
                lines.append(
                    f"- Confidence: {scoring['confidence']} (uncertainty: {scoring['uncertainty']['level']}, {scoring['uncertainty']['calibration_status']})"
                )
            lines.extend(
                [
                    f"- Thermostability indicator: {scoring['thermostability']['label']} ({scoring['thermostability']['score']})",
                    f"- pH fit indicator: {scoring['ph_fit']['label']} ({scoring['ph_fit']['score']})",
                    f"- Solubility proxy: {scoring['solubility']['label']} ({scoring['solubility']['score']})",
                    f"- Risk flags: {', '.join(scoring['risk_flags']) or 'None'}",
                ]
            )
        else:
            lines.append("- Not provided.")

        lines.extend(["", "## Candidate / Variant Ranking"])
        variants = report.get("candidate_variant_ranking")
        if variants and variants["ranked_variants"]:
            for item in variants["ranked_variants"]:
                lines.append(
                    f"- #{item['rank']} {item['variant_id']}: fit {item['predicted_fit_score']}, risk {item['risk_score']}, priority {item['wet_lab_priority']}"
                )
        else:
            lines.append("- No variants were provided.")

        lines.extend(["", "## Wet-lab Validation Plan"])
        for item in report["wet_lab_validation_plan"]:
            lines.append(f"- {item['step']}: {item['rationale']}")

        lines.extend(["", "## Limitations"])
        for limitation in report["limitations"]:
            lines.append(f"- {limitation}")
        lines.extend(["", f"**Disclaimer:** {report['disclaimer']}"])
        return "\n".join(lines)


report_generation_service = ReportGenerationService()
