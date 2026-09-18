"""Canned demonstration and actual OpenAI Agents SDK paths, never silent fallback."""

import re
import time
from agents import Agent, ModelSettings, RunConfig, OpenAIResponsesModel
from openai import AsyncOpenAI
from dbos import DBOS
from dbos_openai_agents import DBOSRunner
from .contracts import ReviewProblem
from agents.models.interface import Model
from . import attempts, spend
from .combined import CombinedOutput, task, model_input

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


class CheckedResponsesModel(OpenAIResponsesModel):
    async def _fetch_response(self, *args, **kwargs):
        response = await super()._fetch_response(*args, **kwargs)
        if response.status != 'completed':
            raise ReviewProblem('MODEL_RESPONSE_INCOMPLETE', 'The provider returned an incomplete response; no result was accepted.')
        return response


def make_model(config, client):
    return CheckedResponsesModel(model=config["model"], openai_client=client)


class GuardedModel(Model):
    """Inside DBOSRunner's model step: replay can never bypass this dispatch claim."""
    def __init__(self, model, tenant, rid, config):
        self.model, self.tenant, self.rid, self.config = model, tenant, rid, config

    async def get_response(self, *args, **kwargs):
        from .workflow import boundary_hook
        cached = attempts.response(self.tenant, self.rid)
        if cached is not None:
            spend.settle(self.tenant, self.config, cached.raw_usage)
            return cached
        boundary_hook(self.rid, 'before_provider_claim')
        spend.claim(self.tenant, self.config)
        attempts.claim(self.tenant, self.rid, self.config['spend']['reservation_id'])
        boundary_hook(self.rid, 'after_provider_claim')
        try:
            result = await self.model.get_response(*args, **kwargs)
            boundary_hook(self.rid, 'after_provider_response')
            attempts.save(self.tenant, self.rid, result)
            spend.settle(self.tenant, self.config, result.raw_usage)
            boundary_hook(self.rid, 'after_response_checkpoint')
            return result
        except ReviewProblem:
            attempts.unknown(self.tenant, self.rid)
            raise
        except Exception:
            attempts.unknown(self.tenant, self.rid)
            raise ReviewProblem('MODEL_OUTCOME_UNKNOWN', 'The provider attempt did not finish durably. It will not be sent again automatically.') from None

    async def stream_response(self, *args, **kwargs):
        raise RuntimeError('Streaming is not supported')
        yield


@DBOS.workflow(name="qa.openai.combined.f3.v1")
async def openai_combined(tenant, rid, payload, config):
    from openai.types.shared import Reasoning
    # Pin the public endpoint and standard tier; custom endpoints have unverified pricing.
    async with AsyncOpenAI(max_retries=0, timeout=120.0, base_url='https://api.openai.com/v1') as client:
        agent = Agent(name='combined_report_review', instructions=task(config),
            model=GuardedModel(make_model(config, client), tenant, rid, config),
            output_type=CombinedOutput,
            model_settings=ModelSettings(store=False, max_tokens=config['model_max_output_tokens'],
                reasoning=Reasoning(effort=config['model_reasoning_effort']),
                truncation='disabled', preserve_raw_usage=True,
                extra_body={'service_tier': 'default'}))
        started = time.monotonic()
        try:
            answer = await DBOSRunner.run(agent, model_input(payload['report_text']), max_turns=1,
                run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False))
        except ReviewProblem:
            raise
        except Exception:
            # SDK parse/refusal exceptions may contain model text; keep them out of
            # DBOS exception logs and public resources. The private response is saved.
            raise ReviewProblem('MODEL_OUTPUT_INVALID', 'The model response could not be accepted. No repair request will be made.') from None
        # SDK can replay a checkpoint without entering GuardedModel; settlement is idempotent.
        last = answer.raw_responses[-1]
        cost = spend.settle(tenant, config, last.raw_usage)
        usage = answer.context_wrapper.usage
        return dict(raw=answer.final_output.model_dump(), metrics=dict(provider='openai',
            model=config['model'], model_calls=1, requests=usage.requests,
            elapsed_ms=round((time.monotonic()-started)*1000), input_tokens=usage.input_tokens if last.raw_usage is not None else None,
            output_tokens=usage.output_tokens if last.raw_usage is not None else None,
            total_tokens=usage.total_tokens if last.raw_usage is not None else None,
            cost_upper_bound_micro_usd=cost))
