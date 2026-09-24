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
                {"report_text": self.report_text},
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()


class ReviewReplacement(ReviewInput):
    expected_input_version: int = Field(ge=1)


class FeedbackInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
HISTORICAL_CONTEXTS = frozenset({"history", "comparison"})


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


def current_report_sections(text: str) -> dict[str, dict]:
    """Return the current Findings/Impression pair from a pasted report.

    RamSoft copies can include a prior review beneath an explicit History or
    Comparison heading. In that shape, the final pair is the current report.
    A second unmarked report remains unsafe to attribute, so it still fails
    closed rather than guessing which study to review.
    """
    indexed = section_index(text)
    grouped = {
        kind: [section for section in indexed if section["kind"] == kind]
        for kind in ("findings", "impression")
    }
    findings, impressions = grouped["findings"], grouped["impression"]
    if not findings or not impressions:
        raise ReviewProblem(
            "MISSING_SECTIONS",
            "Please include identifiable Findings and Impression sections with substantive text.",
            needs_input=True,
        )
    if len(findings) != len(impressions):
        raise ReviewProblem(
            "AMBIGUOUS_SECTIONS",
            "Findings and Impression labels do not form one clear current report. Keep the current pair once, or place the earlier report under History or Comparison before the current sections.",
            needs_input=True,
        )
    current = {"findings": findings[-1], "impression": impressions[-1]}
    if current["findings"]["start"] >= current["impression"]["start"]:
        raise ReviewProblem(
            "AMBIGUOUS_SECTIONS",
            "The current Findings section must appear before the current Impression section.",
            needs_input=True,
        )
    if len(findings) > 1:
        first_prior_label = min(
            *(section["start"] for section in findings[:-1]),
            *(section["start"] for section in impressions[:-1]),
        )
        prior_context = [
            section
            for section in indexed
            if section["kind"] in HISTORICAL_CONTEXTS
            and section["start"] < first_prior_label
        ]
        if not prior_context:
            raise ReviewProblem(
                "AMBIGUOUS_SECTIONS",
                "More than one Findings or Impression section was found. Place the earlier review under a History or Comparison heading before the current Findings and Impression sections.",
                needs_input=True,
            )
        if any(
            section["kind"] == "addendum"
            and first_prior_label < section["start"] < current["findings"]["start"]
            for section in indexed
        ):
            raise ReviewProblem(
                "AMBIGUOUS_SECTIONS",
                "An addendum appears between repeated Findings or Impression sections. Keep one current report, or move the earlier report into a separate History or Comparison block.",
                needs_input=True,
            )
    for kind, section in current.items():
        value = text[section["start"] : section["end"]].strip()
        if not re.search(r"[A-Za-z]{2}", value):
            raise ReviewProblem(
                "INCOMPLETE_REPORT",
                f"Please include substantive text in the current {kind} section.",
                needs_input=True,
            )
    return current


def parse_sections(text: str) -> dict[str, str]:
    current = current_report_sections(text)
    return {
        kind: text[section["start"] : section["end"]].strip()
        for kind, section in current.items()
    }


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
            "\n\n".join(x["comment"] for x in items)
            if items
            else "None."
        )

    copy_text = ""
    if general or critical:
        copy_text = f"PACS comments:\n{lines(general)}\n\nCritical Findings missed flag: {missed_label}\n\nCritical Findings comments:\n{lines(critical)}"
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
        general_copy_text=f"PACS comments:\n{lines(general)}"
        if general
        else "",
        critical_copy_text=f"Critical Findings missed flag: {missed_label}\n\nCritical Findings comments:\n{lines(critical)}"
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
    created_at: str = Field(description="Latest accepted submission timestamp for this review.")
    completed_at: str | None = None
    input_version: int
    input_hash: str
    input: ReviewInput
    execution_status: Literal["queued", "running", "completed", "needs_input", "failed"]
    result: ReviewResult | None
    error: ReviewError | None
    steps: list[StepState]
    provenance: dict
    # The submitting person is determined by server configuration/credentials.
    # It is never accepted from the report-review request body.
    submitted_by: str | None = None


# JEV is a separate, review-gated research resource. Its labels never modify QA results.
FindingGroup = Literal[
    "neurological", "vascular_cardiac", "thoracic", "abdominal_pelvic",
    "gu_obstetric", "musculoskeletal", "device_procedural", "other",
    "insufficient_context",
]
Polarity = Literal["affirmed", "negated", "unclear"]
Certainty = Literal["definite", "probable", "suspicious", "equivocal", "not_stated", "not_applicable"]
TemporalStatus = Literal["new", "worsening", "stable", "improving", "historical", "not_stated"]
Urgency = Literal["minutes", "hours", "days", "routine", "cannot_determine"]


class ClassificationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_id: str = Field(min_length=1, max_length=100)
    input_version: int = Field(ge=1)
    observation_id: str = Field(min_length=1, max_length=100)


class ClassificationLabels(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_group: FindingGroup
    polarity: Polarity
    certainty: Certainty
    temporal_status: TemporalStatus
    urgency: Urgency


class ClassificationField(BaseModel):
    label: str
    raw_probabilities: dict[str, float]
    provider_confidence: float
    top_probability: float
    margin: float
    calibrated_probabilities: dict[str, float] | None = None
    review_reasons: list[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    fields: dict[str, ClassificationField]
    calibration_status: Literal["uncalibrated", "research_calibration"]
    calibrator_id: str | None = None
    human_review_required: Literal[True] = True
    usage: dict[str, int] | None = None
    duration_ms: int | None = None


class ClassificationPublicInput(BaseModel):
    finding_text: str
    qa_comment: str


class ClassificationResource(BaseModel):
    id: str
    object: Literal["finding_classification"] = "finding_classification"
    classification_schema_version: Literal["1.0"] = "1.0"
    review_id: str
    input_version: int
    observation_id: str
    input_hash: str
    input: ClassificationPublicInput
    source_status: Literal["current", "superseded", "unavailable"]
    execution_status: Literal["queued", "running", "completed", "failed"]
    steps: list[dict]
    result: ClassificationResult | None = None
    error: ReviewError | None = None
    provenance: dict[str, str | None]
    created_at: str
    updated_at: str


class ClassificationConfig(BaseModel):
    enabled: bool
    ready: bool
    reason: str | None = None
    model: str
    rubric_id: str
    rubric_hash: str
    calibration_status: Literal["uncalibrated", "research_calibration"]
    labels: dict[str, list[str]]


class ClassificationFeedbackInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["accept", "edit", "reject"]
    final_labels: ClassificationLabels | None = None
    reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valid_action(self):
        if self.action == "accept" and (self.final_labels is not None or self.reason):
            raise ValueError("Acceptance uses the original labels without a reason.")
        if self.action == "edit" and (self.final_labels is None or not (self.reason or "").strip()):
            raise ValueError("Correction requires five labels and a reason.")
        if self.action == "reject" and (self.final_labels is not None or not (self.reason or "").strip()):
            raise ValueError("Rejection requires a reason and no replacement labels.")
        return self


class ClassificationFeedbackResource(BaseModel):
    id: str
    classification_id: str
    action: Literal["accept", "edit", "reject"]
    predicted_labels: ClassificationLabels
    final_labels: ClassificationLabels | None
    reason: str | None
    actor_name: str | None
    created_at: str


class ClassificationFeedbackList(BaseModel):
    items: list[ClassificationFeedbackResource]


class FeedbackResource(FeedbackInput):
    id: str
    object: Literal["qa_feedback"]
    tenant_id: str
    api_version: str
    review_id: str
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


class FindingCounts(BaseModel):
    inconsistencies: int
    critical_findings: int
    clinical_observations: int
    other_issues: int


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
    period: Literal["1h", "6h", "12h", "24h", "7d", "30d", "all"]
    period_start: str | None
    source: Literal["openai", "demo", "all"]
    reviews: ReviewCounts
    findings: FindingCounts
    feedback: FeedbackCounts | None
    critical_evaluation: CriticalEvaluationReadiness


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
    display_id: str = Field(description="Short stable display identifier for this review.")
    created_at: str = Field(description="Latest accepted submission timestamp for this review.")
    submitted_by: str | None = None
    execution_status: str
    preview: str
    outcome: str | None
    general_count: int
    critical_count: int
    feedback_count: int | None
    mode: str


class ReviewComments(BaseModel):
    """The copy-ready observations for one review, without returning its report text."""

    review_id: str
    execution_status: Literal["queued", "running", "completed", "needs_input", "failed"]
    result_version: int | None = None
    general_comments: list[ResultObservation] = []
    critical_comments: list[ResultObservation] = []


class ReviewList(BaseModel):
    object: Literal["list"] = "list"
    items: list[ReviewSummary]
    has_more: bool
    next_cursor: str | None
    url: str = "/api/v1/reviews"
