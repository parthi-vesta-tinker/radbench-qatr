from __future__ import annotations
import hashlib
import json
import re
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

STEPS = [
    "input_validation",
    "combined_review",
    "output_validation",
    "comment_assembly",
]
REASONS = Literal[
    "missed_observation",
    "unnecessary_observation",
    "incorrect_observation",
    "wrong_grouping",
    "unclear_wording",
    "other",
]


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_text: str = Field(min_length=1, max_length=40000)

    @field_validator("report_text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Paste a report containing findings and impression.")
        return value

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.model_dump(),
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()


class FeedbackInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result_version: int = Field(ge=1)
    rating: Literal["up", "down"]
    target: Literal["result", "observation", "missed_flag"] = "result"
    observation_id: str | None = None
    reason: REASONS | None = None
    explanation: str | None = Field(default=None, max_length=2000)
    suggested_comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def valid_target(self):
        if self.rating == "down" and self.reason is None:
            raise ValueError("Select a feedback reason.")
        if (self.target == "observation") != bool(self.observation_id):
            raise ValueError("An observation target requires its observation ID only.")
        return self


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_type: Literal["suggestion", "discrepancy"]
    report_section: Literal[
        "findings",
        "impression",
        "both",
        "history",
        "indication",
        "technique",
        "comparison",
        "addendum",
        "other",
        "multiple",
    ]
    comment: str = Field(min_length=1, max_length=1200)

    @field_validator("comment")
    @classmethod
    def clean_comment(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Observation comment cannot be blank.")
        return value.strip()


class StageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observations: list[Observation]


class CriticalStageOutput(StageOutput):
    flag_status: Literal["documented_flagged", "documented_not_flagged", "unknown"]
    flag_quote: str | None = Field(max_length=1200)

    @model_validator(mode="after")
    def require_flag_basis(self):
        if self.flag_status == "unknown":
            if self.flag_quote is not None:
                raise ValueError(
                    "Unknown designation must not assert a supporting quote."
                )
        elif not self.flag_quote or not self.flag_quote.strip():
            raise ValueError("A documented designation requires an exact report quote.")
        return self


class ReviewProblem(Exception):
    def __init__(self, code: str, message: str, needs_input=False, retryable=False):
        super().__init__(message)
        self.code, self.message, self.needs_input, self.retryable = (
            code,
            message,
            needs_input,
            retryable,
        )

    def __reduce__(self):
        return (type(self), (self.code, self.message, self.needs_input, self.retryable))


# Preserve source offsets; the full raw report remains the model input.
HEADING = re.compile(
    r"(?im)^[ \t]*(history|clinical history|indication|technique|comparison|addend(?:um|a)|findings?|impressions?|conclusions?)[ \t]*(?::|$)"
)
INLINE_REQUIRED = re.compile(r"(?i)(?<!\w)(findings?|impressions?|conclusions?)[ \t]*:")


def section_index(text: str) -> list[dict]:
    headings = list(HEADING.finditer(text))
    # Pasted headings may lose newlines. Delimited labels or standalone ALL-CAPS
    # labels are recognized; mentions such as "correction to the Impression:" are not.
    inline = re.compile(r"(?i)(?<!\w)(findings?|impressions?|conclusions?)[ \t]*:")
    caps = re.compile(
        r"(?<!\w)(FINDINGS|IMPRESSION|IMPRESSIONS|CONCLUSION|CONCLUSIONS)(?=[ \t])"
    )
    found = {h.start(): h for h in headings}
    for h in sorted(
        [*inline.finditer(text), *caps.finditer(text)], key=lambda h: h.start()
    ):
        if any(x.start() <= h.start() < x.end() for x in found.values()):
            continue
        prefix = text[max(0, h.start() - 80) : h.start()]
        if re.search(
            r"(?i)(?:to|the|of|in|prior|previous|original|above|below|see|described|reported)[ \t]+$",
            prefix,
        ):
            continue
        # Do not split narrative inside an addendum or quoted section discussion.
        prior = [x for x in found.values() if x.start() < h.start()]
        if prior and max(prior, key=lambda x: x.start()).group(1).lower().startswith(
            "addend"
        ):
            continue
        if prefix.count('"') % 2 or prefix.count("“") > prefix.count("”"):
            continue
        found[h.start()] = h
    headings = sorted(found.values(), key=lambda h: h.start())
    result, counts = [], {}

    def append(kind, start, end):
        counts[kind] = counts.get(kind, 0) + 1
        result.append(
            dict(section_id=f"{kind}-{counts[kind]}", kind=kind, start=start, end=end)
        )

    if not headings or text[: headings[0].start()].strip():
        append("other", 0, headings[0].start() if headings else len(text))
    for i, h in enumerate(headings):
        name = h.group(1).lower()
        kind = (
            "findings"
            if name.startswith("finding")
            else "impression"
            if name.startswith(("impression", "conclusion"))
            else "history"
            if "history" in name
            else "addendum"
            if name.startswith("addend")
            else name
        )
        append(
            kind,
            h.end(),
            headings[i + 1].start() if i + 1 < len(headings) else len(text),
        )
    return result


def parse_sections(text: str) -> dict[str, str]:
    sections = {}
    for s in section_index(text):
        kind = s["kind"]
        if kind in ("findings", "impression"):
            if kind in sections:
                raise ReviewProblem(
                    "AMBIGUOUS_SECTIONS",
                    "Please provide one current report with one Findings section and one Impression section.",
                    needs_input=True,
                )
            value = text[s["start"] : s["end"]].strip()
            if not re.search(r"[A-Za-z]{2}", value):
                raise ReviewProblem(
                    "INCOMPLETE_REPORT",
                    f"Please include substantive text in the {kind} section.",
                    needs_input=True,
                )
            sections[kind] = value
    if any(k not in sections for k in ("findings", "impression")):
        raise ReviewProblem(
            "MISSING_SECTIONS",
            "Please include identifiable Findings and Impression sections with substantive text.",
            needs_input=True,
        )
    return sections


def assemble(stage_results: dict, report_text: str) -> dict:
    designation = CriticalStageOutput.model_validate(
        stage_results["critical_finding_review"]["output"]
    )
    if designation.flag_quote is not None and designation.flag_quote not in report_text:
        raise ReviewProblem(
            "UNGROUNDED_FLAG_STATUS",
            "The review asserted a flag status without matching report text. Please retry.",
            retryable=True,
        )
    general, critical = [], []
    for stage, group in [
        ("language_review", general),
        ("consistency_review", general),
        ("critical_finding_review", critical),
    ]:
        schema = (
            CriticalStageOutput if stage == "critical_finding_review" else StageOutput
        )
        parsed = schema.model_validate(stage_results[stage]["output"])
        for obs in parsed.observations:
            item = obs.model_dump()
            # Exact duplicates within a group only: never let a general item suppress a critical item.
            if not any(
                x["comment"].casefold() == item["comment"].casefold() for x in group
            ):
                group.append(item)
    for i, item in enumerate(general + critical, 1):
        item["observation_id"] = f"obs-{i}"
    missed = (
        None
        if critical and designation.flag_status == "unknown"
        else bool(critical) and designation.flag_status == "documented_not_flagged"
    )
    missed_label = "Cannot determine" if missed is None else "Yes" if missed else "No"

    def lines(items):
        return (
            "\n".join(f"{i}. {x['comment']}" for i, x in enumerate(items, 1))
            if items
            else "None."
        )

    copy_text = ""
    if general or critical:
        copy_text = f"QA review:\n\nGeneral Comments:\n{lines(general)}\n\nCritical Findings missed flag: {missed_label}\n\nCritical Findings comments:\n{lines(critical)}"
    return dict(
        result_version=1,
        outcome="observations" if general or critical else "no_observations",
        critical_finding_detected=bool(critical),
        missed_flag=missed,
        critical_flag_status=designation.flag_status,
        critical_flag_quote=designation.flag_quote,
        general_comments=general,
        critical_comments=critical,
        copy_text=copy_text,
        general_copy_text=f"QA review:\n\nGeneral Comments:\n{lines(general)}"
        if general
        else "",
        critical_copy_text=f"QA review:\n\nCritical Findings missed flag: {missed_label}\n\nCritical Findings comments:\n{lines(critical)}"
        if critical
        else "",
        _candidate_mapping=[
            dict(
                observation_id=item["observation_id"],
                candidates=[
                    c
                    for value in stage_results.values()
                    for c in value.get("private_candidates", [])
                    if c["comment"].strip() == item["comment"]
                ],
            )
            for item in general + critical
        ],
    )


class ResultObservation(Observation):
    observation_id: str


class ReviewResult(BaseModel):
    result_version: int
    outcome: Literal["observations", "no_observations"]
    critical_finding_detected: bool
    missed_flag: bool | None
    critical_flag_status: Literal[
        "documented_flagged", "documented_not_flagged", "unknown"
    ]
    critical_flag_quote: str | None
    general_comments: list[ResultObservation]
    critical_comments: list[ResultObservation]
    copy_text: str
    general_copy_text: str = ""
    critical_copy_text: str = ""
    comments_copy_text: str = ""
    critical_comments_copy_text: str = ""


class StepState(BaseModel):
    step_id: Literal[
        "input_validation",
        "combined_review",
        "output_validation",
        "comment_assembly",
    ]
    status: Literal[
        "pending", "running", "completed", "needs_input", "failed", "skipped"
    ]
    started_at: str | None
    completed_at: str | None
    metrics: dict | None = None


class ReviewError(BaseModel):
    code: str
    message: str
    retryable: bool


class ReviewResource(BaseModel):
    id: str
    object: Literal["qa_review"]
    tenant_id: str
    api_version: str
    created_at: str
    completed_at: str | None = None
    input_version: int
    input_hash: str
    input: ReviewInput
    execution_status: Literal["queued", "running", "completed", "needs_input", "failed"]
    result: ReviewResult | None
    error: ReviewError | None
    steps: list[StepState]
    provenance: dict


class FeedbackResource(FeedbackInput):
    id: str
    object: Literal["qa_feedback"]
    tenant_id: str
    api_version: str
    review_id: str
    input_hash: str
    created_at: str


class FeedbackList(BaseModel):
    object: Literal["list"] = "list"
    items: list[FeedbackResource]
    has_more: bool
    next_cursor: str | None
    url: str


class FeedbackInboxItem(BaseModel):
    feedback: FeedbackResource
    report_preview: str
    source: str
    target_comment: str | None


class FeedbackInbox(BaseModel):
    object: Literal["list"] = "list"
    items: list[FeedbackInboxItem]
    has_more: bool
    next_cursor: str | None
    url: str = "/api/v1/feedback"


class ReviewCounts(BaseModel):
    total: int
    with_comments: int
    no_comments: int
    critical: int
    statuses: dict[str, int]


class FeedbackCounts(BaseModel):
    total: int
    reviews: int
    up: int
    down: int
    reasons: dict[str, int]


class CriticalEvaluationReadiness(BaseModel):
    status: Literal["not_measured"]
    unit: Literal["report"]
    scope: Literal["report_text_only"]
    precision: None = None
    recall: None = None
    false_positive_rate: None = None
    false_alert_share: None = None
    tp: None = None
    fp: None = None
    fn: None = None
    tn: None = None
    reason: str


class AnalyticsResource(BaseModel):
    object: Literal["qa_analytics"]
    tenant_id: str
    checked_at: str
    period: Literal["7d", "30d", "all"]
    period_start: str | None
    source: Literal["openai", "demo", "all"]
    reviews: ReviewCounts
    feedback: FeedbackCounts | None
    acceptance: list[AcceptanceCounts] | None = None
    critical_evaluation: CriticalEvaluationReadiness


class OutcomeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result_version: int = Field(ge=1)
    stakeholder: Literal["qa", "radiologist", "facility"]
    subject: Literal["report", "qa_comments"]
    decision: Literal["accepted", "rejected", "review_requested", "unknown"]
    source_note: str = Field(min_length=1, max_length=2000)

    @field_validator("source_note")
    @classmethod
    def meaningful_source(cls, value):
        if not value.strip():
            raise ValueError("Record the source of this decision.")
        return value.strip()


class OutcomeResource(OutcomeInput):
    outcome_id: str
    review_id: str
    created_at: str
    recording_method: Literal["operator_recorded"] = "operator_recorded"


class OutcomeList(BaseModel):
    object: Literal["list"] = "list"
    items: list[OutcomeResource]
    has_more: bool
    next_cursor: str | None
    url: str


class AcceptanceCounts(BaseModel):
    stakeholder: Literal["qa", "radiologist", "facility"]
    subject: Literal["report", "qa_comments"]
    eligible: int
    recorded: int
    accepted: int
    rejected: int
    review_requested: int
    unknown: int
    not_recorded: int
    acceptance_rate: float | None


AnalyticsResource.model_rebuild()


class APIErrorDetail(BaseModel):
    type: str
    code: str
    message: str
    retryable: bool
    request_id: str
    param: str | None = None
    field_errors: list[dict] | None = None


class APIErrorEnvelope(BaseModel):
    error: APIErrorDetail


class DemoSample(BaseModel):
    id: str
    label: str
    report_text: str


class ConfigResource(BaseModel):
    mode: Literal["demo", "openai"]
    model: str | None
    prompt_version: str
    workflow_version: str
    policy_status: Literal["supplied_unvalidated", "provisional_no_manual"]
    policy_version: str | None
    ready: bool
    tenant_id: str
    api_version: str
    samples: list[DemoSample]


class ReviewSummary(BaseModel):
    id: str
    created_at: str
    execution_status: str
    preview: str
    outcome: str | None
    general_count: int
    critical_count: int
    feedback_count: int | None
    mode: str


class ReviewList(BaseModel):
    object: Literal["list"] = "list"
    items: list[ReviewSummary]
    has_more: bool
    next_cursor: str | None
    url: str = "/api/v1/reviews"
