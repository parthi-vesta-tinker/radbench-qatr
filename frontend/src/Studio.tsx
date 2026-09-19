import { Check, Minus, AlertCircle } from "lucide-react";
import type { Review } from "./types";
const stages = [
  ["input_validation", "Input validation"],
  ["combined_review", "Combined report review"],
  ["output_validation", "Output validation"],
  ["comment_assembly", "Comment assembly"],
];

// Guidance is advice for the reader, not tracked progress: no state is stored per step.
function guidance(review: Review | null, stale: boolean): string[] {
  if (stale)
    return [
      "Reconnect to confirm the current status.",
      "Do not copy these comments until the status is confirmed.",
    ];
  const state = review?.execution_status;
  if (!review)
    return ["Paste the findings and impression.", "Select Review."];
  if (state === "queued" || state === "running")
    return ["Wait for all checks to finish.", "Results appear here automatically."];
  if (state === "needs_input")
    return [
      "Add the missing findings or impression.",
      "Select Review again.",
    ];
  if (state === "failed")
    return [
      "Read the error above.",
      "Edit the report, then select Review again.",
    ];
  if (review.result?.critical_finding_detected)
    return [
      "Read the critical findings first.",
      "Confirm the critical designation.",
      "Follow the applicable communication pathway.",
      "Copy the comments into the report.",
      "Rate the review.",
    ];
  if (review.result?.outcome === "observations")
    return [
      "Read the comments.",
      "Copy them into the report.",
      "Rate the review.",
    ];
  return ["No comments to copy.", "Rate the review if something was missed."];
}

export function Studio({
  review,
  stale,
}: {
  review: Review | null;
  stale: boolean;
}) {
  return (
    <aside className="studio" aria-label="Review Studio">
      <section className="studio-section">
        <h3>Review steps</h3>
        <ol className="steps">
          {stages.map(([id, label]) => {
            const status =
              review?.steps.find((s) => s.step_id === id)?.status ?? "pending";
            return (
              <li key={id}>
                <span className={"step-icon " + status}>
                  {status === "completed" ? (
                    <Check />
                  ) : status === "failed" || status === "needs_input" ? (
                    <AlertCircle />
                  ) : (
                    <Minus />
                  )}
                </span>
                <span>
                  {label}
                  <small>
                    {status === "running"
                      ? "In progress"
                      : status === "needs_input"
                        ? "Needs input"
                        : status === "failed"
                          ? "Failed"
                          : status === "skipped"
                            ? "Not run"
                            : ""}
                  </small>
                </span>
                <span className="sr-only">{status}</span>
              </li>
            );
          })}
        </ol>
      </section>
      <section className="studio-section">
        <h3>Guidance: Next steps</h3>
        <ol className="guidance">
          {guidance(review, stale).map((step, index) => (
            <li key={step}>
              <span className="guidance-number" aria-hidden="true">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </section>
    </aside>
  );
}
