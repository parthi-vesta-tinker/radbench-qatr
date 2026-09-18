"""Canned demonstration and actual OpenAI Agents SDK paths, never silent fallback."""

import json
import re
import time
from agents import Agent, ModelSettings, RunConfig, OpenAIResponsesModel
from openai import AsyncOpenAI
from dbos import DBOS
from dbos_openai_agents import DBOSRunner
from .contracts import ReviewProblem, StageOutput, CriticalStageOutput

SAMPLES = [
    dict(
        id="mixed",
        label="Critical + language",
        report_text="Findings:\nAcute right pneumothorax. Cardiomediastinal silhoutte is unchanged.\n\nImpression:\nAcute right pneumothorax.",
    ),
    dict(
        id="clean",
        label="No observations",
        report_text="Findings:\nLungs are clear. No pleural effusion or pneumothorax.\n\nImpression:\nNo acute cardiopulmonary abnormality.",
    ),
    dict(
        id="discrepancy",
        label="Laterality discrepancy",
        report_text="Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion.",
    ),
    dict(
        id="critical",
        label="Critical only",
        report_text="Findings:\nAcute right pneumothorax.\n\nImpression:\nAcute right pneumothorax.",
    ),
    dict(
        id="language",
        label="Language only",
        report_text="Findings:\nCardiomediastinal silhoutte is unchanged. Lungs are clear.\n\nImpression:\nNo acute cardiopulmonary abnormality.",
    ),
]

# Fixed synthetic examples, not a clinical classifier. Metadata is part of the report.
SAMPLES.extend(
    [
        dict(
            id="critical_documented",
            label="Critical · documented flag",
            report_text="Critical finding flag: Yes\n\n" + SAMPLES[3]["report_text"],
        ),
        dict(
            id="critical_unflagged",
            label="Critical · explicitly unflagged",
            report_text="Critical finding flag: No\n\n" + SAMPLES[3]["report_text"],
        ),
    ]
)


def normalized(text):
    return re.sub(r"\s+", " ", text).strip().casefold()


def observation(comment, kind="suggestion", section="findings"):
    return dict(finding_type=kind, report_section=section, comment=comment)


@DBOS.step(name="qa.demo.stage.v3")
def demo_stage(stage: str, payload: dict) -> dict:
    match = next(
        (
            s
            for s in SAMPLES
            if normalized(s["report_text"]) == normalized(payload["report_text"])
        ),
        None,
    )
    if not match:
        raise ReviewProblem(
            "DEMO_INPUT_UNSUPPORTED",
            "Demo mode supports the provided synthetic examples only. Configure OpenAI mode to review other reports.",
        )
    found = []
    if stage == "language_review" and match["id"] in ("mixed", "language"):
        found = [
            observation(
                "Findings: “silhoutte” → “silhouette”. Please correct if appropriate."
            )
        ]
    if stage == "consistency_review" and match["id"] == "discrepancy":
        found = [
            observation(
                "Findings state left pleural effusion; impression states right. Please reconcile laterality.",
                "discrepancy",
                "both",
            )
        ]
    if stage == "critical_finding_review" and match["id"] in (
        "mixed",
        "critical",
        "critical_documented",
        "critical_unflagged",
    ):
        found = [
            observation(
                "Impression describes acute right pneumothorax. Please review critical designation and the applicable communication pathway.",
                section="impression",
            )
        ]
    output = dict(observations=found)
    if stage == "critical_finding_review":
        status, quote = {
            "critical_documented": ("documented_flagged", "Critical finding flag: Yes"),
            "critical_unflagged": (
                "documented_not_flagged",
                "Critical finding flag: No",
            ),
        }.get(match["id"], ("unknown", None))
        output.update(flag_status=status, flag_quote=quote)
    return dict(
        output=output,
        metrics=dict(provider="demo", model_calls=0, elapsed_ms=0),
    )


def make_model(config, client):
    return OpenAIResponsesModel(model=config["model"], openai_client=client)


@DBOS.workflow(name="qa.openai.stage.v4")
async def openai_stage(stage: str, payload: dict, sections: dict, config: dict) -> dict:
    # DBOS owns the event loop/executor. Never close it with asyncio.run().
    from .skill_runtime import SkillStageOutput, adapt
    from .contracts import section_index
    from openai.types.shared import Reasoning

    task = config["stage_instructions"][stage]
    schema = SkillStageOutput
    async with AsyncOpenAI(max_retries=0, timeout=120.0) as client:
        agent = Agent(
            name=stage,
            instructions=task,
            model=make_model(config, client),
            output_type=schema,
            model_settings=ModelSettings(
                store=False,
                max_tokens=config["model_max_output_tokens"],
                reasoning=Reasoning(effort=config["model_reasoning_effort"]),
            ),
        )
        started = time.monotonic()
        answer = await DBOSRunner.run(
            agent,
            json.dumps(
                {
                    "report_text": payload["report_text"],
                    "section_index": section_index(payload["report_text"]),
                }
            ),
            max_turns=1,
            run_config=RunConfig(
                tracing_disabled=True, trace_include_sensitive_data=False
            ),
        )
        parsed = schema.model_validate(answer.final_output)
        projected, candidates = adapt(
            parsed, stage, payload["report_text"], config["skill_snapshot"]
        )
        usage = answer.context_wrapper.usage
        return dict(
            output=projected,
            private_candidates=candidates,
            metrics=dict(
                provider="openai",
                model=config["model"],
                elapsed_ms=round((time.monotonic() - started) * 1000),
                requests=usage.requests,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
            ),
        )
