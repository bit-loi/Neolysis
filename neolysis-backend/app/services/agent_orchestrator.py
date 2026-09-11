import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.agent import AgentAnalysisRequest, AgentAnalysisResponse, AgentToolCall
from app.schemas.enzyme import EnzymeFunctionResponse
from app.schemas.report import ReportGenerationRequest
from app.schemas.sequence import SequenceFeatureResponse
from app.schemas.variant import VariantRankRequest
from app.schemas.scientific import AnalysisProvenance, ComponentProvenance
from app.services.embeddings import protein_embedding_service
from app.services.enzyme_function import enzyme_function_service
from app.services.protein_features import protein_feature_service
from app.services.property_scoring import property_scoring_service
from app.services.report_generation import report_generation_service
from app.services.sequence_validation import sequence_validation_service
from app.services.variant_ranking import variant_ranking_service
from app.services.llm_service import llm_service


class NeolysisAgentOrchestrator:
    PLAN = [
        "validate_fasta",
        "extract_protein_features",
        "generate_protein_embedding",
        "predict_enzyme_family",
        "score_industrial_fit",
        "rank_variants_if_provided",
        "generate_validation_report",
        "narrate_report_if_requested",
    ]

    async def analyze(self, request: AgentAnalysisRequest) -> AgentAnalysisResponse:
        tool_calls: list[AgentToolCall] = []
        validation = sequence_validation_service.validate(request.sequence)
        tool_calls.append(
            AgentToolCall(
                name="validate_fasta",
                status="completed",
                summary=f"Sequence valid={validation.valid}; length={validation.sequence_length}.",
            )
        )

        if not validation.valid:
            structured = {"sequence_validation": validation.model_dump()}
            report_request = ReportGenerationRequest(
                sequence_validation=validation,
                target_conditions=request.target_conditions,
                user_question=request.user_question,
            )
            report = report_generation_service.generate(report_request)
            provenance = self._provenance(request.sequence, [], False, None)
            return AgentAnalysisResponse(
                agent_plan=self.PLAN,
                tool_calls=tool_calls,
                structured_analysis=structured,
                final_report=report.markdown_report,
                provenance=provenance,
                limitations=report.limitations,
            )

        sequence = validation.cleaned_sequence
        features = protein_feature_service.extract(sequence)
        tool_calls.append(
            AgentToolCall(
                name="extract_protein_features",
                status="completed",
                summary=f"Computed {features.method} features for {features.sequence_length} residues.",
            )
        )

        embedding = protein_embedding_service.generate_embedding(sequence)
        tool_calls.append(
            AgentToolCall(
                name="generate_protein_embedding",
                status="completed",
                summary=f"Generated {embedding.mode} embedding with {embedding.dimensions} dimensions.",
            )
        )

        prediction = enzyme_function_service.predict(
            sequence,
            embedding=embedding,
            enzyme_class_hint=request.enzyme_class_hint,
        )
        tool_calls.append(
            AgentToolCall(
                name="predict_enzyme_family",
                status="completed",
                summary=f"Predicted {prediction.predicted_family} at confidence {prediction.confidence}.",
            )
        )

        property_result = property_scoring_service.score(sequence, request.target_conditions)
        tool_calls.append(
            AgentToolCall(
                name="score_industrial_fit",
                status="completed",
                summary=f"Industrial fit score={property_result.industrial_fit_score}.",
            )
        )

        variant_result = None
        if request.variants:
            variant_result = variant_ranking_service.rank(
                wild_type_sequence=sequence,
                variants=request.variants,
                target_conditions=request.target_conditions,
            )
            tool_calls.append(
                AgentToolCall(
                    name="rank_variants",
                    status="completed",
                    summary=f"Ranked {len(variant_result.ranked_variants)} candidate variants.",
                )
            )
        else:
            tool_calls.append(
                AgentToolCall(
                    name="rank_variants",
                    status="skipped",
                    summary="No candidate variants were provided.",
                )
            )

        report_request = ReportGenerationRequest(
            sequence_validation=validation,
            protein_features=features,
            enzyme_prediction=prediction,
            property_scoring=property_result,
            variant_ranking=variant_result,
            target_conditions=request.target_conditions,
            user_question=request.user_question,
        )
        report = report_generation_service.generate(report_request)
        tool_calls.append(
            AgentToolCall(
                name="generate_validation_report",
                status="completed",
                summary="Generated structured candidate prioritization report.",
            )
        )

        structured = {
            "sequence": SequenceFeatureResponse(validation=validation, features=features).model_dump(),
            "enzyme_function": EnzymeFunctionResponse(
                embedding=embedding,
                prediction=prediction,
            ).model_dump(),
            "property_scoring": property_result.model_dump(),
            "variant_ranking": variant_result.model_dump() if variant_result else None,
            "report": report.json_report,
        }
        final_report = report.markdown_report
        llm_used = False
        llm_model = None
        if request.narrative_mode == "llm":
            final_report, llm_used, llm_model = await llm_service.generate_enzyme_report(
                report.json_report, report.markdown_report
            )
            tool_calls.append(
                AgentToolCall(
                    name="narrate_report_with_llm",
                    status="completed" if llm_used else "fallback",
                    summary=(
                        f"Narrated immutable structured results with {llm_model}."
                        if llm_used
                        else "LLM unavailable; retained deterministic report without changing scientific results."
                    ),
                )
            )
        else:
            tool_calls.append(
                AgentToolCall(
                    name="narrate_report_with_llm",
                    status="skipped",
                    summary="Deterministic report requested; no LLM was called.",
                )
            )

        components = [
            ComponentProvenance(
                component="protein_embedding",
                method=embedding.mode,
                model_version=embedding.model_version,
                status="fallback" if embedding.status == "fallback" else "completed",
            ),
            ComponentProvenance(
                component="enzyme_function",
                method=prediction.method,
                model_version=prediction.model_version,
            ),
            ComponentProvenance(
                component="property_scoring",
                method=property_result.method,
                model_version=property_result.model_version,
            ),
        ]
        provenance = self._provenance(request.sequence, components, llm_used, llm_model)
        limitations = (
            prediction.limitations
            + property_result.limitations
            + (variant_result.limitations if variant_result else [])
            + report.limitations
        )
        return AgentAnalysisResponse(
            agent_plan=self.PLAN,
            tool_calls=tool_calls,
            structured_analysis=structured,
            final_report=final_report,
            provenance=provenance,
            limitations=list(dict.fromkeys(limitations)),
        )

    @staticmethod
    def _provenance(
        sequence: str,
        components: list[ComponentProvenance],
        llm_used: bool,
        llm_model: str | None,
    ) -> AnalysisProvenance:
        digest = hashlib.sha256(sequence.encode("utf-8")).hexdigest()
        return AnalysisProvenance(
            analysis_id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            input_sha256=digest,
            deterministic_seed=int(digest[:8], 16),
            components=components,
            llm_used=llm_used,
            llm_model=llm_model,
        )


agent_orchestrator = NeolysisAgentOrchestrator()
