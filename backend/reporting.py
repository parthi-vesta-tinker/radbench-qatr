"""Read-only, tenant-scoped Studio queries. Never updates reviews or clinical skills."""

import json
from datetime import datetime, timedelta, timezone
from . import store, presentation


def source_filter(source, alias="r"):
    if source == "all":
        return [], []
    return [f"json_extract({alias}.document, '$.provenance.mode')=?"], [source]


def finding_category(group, observation, candidates):
    """Classify a saved comment using its accepted private check identity."""
    if group == "critical_comments":
        return "critical_findings"
    checks = {candidate.get("check_id") for candidate in candidates if isinstance(candidate, dict)}
    if "qa-internal-consistency" in checks:
        return "inconsistencies"
    if checks & {"qa-clinical-question", "qa-recommendations"}:
        return "clinical_observations"
    # Older and demo results can lack a private candidate map. Their public
    # finding type is the only safe classification evidence retained.
    if observation.get("finding_type") == "discrepancy":
        return "inconsistencies"
    return "other_issues"


def feedback_inbox(tenant, version, limit=20, starting_after=None, query="",
                   rating=None, reason=None, source="openai"):
    terms, values = ["f.tenant_id=?"], [tenant]
    extra, params = source_filter(source)
    terms += extra
    values += params
    for field, value in (("rating", rating), ("reason", reason)):
        if value:
            terms.append(f"json_extract(f.document, '$.{field}')=?")
            values.append(value)
    if query:
        terms.append("(" + " OR ".join(
            f"instr(lower(coalesce({column}, '')), lower(?))>0"
            for column in (
                "f.id", "f.review_id",
                "json_extract(f.document, '$.explanation')",
                "json_extract(f.document, '$.suggested_comment')",
            )
        ) + ")")
        values += [query] * 4
    with store.db() as conn:
        conn.execute("BEGIN")  # Cursor and page share one read snapshot.
        if starting_after:
            cursor = conn.execute(
                "SELECT rowid FROM feedback WHERE tenant_id=? AND id=?",
                (tenant, starting_after),
            ).fetchone()
            if cursor is None:
                raise store.InvalidCursor()
            terms.append("f.rowid<?")
            values.append(cursor[0])
        rows = conn.execute(
            "SELECT f.document AS feedback, r.document AS review FROM feedback f "
            "JOIN reviews r ON r.tenant_id=f.tenant_id AND r.id=f.review_id WHERE "
            + " AND ".join(terms) + " ORDER BY f.rowid DESC LIMIT ?",
            [*values, limit + 1],
        ).fetchall()
    items = []
    for row in rows[:limit]:
        feedback, review = json.loads(row["feedback"]), json.loads(row["review"])
        target = feedback.get('target_comment')
        items.append(dict(
            feedback=presentation.feedback(feedback, version),
            report_preview=" ".join(review["input"]["report_text"].split())[:140],
            source=review["provenance"]["mode"],
            target_comment=target,
        ))
    return items, len(rows) > limit


