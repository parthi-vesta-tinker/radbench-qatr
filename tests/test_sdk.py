"""Runs the real Agents SDK and DBOS adapter with a deterministic Model, no network."""

import json
import re
import uuid
import pytest
from agents.models.interface import Model, ModelResponse
from agents.usage import Usage
from openai.types.responses import ResponseOutputMessage, ResponseOutputText
from backend import reviewer
from test_api import post, finish


class ControlledModel(Model):
    def __init__(self, calls, mode="valid"):
        self.calls = calls
        self.mode = mode

    async def get_response(
        self,
        system_instructions,
        input,
        model_settings,
        tools,
        output_schema,
        handoffs,
        tracing,
        **kwargs,
    ):
        self.calls.append(system_instructions)
        assert model_settings.store is False and not tools
        assert "radiologist_critical_flag" not in json.dumps(input)
        stage = 'critical_finding_review'
        checks = json.loads(re.search(r'checked_skills must contain each of these exactly once: (\[.*?\])', system_instructions).group(1))
        output = {
            "checked_skills": checks,
            "input_problem": None,
            "observations": [],
            "designation": None,
        }
        if stage == "critical_finding_review":
            output["designation"] = dict(status="unknown", anchor=None)
            if self.mode in ("grounded_flag", "ungrounded_flag"):
                output["observations"] = [
                    dict(
                        candidate_id="c1",
                        check_id="qa-critical-match",
                        issue_code="CRIT",
                        finding_type="suggestion",
                        comment="Please review the documented pneumothorax and critical designation.",
                        anchors=[
                            dict(
                                section_id="impression-1",
                                quote="Acute right pneumothorax.",
                            )
                        ],
                        basis="Report describes an acute pneumothorax.",
                        critical_basis=dict(
                            assessment="generic_provisional",
                            assertion_support="explicit_diagnosis",
                            policy_id=None,
                            rule_id=None,
                        ),
                        requirement_ref=None,
                    )
                ]
                output["designation"] = dict(
                    status="documented_flagged",
                    anchor=dict(
                        section_id="other-1",
                        quote="Critical finding flag: Yes"
                        if self.mode == "grounded_flag"
                        else "A fabricated quote.",
                    ),
                )
        text = "not json" if self.mode == "malformed" else json.dumps(output)
        return ModelResponse(
            output=[
                ResponseOutputMessage(
                    id="msg_test",
                    type="message",
                    role="assistant",
                    status="completed",
                    content=[
                        ResponseOutputText(
                            type="output_text", text=text, annotations=[]
                        )
                    ],
                )
            ],
            usage=Usage(requests=1, input_tokens=20, output_tokens=10, total_tokens=30),
            response_id="resp_test",
            raw_usage=dict(input_tokens=20, output_tokens=10, total_tokens=30),
        )

    async def stream_response(self, *args, **kwargs):
        raise AssertionError("Streaming not used")
        yield


@pytest.mark.parametrize(
    "mode", ["valid", "malformed", "grounded_flag", "ungrounded_flag"]
)
def test_sdk_durable_path(client, monkeypatch, mode):
    calls = []
    monkeypatch.setenv("RUN_MODE", "live")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-transmitted")
    monkeypatch.setenv("OPENAI_MODEL", "controlled-sdk-test")
    monkeypatch.setattr(
        reviewer, "make_model", lambda config, client: ControlledModel(calls, mode)
    )
    key = str(uuid.uuid4())
    r = post(client, key=key, sample="critical_documented")
    d = finish(client, r)
    if mode in ("malformed", "ungrounded_flag"):
        assert d["execution_status"] == "failed" and d["result"] is None
    else:
        assert d["execution_status"] == "completed", d
        assert len(calls) == 1
        assert d["result"]["outcome"] == (
            "observations" if mode == "grounded_flag" else "no_observations"
        )
        if mode == "grounded_flag":
            assert (
                d["result"]["missed_flag"] is False and d["result"]["critical_comments"]
            )
        assert (
            sum(s.get("metrics", {}).get("total_tokens", 0) for s in d["steps"]) == 30
        )
        assert (
            post(client, key=key, sample="critical_documented").json()["id"]
            == d["id"]
        )
        assert len(calls) == 1
