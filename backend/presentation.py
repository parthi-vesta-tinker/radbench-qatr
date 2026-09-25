"""Explicit public projection: storage changes do not silently change API output."""

from .contracts import (
    ReviewResource,
    FeedbackResource,
    ReviewResult,
    ResultObservation,
    ReviewComments,
    StepState,
)

API_VERSION = "2026-09-22"
RECORD_SCHEMA_VERSION = 7
PROVENANCE = {
    "skill_content_version",
    "skill_content_sha256",
    "skill_snapshot_sha256",
    "mode",
    "model",
    "policy_status",
    "policy_version",
    "prompt_version",
    "workflow_version",
    "source_kind",
    "source_version",
    "authorship_status",
    "signature_status",
    "upstream_qa",
    "jev_enabled_at_acceptance",
}


def pick(data, fields):
    return {k: v for k, v in data.items() if k in fields}


def classification(item, source_status):
    """Public JEV resource; stored grounded anchors and rubric content remain private."""
    return dict(id=item["id"], object="finding_classification", classification_schema_version="1.0",
                review_id=item["review_id"], input_version=item["input_version"],
                observation_id=item["observation_id"], input_hash=item["input_hash"],
                input={**pick(item["input"], {"finding_text", "qa_comment"}),
                       "source": "report_excerpts" if item["input"].get("report_quotes") else "qa_comment"}, source_status=source_status,
                execution_status=item["execution_status"], steps=item["steps"],
                result=item["result"], error=item["error"],
                provenance=dict(model=item["config"]["model"],
                                rubric_id=item["config"]["rubric"]["id"],
                                rubric_hash=item["config"]["rubric_hash"],
                                workflow_version=item["config"]["workflow_version"]),
                created_at=item["created_at"], updated_at=item["updated_at"])


def classification_analysis(rid, input_data, config):
    """Explicit inspection of the saved JEV request; no private anchor metadata."""
    from .classification import request_body
    body = request_body(input_data, config)
    return dict(classification_id=rid, model=body["model"],
                state=pick(body["state"], {"finding_text", "qa_comment", "report_quotes", "target", "report_context"}),
                questions={field: pick(question, {"type", "instructions", "criteria"})
                           for field, question in body["questions"].items()},
                rubric_id=config["rubric"]["id"], rubric_version=config["rubric"]["version"],
                rubric_status=config["rubric"]["status"], rubric_hash=config["rubric_hash"])


def classification_overview(result):
    """History and analytics expose only the two agreed classification labels."""
    fields = result["fields"]
    return dict(finding_group=fields["finding_group"]["label"],
                communication_priority=fields["urgency"]["label"])


def review(record, version=API_VERSION):
    if version != API_VERSION:
        raise ValueError("Unsupported API version")
    value = pick(record, ReviewResource.model_fields)
    value.update(
        id=record["review_id"],
        object="qa_review",
        tenant_id=record["tenant_id"],
        api_version=version,
    )
    value["input"] = {"report_text": record["input"]["report_text"]}
    value["provenance"] = pick(record["provenance"], PROVENANCE)
    value["submitted_by"] = record["provenance"].get("submitted_by")
    value["steps"] = [pick(s, StepState.model_fields) for s in record["steps"]]
    for step in value["steps"]:
        if step.get("metrics"):
            step["metrics"] = pick(
                step["metrics"],
                {
                    "provider",
                    "model",
                    "elapsed_ms",
                    "requests",
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "model_calls",
                    "cost_upper_bound_micro_usd",
                },
            )
    if record.get("result") is not None:
        result = pick(record["result"], ReviewResult.model_fields)
        for group in ("general_comments", "critical_comments"):
            result[group] = [
                pick(x, ResultObservation.model_fields) for x in result[group]
            ]

        # Additive copy projection hides the deferred flag section in the current UI.
        # Historical receipts and legacy copy fields remain unchanged.
        def lines(items):
            return (
                "\n\n".join(x["comment"] for x in items)
                or "None."
            )

        general, critical = result["general_comments"], result["critical_comments"]
        result["general_copy_text"] = (f"PACS comments:\n{lines(general)}" if general else "")
        result["comments_copy_text"] = (
            f"PACS comments:\n{lines(general)}\n\nCritical Findings comments:\n{lines(critical)}"
            if general or critical
            else ""
        )
        result["critical_comments_copy_text"] = (
            f"Critical Findings comments:\n{lines(critical)}"
            if critical
            else ""
        )
        value["result"] = result
    value = ReviewResource.model_validate(value).model_dump(exclude_unset=True)
    return value


def comments(record):
    """A narrow history projection: comments only, never the raw report text."""
    result = record.get("result") or {}
    return ReviewComments(
        review_id=record["review_id"],
        execution_status=record["execution_status"],
        result_version=result.get("result_version"),
        general_comments=[
            pick(item, ResultObservation.model_fields)
            for item in result.get("general_comments", [])
        ],
        critical_comments=[
            pick(item, ResultObservation.model_fields)
            for item in result.get("critical_comments", [])
        ],
    ).model_dump()


def feedback(record, version=API_VERSION):
    value = pick(record, FeedbackResource.model_fields)
    value.update(
        id=record["feedback_id"],
        object="qa_feedback",
        tenant_id=record["tenant_id"],
        api_version=version,
    )
    return FeedbackResource.model_validate(value).model_dump()