def analytics(tenant, period="7d", source="openai", include_feedback=False):
    checked = datetime.now(timezone.utc)
    windows = {"1h": timedelta(hours=1), "6h": timedelta(hours=6),
               "12h": timedelta(hours=12), "24h": timedelta(hours=24),
               "7d": timedelta(days=7), "30d": timedelta(days=30)}
    start = (checked - windows[period]).isoformat() if period != "all" else None
    extra, params = source_filter(source)
    review_terms, review_values = ["r.tenant_id=?", *extra], [tenant, *params]
    feedback_terms, feedback_values = ["f.tenant_id=?", *extra], [tenant, *params]
    # Periods are rolling UTC windows with an inclusive lower / exclusive upper bound.
    for terms, values, alias in ((review_terms, review_values, "r"), (feedback_terms, feedback_values, "f")):
        terms.append(f"julianday(json_extract({alias}.document, '$.created_at'))<julianday(?)")
        values.append(checked.isoformat())
        if start:
            terms.append(f"julianday(json_extract({alias}.document, '$.created_at'))>=julianday(?)")
            values.append(start)
    with store.db() as conn:
        conn.execute("BEGIN")
        rows = conn.execute(
            "SELECT json_extract(r.document, '$.execution_status') AS status, "
            "count(*) AS total, "
            "sum(coalesce(json_extract(r.document, '$.result.outcome')='observations',0)) AS with_comments, "
            "sum(coalesce(json_extract(r.document, '$.result.outcome')='no_observations',0)) AS no_comments, "
            "sum(coalesce(json_extract(r.document, '$.result.critical_finding_detected')=1,0)) AS critical "
            "FROM reviews r WHERE " + " AND ".join(review_terms) + " GROUP BY status",
            review_values,
        ).fetchall()
        counts = dict.fromkeys(("queued", "running", "completed", "needs_input", "failed"), 0)
        totals = dict(total=0, with_comments=0, no_comments=0, critical=0)
        for row in rows:
            counts[row["status"]] = row["total"]
            totals["total"] += row["total"]
            if row["status"] == "completed":
                for key in ("with_comments", "no_comments", "critical"):
                    totals[key] += row[key]
        observed = conn.execute(
            "SELECT o.review_id, o.id, o.group_name, o.document, x.metadata "
            "FROM reviews r JOIN observations o ON o.tenant_id=r.tenant_id AND o.review_id=r.id "
            "JOIN review_results x ON x.tenant_id=o.tenant_id AND x.review_id=o.review_id "
            "AND x.result_version=o.result_version WHERE " + " AND ".join(review_terms)
            + " AND json_extract(r.document, '$.execution_status')='completed'",
            review_values,
        ).fetchall()
        findings = dict.fromkeys(("inconsistencies", "critical_findings",
                                  "clinical_observations", "other_issues"), 0)
        mappings = {}
        for row in observed:
            if row["review_id"] not in mappings:
                metadata = json.loads(row["metadata"])
                mappings[row["review_id"]] = {
                    item["observation_id"]: item.get("candidates", [])
                    for item in (metadata.get("_candidate_mapping") or [])
                    if isinstance(item, dict) and "observation_id" in item
                }
            category = finding_category(
                row["group_name"], json.loads(row["document"]),
                mappings[row["review_id"]].get(row["id"], []),
            )
            findings[category] += 1
        feedback = None
        if include_feedback:
            joined = " FROM feedback f JOIN reviews r ON r.tenant_id=f.tenant_id AND r.id=f.review_id WHERE " + " AND ".join(feedback_terms)
            summary = conn.execute(
                "SELECT count(*) AS total, count(DISTINCT f.review_id) AS reviews, "
                "coalesce(sum(json_extract(f.document, '$.rating')='up'),0) AS up, "
                "coalesce(sum(json_extract(f.document, '$.rating')='down'),0) AS down" + joined,
                feedback_values,
            ).fetchone()
            reasons = conn.execute(
                "SELECT json_extract(f.document, '$.reason') AS reason, count(*) AS total" + joined
                + " AND json_extract(f.document, '$.rating')='down' GROUP BY reason ORDER BY total DESC, reason",
                feedback_values,
            ).fetchall()
            feedback = dict(summary) | {"reasons": {row["reason"] or "other": row["total"] for row in reasons}}
    return dict(object="qa_analytics", tenant_id=tenant, checked_at=checked.isoformat(),
                period=period, period_start=start, source=source,
                reviews=totals | {"statuses": counts}, findings=findings, feedback=feedback,
                critical_evaluation=dict(
                    status="not_measured", unit="report", scope="report_text_only",
                    precision=None, recall=None, false_positive_rate=None,
                    false_alert_share=None, tp=None, fp=None, fn=None, tn=None,
                    reason="No independent adjudicated reference cohort is connected. Feedback is not ground truth.",
                ))
