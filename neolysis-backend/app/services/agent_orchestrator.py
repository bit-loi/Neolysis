from app.schemas.agent import AgentAnalysisRequest, AgentAnalysisResponse, AgentToolCall
from app.schemas.enzyme import EnzymeFunctionResponse
from app.schemas.report import ReportGenerationRequest
from app.schemas.sequence import SequenceFeatureResponse
from app.schemas.variant import VariantRankRequest
from app.services.embeddings import protein_embedding_service
from app.services.enzyme_function import enzyme_function_service
from app.services.protein_features import protein_feature_service
from app.services.property_scoring import property_scoring_service
from app.services.report_generation import report_generation_service
from app.services.sequence_validation import sequence_validation_service
from app.services.variant_ranking import variant_ranking_service


class NeolysisAgentOrchestrator:
    PLAN = [
        "validate_fasta",
        "extract_protein_features",
        "generate_protein_embedding",
        "predict_enzyme_family",
        "score_industrial_fit",
        "rank_variants_if_provided",
        "generate_validation_report",
    ]

    def analyze(self, request: AgentAnalysisRequest) -> AgentAnalysisResponse:
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
            return AgentAnalysisResponse(
                agent_plan=self.PLAN,
                tool_calls=tool_calls,
                structured_analysis=structured,
                final_report=report.markdown_report,
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
            final_report=report.markdown_report,
            limitations=list(dict.fromkeys(limitations)),
        )


agent_orchestrator = NeolysisAgentOrchestrator()
